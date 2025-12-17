from __future__ import annotations
from typing import Any

from numpy.typing import NDArray
from PySide6.QtCore import QObject, QTimer
from shiboken6 import Shiboken

from cogip.cpp.libraries.models import CircleList as SharedCircleList
from cogip.cpp.libraries.models import PoseBuffer as SharedPoseBuffer
from cogip.cpp.libraries.obstacles import ObstacleCircleList as SharedObstacleCircleList
from cogip.cpp.libraries.obstacles import ObstacleRectangleList as SharedObstacleRectangleList
from cogip.cpp.libraries.shared_memory import LockName, SharedMemory, WritePriorityLock
from cogip.utils.singleton import Singleton
from . import logger


class SharedMemoryManager(metaclass=Singleton):
    """
    Shared memory management.
    """

    def __init__(self):
        """
        Class constructor.
        """
        self.robot_id: int | None = None
        self.shared_memory: SharedMemory | None = None
        self.shared_pose_current_buffer: SharedPoseBuffer | None = None
        self.shared_lidar_data: NDArray | None = None
        self.shared_lidar_data_lock: WritePriorityLock | None = None
        self.shared_circle_obstacles: SharedObstacleCircleList | None = None
        self.shared_rectangle_obstacles: SharedObstacleRectangleList | None = None
        self.shared_obstacles_lock: WritePriorityLock | None = None
        self.shared_monitor_obstacles: SharedCircleList | None = None
        self.shared_monitor_obstacles_lock: WritePriorityLock | None = None
        self.update_obstacles_timer: QTimer | None = None
        self.view_item: QObject | None = None
        self.scene_root: QObject | None = None

    def set_scene(self, scene_root: QObject | None, view_item: QObject | None) -> None:
        self.scene_root = scene_root
        self.view_item = view_item
        if view_item is None and scene_root is None:
            return
        # Ensure QML side starts with empty obstacles so stale data is cleared
        self.apply_obstacle_data([], [])

    def connect(self, robot_id: int, virtual_planner: bool = False, virtual_detector: bool = False) -> None:
        logger.info(f"Connecting to shared memory for robot {robot_id}")
        self.robot_id = robot_id
        if virtual_planner or virtual_detector:
            self.shared_memory = SharedMemory(f"cogip_{self.robot_id}")
        if virtual_planner:
            self.shared_pose_current_buffer = self.shared_memory.get_pose_current_buffer()
            self.shared_circle_obstacles = self.shared_memory.get_circle_obstacles()
            self.shared_rectangle_obstacles = self.shared_memory.get_rectangle_obstacles()
            self.shared_obstacles_lock = self.shared_memory.get_lock(LockName.Obstacles)
            self.shared_obstacles_lock.register_consumer()
            if self.update_obstacles_timer is None:
                self.update_obstacles_timer = QTimer()
                self.update_obstacles_timer.setInterval(100)
                self.update_obstacles_timer.timeout.connect(self.update_obstacles)
            else:
                self.update_obstacles_timer.stop()
                self.update_obstacles_timer.setInterval(100)
            self.update_obstacles_timer.start()
            self.update_obstacles()
        else:
            if self.update_obstacles_timer is not None:
                self.update_obstacles_timer.stop()
            self.apply_obstacle_data([], [])

        if virtual_detector:
            self.shared_lidar_data = self.shared_memory.get_lidar_data()
            self.shared_lidar_data_lock = self.shared_memory.get_lock(LockName.LidarData)
            self.shared_monitor_obstacles = self.shared_memory.get_monitor_obstacles()
            self.shared_monitor_obstacles_lock = self.shared_memory.get_lock(LockName.MonitorObstacles)

    def disconnect(self) -> None:
        logger.info(f"Disconnecting from shared memory for robot {self.robot_id}")
        self.shared_monitor_obstacles_lock = None
        self.shared_monitor_obstacles = None
        self.shared_obstacles_lock = None
        self.shared_rectangle_obstacles = None
        self.shared_circle_obstacles = None
        self.shared_lidar_data_lock = None
        self.shared_lidar_data = None
        self.shared_pose_current_buffer = None
        self.shared_memory = None
        self.robot_id = None
        if self.update_obstacles_timer is not None:
            self.update_obstacles_timer.stop()
            self.update_obstacles_timer.deleteLater()
            self.update_obstacles_timer = None
        self.apply_obstacle_data([], [])

    def update_obstacles(self) -> None:
        if self.shared_obstacles_lock is None:
            return

        rectangles: list[dict[str, float]] = []
        circles: list[dict[str, float]] = []

        self.shared_obstacles_lock.start_reading()
        try:
            if self.shared_rectangle_obstacles is not None:
                for rectangle_obstacle in self.shared_rectangle_obstacles:
                    center = rectangle_obstacle.center
                    rect_data: dict[str, float] = {
                        "x": center.x,
                        "y": center.y,
                        "angle": center.angle,
                        "length_x": rectangle_obstacle.length_x,
                        "length_y": rectangle_obstacle.length_y,
                    }
                    rect_data["bounding_box"] = [
                        {"x": vertex.x, "y": vertex.y} for vertex in rectangle_obstacle.bounding_box
                    ]
                    rectangles.append(rect_data)

            if self.shared_circle_obstacles is not None:
                for circle_obstacle in self.shared_circle_obstacles:
                    center = circle_obstacle.center
                    circle_data: dict[str, float] = {
                        "x": center.x,
                        "y": center.y,
                        "angle": center.angle,
                        "radius": circle_obstacle.radius,
                    }
                    circle_data["bounding_box"] = [
                        {"x": vertex.x, "y": vertex.y} for vertex in circle_obstacle.bounding_box
                    ]
                    circles.append(circle_data)
        finally:
            self.shared_obstacles_lock.finish_reading()

        self.apply_obstacle_data(rectangles, circles)

    def apply_obstacle_data(self, rectangles: list[dict[str, Any]], circles: list[dict[str, Any]]) -> None:
        targets = [self.view_item, self.scene_root]
        for target in targets:
            if target is None:
                continue
            if not Shiboken.isValid(target):
                continue
            target.setProperty("rectangleObstacles", rectangles)
            target.setProperty("circleObstacles", circles)
