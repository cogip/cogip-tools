from __future__ import annotations
import math
from pathlib import Path

from numpy.typing import NDArray
from PySide6 import QtCore, QtGui
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DRender import Qt3DRender
from PySide6.QtCore import Slot as qtSlot

from cogip.cpp.libraries.models import Pose as SharedPose
from cogip.cpp.libraries.obstacles import ObstacleCircleList as SharedObstacleCircleList
from cogip.cpp.libraries.obstacles import ObstacleRectangleList as SharedObstacleRectangleList
from cogip.cpp.libraries.shared_memory import LockName, SharedMemory, WritePriorityLock
from cogip.models import Pose
from cogip.tools.monitor.mainwindow import MainWindow
from .asset import AssetEntity
from .robot_order import RobotOrderEntity
from .sensor import LidarSensor, Sensor, ToFSensor


class RobotEntity(AssetEntity):
    """
    The robot entity displayed on the table.

    Attributes:
        update_pose_current_interval: Interval in milliseconds between each current pose update
        order_robot:: Entity that represents the robot next destination
    """

    update_pose_current_interval: int = 100
    order_robot: RobotOrderEntity = None

    def __init__(self, robot_id: int, win: MainWindow, parent: Qt3DCore.QEntity | None = None):
        """
        Class constructor.

        Inherits [AssetEntity][cogip.entities.asset.AssetEntity].
        """
        self.win = win
        asset_path = Path(f"assets/{'robot' if robot_id == 1 else 'pami'}2024.dae")
        super().__init__(asset_path, parent=parent)
        self.robot_id = robot_id
        self.sensors: list[Sensor] = []
        self.rect_obstacles_pool = []
        self.round_obstacles_pool = []
        self.beacon_entity: Qt3DCore.QEntity | None = None

        self.shared_memory: SharedMemory | None = None
        self.shared_pose_current: SharedPose | None = None
        self.shared_lidar_data: NDArray | None = None
        self.shared_lidar_data_lock: WritePriorityLock | None = None
        self.shared_circle_obstacles: SharedObstacleCircleList | None = None
        self.shared_rectangle_obstacles: SharedObstacleRectangleList | None = None

        if robot_id == 1:
            self.beacon_entity = Qt3DCore.QEntity(self)
            self.beacon_mesh = Qt3DExtras.QCylinderMesh(self.beacon_entity)
            self.beacon_mesh.setLength(80)
            self.beacon_mesh.setRadius(40)
            self.beacon_entity.addComponent(self.beacon_mesh)

            self.beacon_transform = Qt3DCore.QTransform(self.beacon_entity)
            self.beacon_transform.setTranslation(QtGui.QVector3D(0, 0, 350 + self.beacon_mesh.length() / 2))
            self.beacon_transform.setRotationX(90)
            self.beacon_entity.addComponent(self.beacon_transform)

            # Create a layer used by sensors to activate detection on the beacon
            self.beacon_entity.layer = Qt3DRender.QLayer(self.beacon_entity)
            self.beacon_entity.layer.setRecursive(True)
            self.beacon_entity.layer.setEnabled(True)
            self.beacon_entity.addComponent(self.beacon_entity.layer)

        self.update_pose_current_timer = QtCore.QTimer()
        self.update_pose_current_timer.timeout.connect(self.update_pose_current)

    def setEnabled(self, isEnabled):
        if isEnabled:
            self.shared_memory = SharedMemory(f"cogip_{self.robot_id}")
            self.shared_pose_current = self.shared_memory.get_pose_current()
            self.shared_lidar_data = self.shared_memory.get_lidar_data()
            self.shared_lidar_data_lock = self.shared_memory.get_lock(LockName.LidarData)
            self.shared_circle_obstacles = self.shared_memory.get_circle_obstacles()
            self.shared_rectangle_obstacles = self.shared_memory.get_rectangle_obstacles()
            for i in range(360):
                self.shared_lidar_data[i][1] = 255
            for self.sensor in self.sensors:
                self.sensor.shared_sensor_data = self.shared_lidar_data
            self.update_pose_current_timer.start(RobotEntity.update_pose_current_interval)
        else:
            for self.sensor in self.sensors:
                self.sensor.shared_sensor_data = None
            self.update_pose_current_timer.stop()
            self.shared_rectangle_obstacles = None
            self.shared_circle_obstacles = None
            self.shared_lidar_data_lock = None
            self.shared_lidar_data = None
            self.shared_pose_current = None
            self.shared_memory = None
        return super().setEnabled(isEnabled)

    def post_init(self):
        """
        Function called once the asset has been loaded.

        Set the color and enable sensors.
        """
        super().post_init()

        if self.robot_id == 1:
            self.add_lidar_sensors()
        else:
            self.add_tof_sensor()

        self.order_robot = RobotOrderEntity(self.parent(), self.robot_id)

        if self.beacon_entity:
            Sensor.add_obstacle(self.beacon_entity)

    def add_lidar_sensors(self):
        """
        Add LIDAR sensors to the robot entity,
        one by degree around the top of the robot.
        """

        radius = 65.0 / 2

        for i in range(0, 360):
            angle = (360 - i) % 360
            origin_x = radius * math.sin(math.radians(90 - angle))
            origin_y = radius * math.cos(math.radians(90 - angle))
            sensor = LidarSensor(
                asset_entity=self,
                name=f"Lidar {angle}",
                angle=i,
                origin_x=origin_x,
                origin_y=origin_y,
                direction_x=origin_x,
                direction_y=origin_y,
            )
            sensor.shared_sensor_data = self.shared_lidar_data
            self.sensors.append(sensor)

    def add_tof_sensor(self):
        """
        Add a ToF sensor in front of the robot entity.
        """
        sensor = ToFSensor(
            asset_entity=self,
            name="ToF",
            angle=0,
            origin_x=106,
            origin_y=0,
        )
        sensor.shared_sensor_data = self.shared_lidar_data
        self.sensors.append(sensor)

    def update_pose_current(self) -> None:
        """
        Update pose current from shared memory.
        """
        self.transform_component.setTranslation(
            QtGui.QVector3D(self.shared_pose_current.x, self.shared_pose_current.y, 0)
        )
        self.transform_component.setRotationZ(self.shared_pose_current.angle)
        self.win.new_robot_pose(
            self.robot_id,
            Pose(x=self.shared_pose_current.x, y=self.shared_pose_current.y, O=self.shared_pose_current.angle),
        )

    @qtSlot(Pose)
    def new_robot_pose_order(self, new_pose: Pose) -> None:
        """
        Qt slot called to set the robot's new pose order.

        Arguments:
            new_pose: new robot pose
        """
        if self.order_robot:
            self.order_robot.transform.setTranslation(QtGui.QVector3D(new_pose.x, new_pose.y, 0))
            self.order_robot.transform.setRotationZ(new_pose.O)

    def start_sensors_emulation(self) -> None:
        """
        Start timers triggering sensors update and Lidar data emission.
        """
        for sensor in self.sensors:
            sensor.ray_caster.setEnabled(True)

    def stop_sensors_emulation(self) -> None:
        """
        Stop timers triggering sensors update and sensors data emission.
        """
        for sensor in self.sensors:
            sensor.ray_caster.setEnabled(False)
