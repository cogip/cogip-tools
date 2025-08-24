from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from cogip.cpp.libraries.shared_memory import SharedProperties
from cogip.utils.singleton import Singleton
from .actions import Strategy
from .avoidance.avoidance import AvoidanceStrategy
from .positions import StartPosition
from .table import TableEnum


@dataclass(config=ConfigDict(title="Planner Properties", validate_assignment=True))
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
    avoidance_strategy: Annotated[
        AvoidanceStrategy,
        Field(
            title="Avoidance Strategy",
            exclude=True,
        ),
    ]

    def update_shared_properties(self, shared_properties: SharedProperties):
        """
        Update shared properties with the current properties.
        """
        shared_properties.robot_id = self.robot_id
        shared_properties.robot_width = self.robot_width
        shared_properties.robot_length = self.robot_length
        shared_properties.obstacle_radius = self.obstacle_radius
        shared_properties.obstacle_bb_margin = self.obstacle_bb_margin
        shared_properties.obstacle_bb_vertices = self.obstacle_bb_vertices
        shared_properties.obstacle_updater_interval = self.obstacle_updater_interval
        shared_properties.path_refresh_interval = self.path_refresh_interval
        shared_properties.bypass_detector = self.bypass_detector
        shared_properties.disable_fixed_obstacles = self.disable_fixed_obstacles
        shared_properties.table = self.table.val
        shared_properties.strategy = self.strategy.val
        shared_properties.start_position = self.start_position.val
        shared_properties.avoidance_strategy = self.avoidance_strategy.val
