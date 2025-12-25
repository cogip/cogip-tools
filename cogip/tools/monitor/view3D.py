from collections.abc import Sequence
from typing import Any

import numpy as np
from PySide6.QtCore import Q_ARG, Property, QMetaObject, QObject, Qt, QTimer
from PySide6.QtCore import Signal as QtSignal
from PySide6.QtCore import Slot as QtSlot
from PySide6.QtQml import QmlElement
from PySide6.QtQuick import QQuickItemGrabResult

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
    sim_camera_update_interval_ms = 50  # 20 FPS
    robotIdChanged = QtSignal()

    def __init__(self, root: QObject):
        super().__init__()
        self._robot_id: int | None = None
        self.root = root
        self.virtual_planner: bool | None = None
        self.virtual_detector: bool | None = None
        self.view_item = self.root.findChild(QObject, "view") if self.root else None
        self.pip_view = self.root.findChild(QObject, "pipView") if self.root else None
        self.sim_camera_timer = QTimer()
        self.sim_camera_timer.setInterval(self.sim_camera_update_interval_ms)
        self.sim_camera_timer.timeout.connect(self.update_sim_camera)
        self.robot_manual = RobotManual(self.view_item.findChild(QObject, "robotManual"))
        self.ninja_manual = NinjaManual(self.view_item.findChild(QObject, "ninjaManual"))
        self.pami_manual = PamiManual(self.view_item.findChild(QObject, "pamiManual"))
        self.obstacle_window_settings = ObstacleWindowSettings()
        self.view_item.setProperty("obstacleSettings", self.obstacle_window_settings)
        self.live_robot: Robot | None = None
        self.order_robot: RobotOrder | None = None
        self.shm = SharedMemoryManager()
        self.shm.set_scene(self.root, self.view_item)
        signal: QtSignal | None = getattr(self.view_item, "liveRobotNodeChanged", None)
        if signal and isinstance(signal, QtSignal):
            signal.connect(self.handle_live_robot_node_changed)
        self.handle_live_robot_node_changed()
        signal: QtSignal | None = getattr(self.view_item, "orderRobotNodeChanged", None)
        if signal and isinstance(signal, QtSignal):
            signal.connect(self.handle_order_robot_node_changed)
        self.handle_order_robot_node_changed()
        add_artifacts(self.view_item)

    @Property(int, notify=robotIdChanged)
    def robotId(self) -> int:
        return self._robot_id if self._robot_id is not None else -1

    def update_sim_camera(self):
        if not self.pip_view or self._robot_id is None:
            return
        QMetaObject.invokeMethod(self.root, "grabPipView")

    @QtSlot(QObject)
    def process_grab_result(self, result: QQuickItemGrabResult):
        image = result.image()
        if image.isNull():
            return

        ptr = image.constBits()
        arr = np.array(ptr).reshape((image.height(), image.width(), 4))
        self.shm.shared_sim_camera_data_lock.start_writing()
        self.shm.shared_sim_camera_data[:] = arr[:]
        self.shm.shared_sim_camera_data_lock.finish_writing()

    def __del__(self):
        try:
            self.shm.set_scene(None, None)
            self.shm.disconnect()
        except RuntimeError:
            logger.debug("Shared memory cleanup skipped; scene already deleted")
        logger.info("View3D instance deleted")

    def handle_add_robot(self, robot_id: int, virtual_planner: bool, virtual_detector: bool) -> None:
        if not self.view_item:
            logger.warning("View3D view_item not available for add_robot")
            return
        self._robot_id = robot_id
        self.robotIdChanged.emit()
        self.virtual_planner = virtual_planner
        self.virtual_detector = virtual_detector
        self.view_item.setProperty("virtualDetector", virtual_detector)
        self.view_item.setProperty("virtualPlanner", virtual_planner)
        self.shm.connect(robot_id, virtual_planner, virtual_detector)
        logger.info(
            "Adding robot %s (virtual_planner=%s, virtual_detector=%s)", robot_id, virtual_planner, virtual_detector
        )
        QMetaObject.invokeMethod(
            self.view_item,
            "addRobotInstance",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG("QVariant", int(robot_id)),
        )
        QMetaObject.invokeMethod(
            self.view_item,
            "addOrderRobotInstance",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG("QVariant", int(robot_id)),
        )
        if self.pip_view and virtual_planner:
            self.sim_camera_timer.start()

    def handle_del_robot(self, robot_id: int) -> None:
        if not self.view_item:
            logger.warning("View3D view_item not available for del_robot")
            return
        self._robot_id = None
        self.robotIdChanged.emit()
        logger.info("Removing robot %s", robot_id)
        self.sim_camera_timer.stop()
        QMetaObject.invokeMethod(
            self.view_item,
            "removeRobotInstance",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG("QVariant", int(robot_id)),
        )
        QMetaObject.invokeMethod(
            self.view_item,
            "removeOrderRobotInstance",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG("QVariant", int(robot_id)),
        )
        self.shm.disconnect()
        self.virtual_planner = None
        self.virtual_detector = None
        self.view_item.setProperty("virtualDetector", False)
        self.view_item.setProperty("virtualPlanner", False)
        if self.view_item is not None:
            self.view_item.setProperty("robotPathPoints", [])
            self.view_item.setProperty("rectangleObstacles", [])
            self.view_item.setProperty("circleObstacles", [])
        # if self.root is not None:
        #     self.root.setProperty("robotPathPoints", [])
        #     self.root.setProperty("rectangleObstacles", [])
        #     self.root.setProperty("circleObstacles", [])

    def handle_pose_current(self, pose_current: models.Pose) -> None:
        if self.live_robot and not self.virtual_planner:
            self.live_robot.update_pose_current_from_model(pose_current)

    def handle_robot_path(self, path: list[models.Pose]) -> None:
        if len(path) <= 1:
            if self.view_item is not None:
                self.view_item.setProperty("robotPathPoints", [])
            # if self.root is not None:
            #     self.root.setProperty("robotPathPoints", [])
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
        # if self.root is not None:
        #     self.root.setProperty("robotPathPoints", path_points)

    def handle_live_robot_node_changed(self) -> None:
        node = self.view_item.property("liveRobotNode") if self.view_item else None
        if not node:
            if self.live_robot:
                logger.info("Live robot instance cleared")
            self.live_robot = None
            return

        if self._robot_id is None:
            logger.warning("Live robot node available but robot metadata is missing")
            return

        if self.live_robot and self.live_robot.root is node:
            return

        self.live_robot = Robot(node, self.view_item, self._robot_id, self.virtual_planner, self.virtual_detector)
        logger.info("Live robot instance initialized")

    def handle_order_robot_node_changed(self) -> None:
        node = self.view_item.property("orderRobotNode") if self.view_item else None
        if not node:
            if self.order_robot:
                logger.info("Order robot instance cleared")
            self.order_robot = None
            return

        if self._robot_id is None:
            logger.warning("Order robot node available but robot metadata is missing")
            return

        if self.order_robot and self.order_robot.root is node:
            return

        self.order_robot = RobotOrder(node, self._robot_id)
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
