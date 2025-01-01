from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from cogip.utils.singleton import Singleton


@dataclass(config=ConfigDict(title="Planner Properties"))
class Properties(metaclass=Singleton):
    robot_id: Annotated[
        int,
        Field(
            ge=1,
            le=9,
            title="Robot ID",
            description="Robot ID",
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
    max_distance: Annotated[
        int,
        Field(
            ge=0,
            le=4000,
            title="Max Distance",
            description="Maximum distance to take avoidance points into account (mm)",
        ),
    ]
    obstacle_sender_interval: Annotated[
        float,
        Field(
            ge=0.05,
            le=2.0,
            multiple_of=0.05,
            title="Obstacle Sender Interval",
            description="Interval between each send of obstacles to dashboards (seconds)",
        ),
    ]
    path_refresh_interval: Annotated[
        float,
        Field(
            ge=0.1,
            le=2.0,
            multiple_of=0.05,
            title="Path Refresh Interval",
            description="Interval between each update of robot paths (seconds)",
        ),
    ]
    plot: Annotated[
        bool,
        Field(
            title="Debug Plot",
            description="Display avoidance graph in realtime",
        ),
    ]
