from functools import partial

from PySide6.QtCore import QObject, QTimer
from PySide6.QtCore import SignalInstance as QtSignalInstance
from PySide6.QtGui import QVector3D
from PySide6.QtQml import QJSValue, QJSValueIterator

from cogip.models import models
from .. import logger
from ..shared_memory import SharedMemoryManager


class Robot:
    update_pose_current_interval: int = 100

    def __init__(
        self,
        root: QObject,
        view: QObject | None,
        robot_id: int,
        virtual_planner: bool,
        virtual_detector: bool,
    ):
        self.root = root
        self.scene = self.root.parent() if self.root else None
        self.view = view if view is not None else (self.scene.parent() if self.scene else None)
        self.robot_id = robot_id
        self.virtual_planner = virtual_planner
        self.virtual_detector = virtual_detector
        self.shm = SharedMemoryManager()
        self.lidar_ray_nodes: dict[int, QObject] = {}
        self.lidar_distances_changed: bool = False

        self.node = self.root.findChild(QObject, "Scene")
        self.models = [m for m in self.node.children() if m.metaObject().className() == "QQuick3DModel"]
        for model in self.models:
            model.setObjectName(f"robot_{model.objectName()}")

        self.update_pose_current_timer = QTimer(self.root)
        self.update_pose_current_timer.setInterval(Robot.update_pose_current_interval)
        self.update_pose_current_timer.timeout.connect(self.update_pose_current_from_shm)

        if self.virtual_planner:
            self.update_pose_current_timer.start()

        if self.virtual_detector:
            for i in range(360):
                self.shm.shared_lidar_data[i][0] = i
                self.shm.shared_lidar_data[i][2] = 255
            if self.robot_id > 1:
                for i in range(90, 270):
                    self.shm.shared_lidar_data[i][1] = 65535
            self.shm.shared_lidar_data[360][0] = -1

            # Find Lidar ray nodes
            if self.view is None:
                logger.warning("Unable to locate View3D instance for lidar ray binding")
            else:
                lidar_ray_nodes_prop: QJSValue = self.view.property("lidarRayNodes")
                it = QJSValueIterator(lidar_ray_nodes_prop)
                while it.hasNext():
                    it.next()
                    try:
                        index = int(it.name())
                    except ValueError:
                        continue
                    q_object = it.value().toQObject()
                    if not q_object:
                        continue
                    self.lidar_ray_nodes[index] = q_object

                    try:
                        signal_distance_changed: QtSignalInstance = q_object.distanceChanged
                        if isinstance(signal_distance_changed, QtSignalInstance):
                            signal_distance_changed.connect(partial(self.handle_distance_changed, index))
                    except AttributeError:
                        continue

                try:
                    signal_post_lidar_update: QtSignalInstance = self.view.postLidarUpdate
                    if isinstance(signal_post_lidar_update, QtSignalInstance):
                        signal_post_lidar_update.connect(self.post_lidar_update)
                except AttributeError:
                    logger.error("No postLidarUpdate signal found on view")

    def update_pose_current_from_shm(self) -> None:
        """
        Update pose current from shared memory.
        """
        if self.shm.shared_pose_current_buffer is None:
            return

        pose_current = self.shm.shared_pose_current_buffer.last
        if pose_current is None or self.root is None:
            return

        self.root.setProperty("x", pose_current.x)
        self.root.setProperty("y", pose_current.y)
        self.root.setProperty("eulerRotation", QVector3D(0, 0, pose_current.angle))

    def update_pose_current_from_model(self, pose_current: models.Pose) -> None:
        """
        Update pose current from model.
        """
        self.root.setProperty("x", pose_current.x)
        self.root.setProperty("y", pose_current.y)
        self.root.setProperty("eulerRotation", QVector3D(0, 0, pose_current.O))

    def handle_distance_changed(self, index: int) -> None:
        q_object = self.lidar_ray_nodes.get(index)
        if not q_object:
            return
        distance = q_object.property("distance")
        if abs(distance - self.shm.shared_lidar_data[index][1]) < 1.0:
            return
        self.lidar_distances_changed = True
        self.shm.shared_lidar_data[index][1] = distance

    def post_lidar_update(self) -> None:
        """
        Post lidar update to shared memory if distances have changed.
        """
        if self.lidar_distances_changed:
            self.lidar_distances_changed = False
            self.shm.shared_lidar_data_lock.post_update()
