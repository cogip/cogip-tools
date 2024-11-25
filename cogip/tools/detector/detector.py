import math
import threading
import time

import socketio
from more_itertools import consecutive_groups

try:
    import ydlidar
except:  # noqa
    ydlidar = None

from cogip import models
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
        server_url: str,
        lidar_port: str | None,
        min_distance: int,
        max_distance: int,
        beacon_radius: int,
        refresh_interval: float,
    ):
        """
        Class constructor.

        Arguments:
            server_url: server URL
            lidar_port: Serial port connected to the Lidar
            min_distance: Minimum distance to detect an obstacle
            max_distance: Maximum distance to detect an obstacle
            beacon_radius: Radius of the opponent beacon support (a cylinder of 70mm diameter to a cube of 100mm width)
            refresh_interval: Interval between each update of the obstacle list (in seconds)
        """
        self._server_url = server_url
        self._lidar_port = lidar_port
        self._properties = Properties(
            min_distance=min_distance,
            max_distance=max_distance,
            beacon_radius=beacon_radius,
            refresh_interval=refresh_interval,
        )
        self._lidar_data: list[int] = list()
        self._lidar_data_lock = threading.Lock()
        self._robot_pose = models.Pose()
        self._robot_pose_lock = threading.Lock()

        self._monitor_obstacles: list[models.Vertex] = []
        self.monitor_obstacles_lock = threading.Lock()

        self._obstacles_updater_loop = ThreadLoop(
            "Obstacles updater loop",
            refresh_interval,
            self.send_obstacles,
            logger=True,
        )

        self._lidar_reader_loop = ThreadLoop(
            "Lidar reader loop",
            refresh_interval,
            self.read_lidar,
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
            self._laser.setlidaropt(ydlidar.LidarPropMaxRange, (max_distance - beacon_radius) / 1000)
            self._laser.setlidaropt(ydlidar.LidarPropMinRange, min_distance / 1000)
            self._laser.setlidaropt(ydlidar.LidarPropInverted, False)

            self._scan = ydlidar.LaserScan()

        self._sio = socketio.Client(logger=False)
        self._sio.register_namespace(SioEvents(self))

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
            self._lidar_reader_loop.start()
            self.start_lidar()

    def stop(self) -> None:
        """
        Stop updating obstacles list.
        """
        self._obstacles_updater_loop.stop()
        if self._laser:
            self._lidar_reader_loop.stop()
            self.stop_lidar()

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

    @property
    def robot_pose(self) -> models.Pose:
        """
        Last position of the robot.
        """
        return self._robot_pose
    
    @property
    def monitor_obstacles(self) -> list[models.Vertex]:
        """
        List of obstacles sent by the Monitor
        """
        with self.monitor_obstacles_lock:
            return self._monitor_obstacles

    @monitor_obstacles.setter
    def monitor_obstacles(self, new_list: list[models.Vertex]) -> None:
        with self.monitor_obstacles_lock:
            self._monitor_obstacles = new_list

    @robot_pose.setter
    def robot_pose(self, new_pose: models.Pose) -> None:
        with self._robot_pose_lock:
            self._robot_pose = new_pose

    def update_refresh_interval(self) -> None:
        self._obstacles_updater_loop.interval = self._properties.refresh_interval
        self._lidar_reader_loop.interval = self._properties.refresh_interval

    def send_obstacles(self):
        if True:
            obstacles = self._monitor_obstacles
        else:
            obstacles = self.process_lidar_data()

        logger.debug(f"Detector obstacles: {obstacles}")

        if self._sio.connected:
            self._sio.emit("obstacles", [o.model_dump(exclude_defaults=True) for o in obstacles], namespace="/detector")

    def update_lidar_data(self, lidar_data: list[int]):
        """
        Receive Lidar data.
        """
        with self._lidar_data_lock:
            self._lidar_data[:] = lidar_data[:]

    def filter_distances(self) -> list[int]:
        """
        Find consecutive obstacles and keep the nearest obstacle at the middle.
        """
        filtered_distances = [self.properties.max_distance - self.properties.beacon_radius] * 360

        # Find an angle without obstacle
        angles_without_obstacles = [
            i
            for i, d in enumerate(self._lidar_data)
            if d >= self.properties.max_distance - self.properties.beacon_radius
        ]

        # Exit if no obstacle detected
        if len(angles_without_obstacles) == 0:
            return filtered_distances

        start = angles_without_obstacles[0]

        # Iterate over all angles, starting by the first angle without obstacle
        first = start
        while first < start + 360:
            dist_min = self._lidar_data[first % 360]

            # Find the next angle with obstacle
            if dist_min >= self.properties.max_distance - self.properties.beacon_radius:
                first += 1
                continue

            # An angle (first) with obstacle is found, iterate until the next angle without obstacle
            for last in range(first + 1, start + 360 + 1):
                dist_current = self._lidar_data[last % 360]

                # Keep the nearest distance of consecutive obstacles
                if dist_current < (self.properties.max_distance - self.properties.beacon_radius) or self._lidar_data[
                    (last + 1) % 360
                ] < (self.properties.max_distance - self.properties.beacon_radius):
                    dist_min = dist_current if dist_current < dist_min else dist_min
                    continue

                # Do not exit the loop only if NB_ANGLES_WITHOUT_OBSTACLE_TO_IGNORE consecutive
                # angles have no obstacle.
                continue_loop = False
                for next in range(last + 1, last + self.NB_ANGLES_WITHOUT_OBSTACLE_TO_IGNORE):
                    if self._lidar_data[next % 360] < self.properties.max_distance - self.properties.beacon_radius:
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

    def generate_obstacles(self, robot_pose: models.Pose, distances: list[int]) -> list[models.Vertex]:
        """
        Update obstacles list from lidar data.
        """
        obstacles: list[models.Vertex] = []

        for angle, distance in enumerate(distances):
            if (
                distance < self.properties.min_distance
                or distance >= self.properties.max_distance - self.properties.beacon_radius
            ):
                continue

            angle = (360 - angle) % 360

            # Compute obstacle position
            obstacle_angle = math.radians((int(robot_pose.O) + angle) % 360)
            x = robot_pose.x + distance * math.cos(obstacle_angle)
            y = robot_pose.y + distance * math.sin(obstacle_angle)

            obstacles.append(models.Vertex(x=x, y=y))

        return obstacles

    def process_lidar_data(self):
        """
        Function executed in a thread loop to update and send dynamic obstacles.
        """
        with self._lidar_data_lock:
            filtered_distances = self.filter_distances()
        with self._robot_pose_lock:
            robot_pose = self.robot_pose.model_copy()

        obstacles = self.generate_obstacles(robot_pose, filtered_distances)
        logger.debug(f"Generated obstacles: {obstacles}")

        return obstacles


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
                distance = self.properties.max_distance - self.properties.beacon_radius
                if size := len(distances):
                    distance = round(sum(distances) * 1000 / size)
                else:
                    empty_angles.append(angle)

                result.append(distance + self.properties.beacon_radius)

            # If a degree has no valid point and is isolated (no other empty angle before and after)
            # it is probably a bad value, so set it to the mean of surrounding degrees.
            for group in consecutive_groups(empty_angles):
                g = list(group)
                if len(g) == 1:
                    isolated = g[0]
                    before = result[(isolated - 1) % 360]
                    after = result[(isolated + 1) % 360]
                    result[isolated] = round((before + after) / 2)

            self.update_lidar_data(result)
        else:
            print("Failed to get Lidar Data")

    def stop_lidar(self):
        """
        Stop the Lidar.
        """
        if self._laser:
            self._laser.turnOff()
            self._laser.disconnecting()
