"""
This module contains all data models used in the monitor.

The models are based on [Pydantic](https://pydantic-docs.helpmanual.io/) models,
allowing them to be loaded from/exported to JSON strings/files.
All values are automatically verified and converted to the expected data type,
an exception being raised if impossible.
"""

import numpy as np
from numpy.typing import ArrayLike
from pydantic import BaseModel, Field
from typing import List, Tuple

from cogip.protobuf import PB_PathPose
#from cogip.cpp.avoidance import CppObstacleCircle, CppObstaclePolygon, CppObstacleRectangle


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
    """

    max_speed_linear: int = 66
    max_speed_angular: int = 66
    allow_reverse: bool = True
    bypass_anti_blocking: bool = False
    timeout_ms: int = 0
    bypass_final_orientation: bool = False
    _cython_obj: 'CppPose' = None  # Reference to the Cython object

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

    def __init__(self, **data):
        super().__init__(**data)
        from cogip.cpp.avoidance import CppPose  # Import here to avoid compilation issues
        self._cython_obj = CppPose(
            x=self.x,
            y=self.y,
            O=self.O,
        )

    @classmethod
    def from_cython(cls, cython_obj):
        return cls(
            x=cython_obj.x,
            y=cython_obj.y,
            O=cython_obj.O,
            _cython_obj=cython_obj
        )

# DTO for CppObstacleCircle
class DynRoundObstacle(BaseModel):
    x: float = Field(...)
    y: float = Field(...)
    angle: float = Field(...)
    radius: float = Field(...)
    _cython_obj: 'CppObstacleCircle' = None  # Reference to the Cython object

    def __init__(self, **data):
        super().__init__(**data)
        from cogip.cpp.avoidance import CppObstacleCircle  # Import here to avoid compilation issues
        self._cython_obj = CppObstacleCircle(
            x=self.x,
            y=self.y,
            angle=self.angle,
            radius=self.radius
        )

    @classmethod
    def from_cython(cls, cython_obj):
        return cls(
            x=cython_obj.x,
            y=cython_obj.y,
            angle=cython_obj.angle,
            radius=cython_obj.radius,
            _cython_obj=cython_obj
        )

# DTO for CppObstaclePolygon
class DynObstaclePolygon(BaseModel):
    points: List[Tuple[float, float]] = Field(..., description="List of polygon points")
    _cython_obj: 'CppObstaclePolygon' = None  # Reference to the Cython object

    def __init__(self, **data):
        super().__init__(**data)
        from cogip.cpp.avoidance import CppObstaclePolygon  # Import here to avoid compilation issues
        self._cython_obj = CppObstaclePolygon(
            points=self.points
        )

    @classmethod
    def from_cython(cls, cython_obj):
        points = [(point.x(), point.y()) for point in cython_obj.c_obstacle_polygon.get_points()]
        return cls(points=points, _cython_obj=cython_obj)

# DTO for CppObstacleRectangle
class DynObstacleRect(BaseModel):
    x: float = Field(0.0, description="X position")
    y: float = Field(0.0, description="Y position")
    angle: float = Field(0.0, description="Rotation angle")
    length_x: float = Field(..., description="Rectangle length in X direction")
    length_y: float = Field(..., description="Rectangle length in Y direction")
    _cython_obj: 'CppObstacleRectangle' = None  # Reference to the Cython object

    def __init__(self, **data):
        super().__init__(**data)
        from cogip.cpp.avoidance import CppObstacleRectangle  # Import here to avoid compilation issues
        self._cython_obj = CppObstacleRectangle(
            x=self.x,
            y=self.y,
            angle=self.angle,
            length_x=self.length_x,
            length_y=self.length_y
        )

    @classmethod
    def from_cython(cls, cython_obj):
        return cls(
            x=cython_obj.x,
            y=cython_obj.y,
            angle=cython_obj.angle,
            length_x=cython_obj.length_x,
            length_y=cython_obj.length_y,
            _cython_obj=cython_obj
        )

DynObstacle = DynRoundObstacle | DynObstaclePolygon | DynObstacleRect
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
