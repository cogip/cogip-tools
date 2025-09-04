"""
This module contains all data models used in the monitor.

The models are based on [Pydantic](https://pydantic-docs.helpmanual.io/) models,
allowing them to be loaded from/exported to JSON strings/files.
All values are automatically verified and converted to the expected data type,
an exception being raised if impossible.
"""

import math

import numpy as np
from numpy.typing import ArrayLike
from pydantic import BaseModel

from cogip.cpp.libraries.models import Pose as SharedPose
from cogip.cpp.libraries.models import PoseOrder as SharedPoseOrder
from cogip.protobuf import PB_PathPose


class MenuEntry(BaseModel):
    """
    Represents one entry in a firmware's shell menu

    Attributes:
        cmd: Command name
        desc: Description of the command

    Examples:
        The following line shows how to initialize this class from a JSON
        string received on the serial port:
        ```py
        MenuEntry.model_validate_json("{\\"cmd\\": \\"_state\\", \\"desc\\": \\"Print current state\\"}")
        ```
    """

    cmd: str
    desc: str


class ShellMenu(BaseModel):
    """
    Represents a firmware's shell menu.

    Attributes:
        name: Name of the menu
        entries: List of the menu entries

    Examples:
        The following line shows how to initialize this class from a JSON
        string received on the serial port:
        ```py
        ShellMenu.model_validate_json(
            "{\\"name\\": \\"planner\\","
            " \\"entries\\": ["
            "    {\\"cmd\\": \\"_help_json\\", \\"desc\\": \\"Display available commands in JSON format\\"},"
            "    {\\"cmd\\": \\"_state\\", \\"desc\\": \\"Print current state\\"}
            "]}"
        )
        ```
    """

    name: str
    entries: list[MenuEntry]


class Vertex(BaseModel):
    """
    Represents a point in 2D/3D coordinates.

    Attributes:
        x: X position
        y: Y position
        z: Z position (optional)
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))


class Pose(Vertex):
    """
    A position of the robot.

    Attributes:
        x: X position
        y: Y position
        O: Rotation
    """

    O: float | None = 0.0  # noqa


class Speed(BaseModel):
    """
    A speed value.

    Attributes:
        distance: Linear speed
        angle: Angular speed
    """

    distance: float = 0.0
    angle: float = 0.0


class PathPose(Pose):
    """
    Class representing a position in a path.

    Attributes:
        x: X coordinate
        y: Y coordinate
        O: 0-orientation
        max_speed_linear: max linear speed in percentage of the robot max linear speed
        max_speed_angular: max angular speed in percentage of the robot max angular speed
        allow_reverse: reverse mode
        bypass_anti_blocking: send pose_reached if robot is blocked
        timeout_ms: max time is milliseconds to reach the pose, the robot stops if timeout is reached, 0 for no timeout
        bypass_final_orientation: do not set orientation pose order
        is_intermediate: whether this pose is an intermediate pose in a path
    """

    max_speed_linear: int = 66
    max_speed_angular: int = 66
    allow_reverse: bool = True
    bypass_anti_blocking: bool = False
    timeout_ms: int = 0
    bypass_final_orientation: bool = False
    is_intermediate: bool = False

    @property
    def pose(self) -> Pose:
        return Pose(**self.model_dump())

    def copy_pb(self, pb_path_pose: PB_PathPose) -> None:
        """
        Copy data in a Protobuf message.

        Arguments:
            pb_path_pose: Protobuf message to fill
        """
        pb_path_pose.pose.x = int(self.x)
        pb_path_pose.pose.y = int(self.y)
        pb_path_pose.pose.O = int(self.O)  # noqa
        pb_path_pose.max_speed_ratio_linear = self.max_speed_linear
        pb_path_pose.max_speed_ratio_angular = self.max_speed_angular
        pb_path_pose.allow_reverse = self.allow_reverse
        pb_path_pose.bypass_anti_blocking = self.bypass_anti_blocking
        pb_path_pose.timeout_ms = self.timeout_ms
        pb_path_pose.bypass_final_orientation = self.bypass_final_orientation
        pb_path_pose.is_intermediate = self.is_intermediate

    def to_shared(self, shared_pose_order: SharedPoseOrder | None) -> None:
        """
        Copy data in a Protobuf message.

        Arguments:
            pb_path_pose: Protobuf message to fill
        """
        if shared_pose_order is None:
            return
        shared_pose_order.x = int(self.x)
        shared_pose_order.y = int(self.y)
        shared_pose_order.angle = int(self.O)  # noqa
        shared_pose_order.max_speed_linear = self.max_speed_linear
        shared_pose_order.max_speed_angular = self.max_speed_angular
        shared_pose_order.allow_reverse = self.allow_reverse
        shared_pose_order.bypass_anti_blocking = self.bypass_anti_blocking
        shared_pose_order.bypass_final_orientation = self.bypass_final_orientation
        shared_pose_order.timeout_ms = self.timeout_ms
        shared_pose_order.is_intermediate = self.is_intermediate

    @classmethod
    def from_shared(cls, shared_pose: SharedPose | SharedPoseOrder) -> "PathPose":
        """
        Create a PathPose from a SharedPoseOrder.

        Arguments:
            shared_pose_order: SharedPoseOrder to convert

        Returns:
            A PathPose instance with the data from the SharedPoseOrder.
        """
        path_pose = cls(
            x=shared_pose.x,
            y=shared_pose.y,
            O=shared_pose.angle,  # noqa
        )
        if isinstance(shared_pose, SharedPoseOrder):
            path_pose.max_speed_linear = shared_pose.max_speed_linear
            path_pose.max_speed_angular = shared_pose.max_speed_angular
            path_pose.allow_reverse = shared_pose.allow_reverse
            path_pose.bypass_anti_blocking = shared_pose.bypass_anti_blocking
            path_pose.timeout_ms = shared_pose.timeout_ms
            path_pose.bypass_final_orientation = shared_pose.bypass_final_orientation
            path_pose.is_intermediate = shared_pose.is_intermediate

        return path_pose


class DynObstacleRect(BaseModel):
    """
    A dynamic rectangle obstacle created by the robot.

    Attributes:
        x: X coordinate of the obstacle center
        y: Y coordinate of the obstacle center
        angle: Orientation of the obstacle
        length_x: length along X axis
        length_y: length along Y axis
        bb: bounding box
    """

    x: float
    y: float
    angle: float
    length_x: float
    length_y: float
    bb: list[Vertex] = []

    def contains(self, point: Vertex) -> bool:
        half_length_x = self.length_x / 2
        half_length_y = self.length_y / 2

        return (self.x - half_length_x <= point.x <= self.x + half_length_x) and (
            self.y - half_length_y <= point.y <= self.y + half_length_y
        )

    def create_bounding_box(self, bb_radius: float, nb_vertices: int = 4):
        half_length_x = self.length_x / 2
        half_length_y = self.length_y / 2

        self.bb = [
            Vertex(x=self.x - half_length_x - bb_radius, y=self.y + half_length_y + bb_radius),
            Vertex(x=self.x + half_length_x + bb_radius, y=self.y + half_length_y + bb_radius),
            Vertex(x=self.x + half_length_x + bb_radius, y=self.y - half_length_y - bb_radius),
            Vertex(x=self.x - half_length_x - bb_radius, y=self.y - half_length_y - bb_radius),
        ]

    def __hash__(self):
        """
        Hash function to allow this class to be used as a key in a dict.
        """
        return hash((type(self),) + tuple(self.__root__))


class DynRoundObstacle(BaseModel):
    """
    A dynamic round obstacle created by the robot.

    Attributes:
        x: Center X position
        y: Center Y position
        radius: Radius of the obstacle
        bb: bounding box
    """

    x: float
    y: float
    radius: float
    bb: list[Vertex] = []

    def contains(self, point: Vertex) -> bool:
        return (point.x - self.x) * (point.x - self.x) + (point.y - self.y) * (point.y - self.y) <= self.radius**2

    def create_bounding_box(self, bb_radius, nb_vertices):
        self.bb = [
            Vertex(
                x=self.x + bb_radius * math.cos(tmp := (i * 2 * math.pi) / nb_vertices),
                y=self.y + bb_radius * math.sin(tmp),
            )
            for i in reversed(range(nb_vertices))
        ]

    def __hash__(self):
        """
        Hash function to allow this class to be used as a key in a dict.
        """
        return hash((type(self),) + tuple(self.__root__))


DynObstacle = DynRoundObstacle | DynObstacleRect
DynObstacleList = list[DynObstacle]


class RobotState(BaseModel):
    """
    This contains information about robot state,
    like mode, cycle, positions, speed, path and obstacles.
    It is given by the firmware through the serial port.

    Attributes:
        pose_order: Position to reach
        cycle: Current cycle
        speed_current: Current speed
        speed_order: Speed order
        path: Computed path
    """

    pose_current: Pose = Pose()
    pose_order: Pose = Pose()
    cycle: int = 0
    speed_current: Speed = Speed()
    speed_order: Speed = Speed()


class Obstacle(BaseModel):
    """
    Contains the properties of an obstacle added on the table.

    Attributes:
        x: X position
        y: Y position
        rotation: Rotation
        length: Length
        width: Width
        height: Height
        bb: bounding box
    """

    x: int = 0
    y: int = 1000
    rotation: int = 0
    length: int = 200
    width: int = 200
    height: int = 600


ObstacleList = list[Obstacle]


class CameraExtrinsicParameters(BaseModel):
    """Model representing camera extrinsic properties"""

    x: float
    y: float
    z: float
    angle: float

    @property
    def tvec(self) -> ArrayLike:
        return np.array([self.x, self.y, self.z])
