"""
This module contains all data models used in the monitor.

The models are based on [Pydantic](https://pydantic-docs.helpmanual.io/) models,
allowing them to be loaded from/exported to JSON strings/files.
All values are automatically verified and converted to the expected data type,
an exception being raised if impossible.
"""

import math
import platform
from enum import IntEnum

import numpy as np
from numpy.typing import ArrayLike
from pydantic import BaseModel

from cogip.tools.copilot.messages import PB_PathPose


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


if platform.machine() == "x86_64":

    class SpeedEnum(IntEnum):
        """
        Speed levels.
        In mcu-firmware, the speeds (linear and angular) are float-point values,
        but they can take only 3 values: low, normal and max speed. These values
        depend on the platform, so on the Raspberry side, we only need to define
        the speed levels instead of the real values.

        Attributes:
            LOW:
            NORMAL:
            MAX:
        """

        LOW = 33
        NORMAL = 66
        MAX = 100
else:

    class SpeedEnum(IntEnum):
        LOW = 0
        NORMAL = 1
        MAX = 2


class PathPose(Pose):
    """
    Class representing a position in a path.

    Attributes:
        x: X coordinate
        y: Y coordinate
        O: 0-orientation
        max_speed_linear: max speed linear
        max_speed_angular: max speed angular
        allow_reverse: reverse mode
    """

    max_speed_linear: SpeedEnum = SpeedEnum.NORMAL
    max_speed_angular: SpeedEnum = SpeedEnum.NORMAL
    allow_reverse: bool = True

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


class LogMessage(BaseModel):
    """
    A log received on the serial port.

    Attributes:
        log: message
    """

    log: str


SerialMessage = RobotState | ShellMenu | LogMessage


class CameraExtrinsicParameters(BaseModel):
    """Model representing camera extrinsic properties"""

    x: float
    y: float
    z: float
    angle: float

    @property
    def tvec(self) -> ArrayLike:
        return np.array([self.x, self.y, self.z])
