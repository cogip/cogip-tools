import math
import threading
import time

import socketio
from more_itertools import consecutive_groups
from numpy.typing import NDArray

try:
    import ydlidar
except:  # noqa
    ydlidar = None

from cogip import models
from cogip.cpp.libraries.models import CoordsList as SharedCoordsList
from cogip.cpp.libraries.models import Pose as SharedPose
from cogip.cpp.libraries.models import PoseBuffer as SharedPoseBuffer
from cogip.cpp.libraries.shared_memory import LockName, SharedMemory, WritePriorityLock
from cogip.utils import ThreadLoop
from . import logger
from .properties import Properties
from .sio_events import SioEvents


class Detector:
    """
    Main detector class.

    Read Lidar data from the Lidar in monitoring mode
    or fake data provided by `Monitor` in emulation Mode.

    Build obstacles and send the list to the server.
    """

    NB_ANGLES_WITHOUT_OBSTACLE_TO_IGNORE: int = 3

    def __init__(
        self,
        robot_id: int,
        server_url: str,
        lidar_port: str | None,
        min_distance: int,
        max_distance: int,
        beacon_radius: int,
        refresh_interval: float,
        sensor_delay: int,
    ):
        """
        Class constructor.

        Arguments:
            robot_id: Robot ID
            server_url: server URL
            lidar_port: Serial port connected to the Lidar
            min_distance: Minimum distance to detect an obstacle
            max_distance: Maximum distance to detect an obstacle
            beacon_radius: Radius of the opponent beacon support (a cylinder of 70mm diameter to a cube of 100mm width)
            refresh_interval: Interval between each update of the obstacle list (in seconds)
            sensor_delay: Delay to compensate the delay between sensor data fetch and obstacle positions computation,"
                          unit is the index of pose current to get in the past
        """
        self.robot_id = robot_id
        self._server_url = server_url
        self._lidar_port = lidar_port
        self._properties = Properties(
            min_distance=min_distance,
            max_distance=max_distance,
            beacon_radius=beacon_radius,
            refresh_interval=refresh_interval,
            sensor_delay=sensor_delay,
        )

        self.shared_memory: SharedMemory | None = None
        self.shared_pose_current_lock: WritePriorityLock | None = None
        self.shared_pose_current: SharedPose | None = None
        self.shared_pose_current_buffer: SharedPoseBuffer | None = None
        self.shared_lidar_data: NDArray | None = None
        self.shared_lidar_data_lock: WritePriorityLock | None = None
        self.shared_detector_obstacles: SharedCoordsList | None = None
        self.shared_detector_obstacles_lock: WritePriorityLock | None = None

        self._lidar_data: list[int] = list()
        self._lidar_data_lock = threading.Lock()

        self._obstacles_updater_loop = ThreadLoop(
            "Obstacles updater loop",
            refresh_interval,
            self.process_lidar_data,
            logger=True,
        )

        self._lidar_reader_loop = ThreadLoop(
            "Lidar reader loop",
            refresh_interval,
            self.read_lidar,
            logger=True,
        )

        self._fake_lidar_reader_loop = ThreadLoop(
            "Fake Lidar reader loop",
            refresh_interval,
            self.read_fake_lidar,
            logger=True,
        )

        self._laser: ydlidar.CYdLidar | None = None
        self._scan: ydlidar.LaserScan | None = None
        if ydlidar and not self._lidar_port:
            for _, value in ydlidar.lidarPortList().items():
                self._lidar_port = value
        if self._lidar_port:
            self._laser = ydlidar.CYdLidar()
            self._laser.setlidaropt(ydlidar.LidarPropSerialPort, str(self._lidar_port))
            self._laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 230400)
            self._laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
            self._laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
            self._laser.setlidaropt(ydlidar.LidarPropSingleChannel, False)
            self._laser.setlidaropt(ydlidar.LidarPropSampleRate, 5)
            self._laser.setlidaropt(ydlidar.LidarPropIntenstiy, True)
            self._laser.setlidaropt(ydlidar.LidarPropScanFrequency, 5.0)
            self._laser.setlidaropt(ydlidar.LidarPropMaxRange, max_distance / 1000)
            self._laser.setlidaropt(ydlidar.LidarPropMinRange, min_distance / 1000)
            self._laser.setlidaropt(ydlidar.LidarPropInverted, False)

            self._scan = ydlidar.LaserScan()

        self._sio = socketio.Client(logger=False)
        self._sio.register_namespace(SioEvents(self))

    def create_shared_memory(self):
        self.shared_memory = SharedMemory(f"cogip_{self.robot_id}")
        self.shared_pose_current_lock = self.shared_memory.get_lock(LockName.PoseCurrent)
        self.shared_pose_current = self.shared_memory.get_pose_current()
        self.shared_pose_current_buffer = self.shared_memory.get_pose_current_buffer()
        self.shared_lidar_data = self.shared_memory.get_lidar_data()
        self.shared_lidar_data_lock = self.shared_memory.get_lock(LockName.LidarData)
        self.shared_detector_obstacles = self.shared_memory.get_detector_obstacles()
        self.shared_detector_obstacles_lock = self.shared_memory.get_lock(LockName.DetectorObstacles)

    def delete_shared_memory(self):
        self.shared_detector_obstacles_lock = None
        self.shared_detector_obstacles = None
        self.shared_lidar_data_lock = None
        self.shared_lidar_data = None
        self.shared_pose_current_buffer = None
        self.shared_pose_current = None
        self.shared_pose_current_lock = None
        self.shared_memory = None

    def connect(self):
        """
        Connect to SocketIO server.
        """
        threading.Thread(target=self.try_connect).start()

    def start(self) -> None:
        """
        Start updating obstacles list.
        """
        self._obstacles_updater_loop.start()
        if self._laser:
            for i in range(360):
                self._lidar_data[i][0] = i
                self._lidar_data[i][2] = 255
            self._lidar_data[360][0] = -1
            self._lidar_data[360][1] = -1
            self._lidar_data[360][2] = -1

            self._lidar_reader_loop.start()
            self.start_lidar()
        else:
            self._fake_lidar_reader_loop.start()

    def stop(self) -> None:
        """
        Stop updating obstacles list.
        """
        self._obstacles_updater_loop.stop()
        if self._laser:
            self._lidar_reader_loop.stop()
            self.stop_lidar()
        else:
            self._fake_lidar_reader_loop.stop()

    def try_connect(self):
        """
        Poll to wait for the first cogip-server connection.
        Disconnections/reconnections are handle directly by the client.
        """
        while True:
            try:
                self._sio.connect(
                    self._server_url,
                    namespaces=["/detector"],
                )
                self._sio.wait()
            except socketio.exceptions.ConnectionError:
                time.sleep(2)
                continue
            break

    @property
    def properties(self) -> Properties:
        return self._properties

    def update_refresh_interval(self) -> None:
        self._obstacles_updater_loop.interval = self._properties.refresh_interval
        self._lidar_reader_loop.interval = self._properties.refresh_interval

    def filter_distances(self) -> list[int]:
        """
        Find consecutive obstacles and keep the nearest obstacle at the middle.
        """
        filtered_distances = [self.properties.max_distance] * 360
        self._lidar_data = [
            min(distance + self.properties.beacon_radius, self.properties.max_distance) for distance in self._lidar_data
        ]
        # Find an angle without obstacle
        angles_without_obstacles = [i for i, d in enumerate(self._lidar_data) if d >= self.properties.max_distance]

        # Exit if no obstacle detected
        if len(angles_without_obstacles) == 0:
            return filtered_distances

        start = angles_without_obstacles[0]

        # Iterate over all angles, starting by the first angle without obstacle
        first = start
        while first < start + 360:
            dist_min = self._lidar_data[first % 360]

            # Find the next angle with obstacle
            if dist_min >= self.properties.max_distance:
                first += 1
                continue

            # An angle (first) with obstacle is found, iterate until the next angle without obstacle
            for last in range(first + 1, start + 360 + 1):
                dist_current = self._lidar_data[last % 360]

                # Keep the nearest distance of consecutive obstacles
                if (
                    dist_current < self.properties.max_distance
                    or self._lidar_data[(last + 1) % 360] < self.properties.max_distance
                ):
                    dist_min = dist_current if dist_current < dist_min else dist_min
                    continue

                # Do not exit the loop only if NB_ANGLES_WITHOUT_OBSTACLE_TO_IGNORE consecutive
                # angles have no obstacle.
                continue_loop = False
                for next in range(last + 1, last + self.NB_ANGLES_WITHOUT_OBSTACLE_TO_IGNORE):
                    if self._lidar_data[next % 360] < self.properties.max_distance:
                        continue_loop = True
                        break

                if continue_loop:
                    continue

                # Only keep one angle at the middle of the consecutive angles with obstacles
                # Set its distance to the minimum distance of the range
                last = last - 1
                middle = first + int((last - first) / 2 + 0.5)
                filtered_distances[middle % 360] = dist_min
                first = last + 1
                break
            first += 1

        return filtered_distances

    def generate_obstacles(self, distances: list[int]) -> list[models.Vertex]:
        """
        Update obstacles list from lidar data.
        """
        obstacles: list[models.Vertex] = []

        # Copy the pose before computation to reduce critical section length
        self.shared_pose_current_lock.start_reading()
        try:
            pose_current = self.shared_pose_current_buffer.get(self._properties.sensor_delay)
        except Exception:
            pose_current = self.shared_pose_current
        robot_x = pose_current.x
        robot_y = pose_current.y
        robot_angle = pose_current.angle
        self.shared_pose_current_lock.finish_reading()

        for angle, distance in enumerate(distances):
            if distance < self.properties.min_distance or distance >= self.properties.max_distance:
                continue

            angle = (360 - angle) % 360

            # Compute obstacle position
            obstacle_angle = math.radians((int(robot_angle) + angle) % 360)
            x = robot_x + distance * math.cos(obstacle_angle)
            y = robot_y + distance * math.sin(obstacle_angle)

            obstacles.append(models.Vertex(x=x, y=y))

        return obstacles

    def process_lidar_data(self):
        """
        Function executed in a thread loop to update and send dynamic obstacles.
        """
        with self._lidar_data_lock:
            filtered_distances = self.filter_distances()

        obstacles = self.generate_obstacles(filtered_distances)
        self.shared_detector_obstacles_lock.start_writing()
        self.shared_detector_obstacles.clear()
        for obstacle in obstacles:
            self.shared_detector_obstacles.append(obstacle.x, obstacle.y)
        self.shared_detector_obstacles_lock.finish_writing()
        logger.debug(f"Generated obstacles: {obstacles}")

    def start_lidar(self):
        """
        Start the Lidar.
        """
        if self._laser:
            self._laser.initialize()
            self._laser.turnOn()

    def read_lidar(self):
        """
        Function executed in a thread loop to read Lidar data.
        """
        if not ydlidar.os_isOk():
            return

        ret = self._laser.doProcessSimple(self._scan)
        if ret:
            tmp_distances = [[] for _ in range(360)]
            result = []

            # Build a list of points for each integer degree
            for point in self._scan.points:
                angle_sym = math.floor(math.degrees(point.angle))
                angle = angle_sym if angle_sym >= 0 else angle_sym + 360
                if 0 <= angle < 360 and point.range > 0.0:
                    tmp_distances[angle].append(point.range)

            # Compute mean of points list for each degree.
            empty_angles = []
            for angle, distances in enumerate(tmp_distances):
                distance = self.properties.max_distance
                if size := len(distances):
                    distance = round(sum(distances) * 1000 / size)
                else:
                    empty_angles.append(angle)

                result.append(distance)

            # If a degree has no valid point and is isolated (no other empty angle before and after)
            # it is probably a bad value, so set it to the mean of surrounding degrees.
            for group in consecutive_groups(empty_angles):
                g = list(group)
                if len(g) == 1:
                    isolated = g[0]
                    before = result[(isolated - 1) % 360]
                    after = result[(isolated + 1) % 360]
                    result[isolated] = round((before + after) / 2)

            with self._lidar_data_lock:
                for i, distance in enumerate(result):
                    self._lidar_data[i][1] = distance
        else:
            print("Failed to get Lidar Data")

    def read_fake_lidar(self):
        with self._lidar_data_lock:
            self._lidar_data[:] = self.shared_lidar_data[:360, 1].tolist()

    def stop_lidar(self):
        """
        Stop the Lidar.
        """
        if self._laser:
            self._laser.turnOff()
            self._laser.disconnecting()
