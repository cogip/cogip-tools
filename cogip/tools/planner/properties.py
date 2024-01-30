from pydantic import Field
from pydantic.dataclasses import dataclass

from cogip.utils.singleton import Singleton


@dataclass
class Properties(metaclass=Singleton):
    robot_width: int = Field(
        ...,
        ge=100,
        le=1000,
        title="Robot_width",
        description="Width of the robot (mm)",
    )
    obstacle_radius: int = Field(
        ...,
        ge=100,
        le=1000,
        title="Obstacle Radius",
        description="Radius of a dynamic obstacle (mm)",
    )
    obstacle_bb_margin: float = Field(
        ...,
        ge=0,
        le=1,
        multiple_of=0.01,
        title="Bounding Box Margin",
        description="Obstacle bounding box margin in percent of the radius (%)",
    )
    obstacle_bb_vertices: int = Field(
        ...,
        ge=3,
        le=20,
        title="Bounding Box Vertices",
        description="Number of obstacle bounding box vertices",
    )
    max_distance: int = Field(
        ...,
        ge=0,
        le=4000,
        title="Max Distance",
        description="Maximum distance to take avoidance points into account (mm)",
    )
    obstacle_sender_interval: float = Field(
        ...,
        ge=0.1,
        le=2.0,
        multiple_of=0.05,
        title="Obstacle Sender Interval",
        description="Interval between each send of obstacles to dashboards (seconds)",
    )
    path_refresh_interval: float = Field(
        ...,
        ge=0.1,
        le=2.0,
        multiple_of=0.05,
        title="Path Refresh Interval",
        description="Interval between each update of robot paths (seconds)",
    )
    launcher_speed: int = Field(
        ...,
        ge=0,
        le=100,
        title="Launcher Speed",
        description="Launcher Speed",
    )
    esc_speed: int = Field(
        ...,
        ge=0,
        le=5,
        title="ESC Speed",
        description="ESC Speed",
    )
    plot: bool = Field(
        ...,
        title="Debug Plot",
        description="Display avoidance graph in realtime",
    )

    class Config:
        title = "Planner Properties"
