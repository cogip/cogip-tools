from collections.abc import Sequence
from typing import Any

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt
from PySide6.QtCore import Signal as QtSignal
from PySide6.QtCore import Slot as QtSlot
from PySide6.QtQml import QmlElement

from cogip.models import models
from . import logger
from .artifacts.artifacts import add_artifacts
from .obstacle import ObstacleStorage, ObstacleWindowSettings
from .robots.ninja_manual import NinjaManual
from .robots.pami_manual import PamiManual
from .robots.robot import Robot
from .robots.robot_manual import RobotManual
from .robots.robot_order import RobotOrder
from .shared_memory import SharedMemoryManager

QML_IMPORT_NAME = "View3DBackend"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class View3DBackend(QObject):
    def __init__(self, root: QObject):
        super().__init__()
        self.root = root
        self.robot_id: int | None = None
        self.virtual_planner: bool | None = None
        self.virtual_detector: bool | None = None
        self.view_item = self.root.findChild(QObject, "view") if self.root else None
        self.robot_manual = RobotManual(self.root.findChild(QObject, "robotManual"))
        self.ninja_manual = NinjaManual(self.root.findChild(QObject, "ninjaManual"))
        self.pami_manual = PamiManual(self.root.findChild(QObject, "pamiManual"))
        self.obstacle_window_settings = ObstacleWindowSettings()
        self.root.setProperty("obstacleSettings", self.obstacle_window_settings)
        self.live_robot: Robot | None = None
        self.order_robot: RobotOrder | None = None
        self.shm = SharedMemoryManager()
        self.shm.set_scene(self.root, self.view_item)
        signal: QtSignal | None = getattr(self.root, "liveRobotNodeChanged", None)
        if signal and isinstance(signal, QtSignal):
            signal.connect(self.handle_live_robot_node_changed)
        self.handle_live_robot_node_changed()
        signal: QtSignal | None = getattr(self.root, "orderRobotNodeChanged", None)
        if signal and isinstance(signal, QtSignal):
            signal.connect(self.handle_order_robot_node_changed)
        self.handle_order_robot_node_changed()
        add_artifacts(self.root)

    def __del__(self):
        try:
            self.shm.set_scene(None, None)
            self.shm.disconnect()
        except RuntimeError:
            logger.debug("Shared memory cleanup skipped; scene already deleted")
        logger.info("View3D instance deleted")

    def handle_add_robot(self, robot_id: int, virtual_planner: bool, virtual_detector: bool) -> None:
        if not self.root:
            logger.warning("View3D root not available for add_robot")
            return
        self.robot_id = robot_id
        self.virtual_planner = virtual_planner
        self.virtual_detector = virtual_detector
        self.root.setProperty("virtualDetector", virtual_detector)
        self.root.setProperty("virtualPlanner", virtual_planner)
        self.shm.connect(robot_id, virtual_planner, virtual_detector)
        logger.info(
            "Adding robot %s (virtual_planner=%s, virtual_detector=%s)", robot_id, virtual_planner, virtual_detector
        )
        QMetaObject.invokeMethod(
            self.root,
            "addRobotInstance",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG("QVariant", int(robot_id)),
        )
        QMetaObject.invokeMethod(
            self.root,
            "addOrderRobotInstance",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG("QVariant", int(robot_id)),
        )

    def handle_del_robot(self, robot_id: int) -> None:
        if not self.root:
            logger.warning("View3D root not available for del_robot")
            return
        logger.info("Removing robot %s", robot_id)
        QMetaObject.invokeMethod(
            self.root,
            "removeRobotInstance",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG("QVariant", int(robot_id)),
        )
        QMetaObject.invokeMethod(
            self.root,
            "removeOrderRobotInstance",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG("QVariant", int(robot_id)),
        )
        self.shm.disconnect()
        self.robot_id = None
        self.virtual_planner = None
        self.virtual_detector = None
        self.root.setProperty("virtualDetector", False)
        self.root.setProperty("virtualPlanner", False)
        if self.view_item is not None:
            self.view_item.setProperty("robotPathPoints", [])
            self.view_item.setProperty("rectangleObstacles", [])
            self.view_item.setProperty("circleObstacles", [])
        if self.root is not None:
            self.root.setProperty("robotPathPoints", [])
            self.root.setProperty("rectangleObstacles", [])
            self.root.setProperty("circleObstacles", [])

    def handle_pose_current(self, pose_current: models.Pose) -> None:
        if self.live_robot and not self.virtual_planner:
            self.live_robot.update_pose_current_from_model(pose_current)

    def handle_robot_path(self, path: list[models.Pose]) -> None:
        if len(path) <= 1:
            if self.view_item is not None:
                self.view_item.setProperty("robotPathPoints", [])
            if self.root is not None:
                self.root.setProperty("robotPathPoints", [])
            return

        if self.order_robot:
            self.order_robot.set_pose_order(path[1])

        path_points: list[dict[str, float]] = [
            {
                "x": pose.x,
                "y": pose.y,
                "z": 0.0,
            }
            for pose in path
        ]
        if self.view_item is not None:
            self.view_item.setProperty("robotPathPoints", path_points)
        if self.root is not None:
            self.root.setProperty("robotPathPoints", path_points)

    def handle_live_robot_node_changed(self) -> None:
        node = self.root.property("liveRobotNode") if self.root else None
        if not node:
            if self.live_robot:
                logger.info("Live robot instance cleared")
            self.live_robot = None
            return

        if self.robot_id is None:
            logger.warning("Live robot node available but robot metadata is missing")
            return

        if self.live_robot and self.live_robot.root is node:
            return

        self.live_robot = Robot(node, self.view_item, self.robot_id, self.virtual_planner, self.virtual_detector)
        logger.info("Live robot instance initialized")

    def handle_order_robot_node_changed(self) -> None:
        node = self.root.property("orderRobotNode") if self.root else None
        if not node:
            if self.order_robot:
                logger.info("Order robot instance cleared")
            self.order_robot = None
            return

        if self.robot_id is None:
            logger.warning("Order robot node available but robot metadata is missing")
            return

        if self.order_robot and self.order_robot.root is node:
            return

        self.order_robot = RobotOrder(node, self.robot_id)
        logger.info("Order robot instance initialized")

    @QtSlot("QVariant")
    def update_shared_obstacles(self, obstacles: Sequence[Any] | None) -> None:
        if not self.virtual_detector:
            return

        obstacles = ObstacleStorage.coerce_data(obstacles)

        self.shm.shared_monitor_obstacles_lock.start_writing()
        self.shm.shared_monitor_obstacles.clear()
        for obstacle in obstacles:
            self.shm.shared_monitor_obstacles.append(obstacle["x"], obstacle["y"])
        self.shm.shared_monitor_obstacles_lock.finish_writing()
