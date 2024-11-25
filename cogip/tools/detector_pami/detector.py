import math
import threading
import time

import socketio
from VL53L1X import VL53L1X, VL53L1xDistanceMode

from cogip import models
from cogip.utils import ThreadLoop
from . import logger
from .properties import Properties
from .sio_events import SioEvents


class Detector:
    """
    Main detector class.

    Read data from the ToF in monitoring mode
    or fake data provided by `Monitor` in emulation Mode.

    Build obstacles and send the list to the server.
    """

    def __init__(
        self,
        server_url: str,
        tof_bus: int | None,
        tof_address: int | None,
        min_distance: int,
        max_distance: int,
        refresh_interval: float,
    ):
        """
        Class constructor.

        Arguments:
            server_url: server URL
            tof_bus: ToF i2c bus
            tof_address: ToF i2c address
            min_distance: Minimum distance to detect an obstacle
            max_distance: Maximum distance to detect an obstacle
            refresh_interval: Interval between each update of the obstacle list (in seconds)
        """
        self.server_url = server_url
        self.tof_bus = tof_bus
        self.tof_address = tof_address
        self.properties = Properties(
            min_distance=min_distance,
            max_distance=max_distance,
            refresh_interval=refresh_interval,
        )
        self.sensor: VL53L1X | None = None
        self.sensors_data: list[int] = list()
        self.sensors_data_lock = threading.Lock()
        self._robot_pose = models.Pose()
        self.robot_pose_lock = threading.Lock()

        self._monitor_obstacles: list[models.Vertex] = []
        self.monitor_obstacles_lock = threading.Lock()

        self.obstacles_updater_loop = ThreadLoop(
            "Obstacles updater loop",
            refresh_interval,
            self.send_obstacles,
            logger=True,
        )

        self.sensor_reader_loop = ThreadLoop(
            "Sensor reader loop",
            refresh_interval,
            self.read_sensors,
            logger=True,
        )

        self.init_sensor()

        self.sio = socketio.Client(logger=False)
        self.sio.register_namespace(SioEvents(self))

    def connect(self):
        """
        Connect to SocketIO server.
        """
        threading.Thread(target=self.try_connect).start()

    def init_sensor(self):
        if self.tof_bus and self.tof_address:
            self.sensor = VL53L1X(i2c_bus=self.tof_bus, i2c_address=self.tof_address)
            self.sensor.open(reset=True)

    def start(self):
        """
        Start updating obstacles list.
        """
        self.obstacles_updater_loop.start()
        if self.sensor:
            self.sensor_reader_loop.start()
            self.start_sensors()

    def stop(self) -> None:
        """
        Stop updating obstacles list.
        """
        self.obstacles_updater_loop.stop()
        if self.sensor:
            self.sensor_reader_loop.stop()
            self.stop_sensors()

    def try_connect(self):
        """
        Poll to wait for the first cogip-server connection.
        Disconnections/reconnections are handle directly by the client.
        """
        while True:
            try:
                self.sio.connect(
                    self.server_url,
                    namespaces=["/detector"],
                )
                self.sio.wait()
            except socketio.exceptions.ConnectionError:
                time.sleep(2)
                continue
            break

    @property
    def robot_pose(self) -> models.Pose:
        """
        Last position of the robot.
        """
        return self._robot_pose

    @robot_pose.setter
    def robot_pose(self, new_pose: models.Pose) -> None:
        with self.robot_pose_lock:
            self._robot_pose = new_pose

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

    def update_refresh_interval(self) -> None:
        self.obstacles_updater_loop.interval = self.properties.refresh_interval
        self.sensor_reader_loop.interval = self.properties.refresh_interval

    def update_sensors_data(self, sensors_data: list[int]):
        """
        Receive sensors data.
        """
        with self.sensors_data_lock:
            self.sensors_data[:] = sensors_data[:]

    def filter_distances(self) -> list[int]:
        """
        Nothing to do with ToF sensors of PAMI.
        Just keep the function for API compatibility.
        """
        return self.sensors_data

    def generate_obstacles(self, robot_pose: models.Pose, distances: list[int]) -> list[models.Vertex]:
        """
        Update obstacles list from sensors data.
        """
        if len(distances) == 0:
            return []

        distance = distances[0]
        if distance < self.properties.min_distance or distance >= self.properties.max_distance:
            return []

        # Compute obstacle position
        angle = math.radians(robot_pose.O)
        x = robot_pose.x + distance * math.cos(angle)
        y = robot_pose.y + distance * math.sin(angle)

        return [models.Vertex(x=x, y=y)]
    
    def send_obstacles(self):
        obstacles_lidar = self.process_sensor_data()
        obstacles_monitor = self.read_monitor_obstacles()

        if self.sio.connected:
            self.sio.emit("obstacles", [o.model_dump(exclude_defaults=True) for o in obstacles_monitor], namespace="/detector")

    def read_monitor_obstacles(self) -> list[models.Vertex]:
        """
        Read obstacles sent by the monitor
        """
        logger.info(f"Monitor obstacles: {self._monitor_obstacles}")
        return self._monitor_obstacles


    def process_sensor_data(self) -> list[models.Vertex]:
        """
        Function executed in a thread loop to update and send dynamic obstacles.
        """
        with self.sensors_data_lock:
            filtered_distances = self.filter_distances()
        with self.robot_pose_lock:
            robot_pose = self.robot_pose.model_copy()

        obstacles = self.generate_obstacles(robot_pose, filtered_distances)
        logger.debug(f"Generated obstacles: {obstacles}")

        return obstacles

    def start_sensors(self):
        """
        Start sensors.
        """
        if self.sensor:
            self.sensor.start_ranging(mode=VL53L1xDistanceMode.LONG)
            self.sensor.set_timing(150, 200)

    def read_sensors(self):
        """
        Function executed in a thread loop to read sensors data.
        """
        if not self.sensor:
            return

        self.update_sensors_data([self.sensor.get_distance()])

    def stop_sensors(self):
        """
        Stop sensors.
        """
        if self.sensor:
            self.sensor.stop_ranging()
            self.sensor.close()
