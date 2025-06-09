import os
import threading
import time

import numpy as np
import socketio
import socketio.exceptions
from matplotlib import pyplot as plt
from numpy.typing import NDArray
from sklearn.cluster import DBSCAN

from cogip.cpp.drivers.lidar_ld19 import LDLidarDriver
from cogip.cpp.drivers.ydlidar_g2 import YDLidar
from cogip.cpp.libraries.models import CircleList as SharedCircleList
from cogip.cpp.libraries.models import PoseBuffer as SharedPoseBuffer
from cogip.cpp.libraries.shared_memory import LockName, SharedMemory, WritePriorityLock
from cogip.cpp.libraries.utils import LidarDataConverter
from cogip.utils import ThreadLoop
from . import logger
from .gui import DetectorGUI
from .properties import Properties
from .sio_events import SioEvents
from .web import start_web


class Detector:
    """
    Main detector class.

    Read Lidar data from the Lidar in monitoring mode
    or fake data provided by `Monitor` in emulation Mode.

    Build obstacles and send the list to the server.
    """

    TABLE_LIMITS_MARGIN: int = 50
    YDLIDAR_READY_TIMEOUT_MS: int = 10000

    def __init__(
        self,
        robot_id: int,
        server_url: str,
        lidar_port: str | None,
        min_distance: int,
        max_distance: int,
        min_intensity: int,
        refresh_interval: float,
        sensor_delay: int,
        cluster_min_samples: int,
        cluster_eps: float,
        gui: bool,
        web: bool,
    ):
        """
        Class constructor.

        Arguments:
            robot_id: Robot ID
            server_url: server URL
            lidar_port: Serial port connected to the Lidar
            min_distance: Minimum distance to detect an obstacle
            max_distance: Maximum distance to detect an obstacle
            min_intensity: Minimum intensity to detect an obstacle
            refresh_interval: Interval between each update of the obstacle list (in seconds)
            sensor_delay: Delay to compensate the delay between sensor data fetch and obstacle positions computation,"
                          unit is the index of pose current to get in the past
            cluster_min_samples: Minimum number of samples to form a cluster
            cluster_eps: Maximum distance between two samples to form a cluster (mm)
            gui: Enable GUI
            web: Enable data display on a web server
        """
        self.robot_id = robot_id
        self.server_url = server_url
        self.lidar_port = lidar_port
        self.gui = gui
        self.web = web
        self.properties = Properties(
            min_distance=min_distance,
            max_distance=max_distance,
            min_intensity=min_intensity,
            refresh_interval=refresh_interval,
            sensor_delay=sensor_delay,
            cluster_min_samples=cluster_min_samples,
            cluster_eps=cluster_eps,
        )

        if robot_id == 1:
            self.LIDAR_OFFSET_X = 0.0
        else:
            self.LIDAR_OFFSET_X = 75.5
        self.LIDAR_OFFSET_Y = 0.0

        self.shared_memory: SharedMemory | None = None
        self.shared_pose_current_lock: WritePriorityLock | None = None
        self.shared_pose_current_buffer: SharedPoseBuffer | None = None
        self.shared_lidar_data: NDArray | None = None
        self.shared_lidar_coords: NDArray | None = None
        self.shared_lidar_data_lock: WritePriorityLock | None = None
        self.shared_lidar_coords_lock: WritePriorityLock | None = None
        self.shared_detector_obstacles: SharedCircleList | None = None
        self.shared_detector_obstacles_lock: WritePriorityLock | None = None

        self.lidar_data_converter: LidarDataConverter | None = None

        self.lidar: LDLidarDriver | YDLidar | None = None
        self.clusters: list[NDArray] = []

        self.obstacles_updater_loop = ThreadLoop(
            "Obstacles updater loop",
            refresh_interval,
            self.process_lidar_coords,
            logger=True,
        )

        if gui:
            self.gui_handler = DetectorGUI(self)

        if web:
            self.web_thread = threading.Thread(
                target=start_web,
                args=(self, 8110 + robot_id),
                name="Web thread",
            )

        self.sio = socketio.Client(logger=False)
        self.sio.register_namespace(SioEvents(self))

    def create_shared_memory(self):
        self.shared_memory = SharedMemory(f"cogip_{self.robot_id}")
        self.shared_pose_current_lock = self.shared_memory.get_lock(LockName.PoseCurrent)
        self.shared_pose_current_buffer = self.shared_memory.get_pose_current_buffer()
        self.shared_lidar_data = self.shared_memory.get_lidar_data()
        self.shared_lidar_coords = self.shared_memory.get_lidar_coords()
        self.shared_lidar_data_lock = self.shared_memory.get_lock(LockName.LidarData)
        self.shared_lidar_coords_lock = self.shared_memory.get_lock(LockName.LidarCoords)
        self.shared_detector_obstacles = self.shared_memory.get_detector_obstacles()
        self.shared_detector_obstacles_lock = self.shared_memory.get_lock(LockName.DetectorObstacles)

        self.shared_lidar_data_lock.reset()
        self.shared_lidar_coords_lock.reset()
        # self.shared_lidar_coords_lock.register_consumer()

        # Lidar data is initialized to -1 to indicate that no data is available
        self.shared_lidar_data[0][0] = -1
        self.shared_lidar_data[0][1] = -1
        self.shared_lidar_data[0][2] = -1
        self.shared_lidar_coords[0][0] = -1
        self.shared_lidar_coords[0][1] = -1

        self.lidar_data_converter = LidarDataConverter(f"cogip_{self.robot_id}")
        self.lidar_data_converter.set_pose_current_index(self.properties.sensor_delay)
        self.lidar_data_converter.set_lidar_offset_x(self.LIDAR_OFFSET_X)
        self.lidar_data_converter.set_lidar_offset_y(self.LIDAR_OFFSET_Y)
        self.lidar_data_converter.set_table_limits_margin(self.TABLE_LIMITS_MARGIN)

    def delete_shared_memory(self):
        self.shared_detector_obstacles_lock = None
        self.shared_detector_obstacles = None
        self.shared_lidar_data_lock = None
        self.shared_lidar_coords_lock = None
        self.shared_lidar_coords = None
        self.shared_lidar_data = None
        self.shared_pose_current_buffer = None
        self.shared_pose_current_lock = None
        self.shared_memory = None

        self.lidar_data_converter = None

    def connect(self):
        """
        Connect to SocketIO server.
        """
        threading.Thread(target=self.try_connect).start()

        if self.web:
            self.web_thread.start()

        if self.gui:
            self.gui_handler.start_animation()
            try:
                plt.show()
            except KeyboardInterrupt:
                pass

    def start(self) -> None:
        """
        Start updating obstacles list.
        """
        self.create_shared_memory()
        self.lidar_data_converter.start()
        self.start_lidar()
        self.obstacles_updater_loop.start()

    def stop(self) -> None:
        """
        Stop updating obstacles list.
        """
        self.obstacles_updater_loop.stop()
        self.stop_lidar()
        self.lidar_data_converter.stop()
        self.delete_shared_memory()

    def try_connect(self):
        """
        Poll to wait for the first cogip-server connection.
        Disconnections/re-connections are handle directly by the client.
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

    def cluster_obstacles(self, lidar_coords: NDArray) -> list[NDArray]:
        """
        Groups points into obstacle clusters using DBSCAN

        Returns:
            List of clusters, each cluster being a set of points belonging to the same obstacle
        """
        if len(lidar_coords) == 0:
            return []

        db = DBSCAN(
            eps=self.properties.cluster_eps,
            min_samples=self.properties.cluster_min_samples,
        ).fit(lidar_coords)
        labels = db.labels_

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

        clusters = []
        for i in range(n_clusters):
            cluster_points = lidar_coords[labels == i]
            clusters.append(cluster_points)

        return clusters

    def estimate_obstacle_properties(self, clusters: list[NDArray]) -> list[tuple[float, float, float]]:
        """
        Estimates position and size of obstacles from clusters

        Args:
            clusters: List of clusters, each cluster being a set of points

        Returns:
            List of tuples (center_x, center_y, radius) for each obstacle
        """
        obstacle_properties = []

        for cluster in clusters:
            center_x = np.mean(cluster[:, 0])
            center_y = np.mean(cluster[:, 1])

            # Calculate the maximum distance from center in x and y directions
            # This will be used as the radius of the circle
            radius_x = np.max(np.abs(cluster[:, 0] - center_x))
            radius_y = np.max(np.abs(cluster[:, 1] - center_y))
            radius = max(radius_x, radius_y, 20)  # Minimum radius of 20

            obstacle_properties.append((center_x, center_y, radius))

        return obstacle_properties

    def process_lidar_coords(self):
        """
        Function executed in a thread loop to update and send dynamic obstacles.
        """
        # self.shared_lidar_coords_lock.wait_update()
        self.shared_lidar_coords_lock.start_reading()
        lidar_coords = self.shared_lidar_coords[: np.argmax(self.shared_lidar_coords[:, 0] == -1)].copy()
        self.shared_lidar_coords_lock.finish_reading()

        self.clusters = self.cluster_obstacles(lidar_coords)
        obstacles = self.estimate_obstacle_properties(self.clusters)
        self.shared_detector_obstacles_lock.start_writing()
        self.shared_detector_obstacles.clear()
        for x, y, radius in obstacles:
            self.shared_detector_obstacles.append(x=x, y=y, radius=radius)
        self.shared_detector_obstacles_lock.finish_writing()
        self.shared_detector_obstacles_lock.post_update()

        logger.debug(f"Generated obstacles: {obstacles}")

    def start_lidar(self):
        """
        Start the Lidar.
        """
        if self.lidar_port:
            if self.robot_id == 1:
                self.lidar = YDLidar(self.shared_lidar_data)
                self.lidar.set_scan_frequency(10)
                # No excluded angle range
                self.lidar.set_invalid_angle_range(360, 0)
            else:
                self.lidar = LDLidarDriver(self.shared_lidar_data)
                # Skip rear-facing Lidar data because Lidar is mounted in PAMI
                self.lidar.set_invalid_angle_range(30, 330)
            self.lidar.set_data_write_lock(self.shared_lidar_data_lock)
            self.lidar.set_min_distance(self.properties.min_distance)
            self.lidar.set_max_distance(self.properties.max_distance)
            self.lidar.set_min_intensity(self.properties.min_intensity)

            res = self.lidar.connect(str(self.lidar_port))
            if not res:
                logger.error("Error: Lidar connection failed.")
                os._exit(1)
            logger.info("Lidar connected.")

            if self.robot_id > 1:
                res = self.lidar.wait_lidar_comm(self.YDLIDAR_READY_TIMEOUT_MS)
                if not res:
                    logger.error("Error: Lidar not ready.")
                    os._exit(1)
                logger.info("Lidar is ready.")

            res = self.lidar.start()
            if not res:
                logger.error("Error: Lidar not started.")
                os._exit(1)
            logger.info("Lidar started.")

    def stop_lidar(self):
        """
        Stop the Lidar.
        """
        if self.lidar:
            self.lidar.stop()
            self.lidar.disconnect()
            self.lidar = None
