from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from cogip.utils.singleton import Singleton
from .actions import Strategy
from .positions import StartPosition
from .table import TableEnum


@dataclass(config=ConfigDict(title="Planner Properties"))
class Properties(metaclass=Singleton):
    robot_id: Annotated[
        int,
        Field(
            ge=1,
            le=9,
            title="Robot ID",
            description="Robot ID",
            exclude=True,
        ),
    ]
    robot_width: Annotated[
        int,
        Field(
            ge=100,
            le=1000,
            title="Robot_width",
            description="Width of the robot (mm)",
        ),
    ]
    robot_length: Annotated[
        int,
        Field(
            ge=100,
            le=1000,
            title="Robot Length",
            description="Length of the robot (mm)",
        ),
    ]
    obstacle_radius: Annotated[
        int,
        Field(
            ge=100,
            le=1000,
            title="Obstacle Radius",
            description="Radius of a dynamic obstacle (mm)",
        ),
    ]
    obstacle_bb_margin: Annotated[
        float,
        Field(
            ge=0,
            le=1,
            multiple_of=0.01,
            title="Bounding Box Margin",
            description="Obstacle bounding box margin in percent of the radius (%)",
        ),
    ]
    obstacle_bb_vertices: Annotated[
        int,
        Field(
            ge=3,
            le=20,
            title="Bounding Box Vertices",
            description="Number of obstacle bounding box vertices",
        ),
    ]
    obstacle_updater_interval: Annotated[
        float,
        Field(
            ge=0.05,
            le=2.0,
            multiple_of=0.05,
            title="Obstacle Updater Interval",
            description="Interval between each obstacles list update (seconds)",
        ),
    ]
    path_refresh_interval: Annotated[
        float,
        Field(
            ge=0.001,
            le=2.0,
            multiple_of=0.001,
            title="Path Refresh Interval",
            description="Interval between each update of robot paths (seconds)",
        ),
    ]
    bypass_detector: Annotated[
        bool,
        Field(
            title="Bypass Detector",
            description="Use perfect obstacles from monitor instead of detected obstacles by Lidar",
        ),
    ]
    disable_fixed_obstacles: Annotated[
        bool,
        Field(
            title="Disable Fixed Obstacles",
            description="Disable fixed obstacles. Useful to work on Lidar obstacles and avoidance",
        ),
    ]
    table: Annotated[
        TableEnum,
        Field(
            title="Table",
            exclude=True,
        ),
    ]
    strategy: Annotated[
        Strategy,
        Field(
            title="Strategy",
            exclude=True,
        ),
    ]
    start_position: Annotated[
        StartPosition,
        Field(
            title="Start Position",
            exclude=True,
        ),
    ]
