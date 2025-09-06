import math
from typing import TYPE_CHECKING

from cogip import models

if TYPE_CHECKING:
    from ..planner import Planner


def get_relative_pose(
    reference_pose: models.Pose,
    *,
    front_offset: float,
    side_offset: float = 0.0,
    angular_offset: float = 0.0,
) -> models.Pose:
    """
    Get a new pose relative to the reference pose with the specified linear and angular offsets.

    Args:
        reference_pose: The reference pose.
        front_offset: The offset in the direction of the reference's front.
        side_offset: The offset in the direction of the reference's side. Positive is to the left.
        angular_offset: The angular offset in degrees.
    """
    # This function calculates a new pose relative to a reference pose.
    new_x = (
        reference_pose.x
        + front_offset * math.cos(math.radians(reference_pose.O))
        - side_offset * math.sin(math.radians(reference_pose.O))
    )
    new_y = (
        reference_pose.y
        + front_offset * math.sin(math.radians(reference_pose.O))
        + side_offset * math.cos(math.radians(reference_pose.O))
    )
    # Normalize the angle to be between 0 and 360 degrees
    new_angle = (reference_pose.O + angular_offset) % 360
    return models.Pose(x=new_x, y=new_y, O=new_angle)


async def set_countdown_color(planner: "Planner", color: "str"):
    await planner.sio_ns.emit(
        "start_countdown",
        (
            planner.robot_id,
            planner.game_context.game_duration,
            planner.countdown_start_timestamp.isoformat(),
            color,
        ),
    )
