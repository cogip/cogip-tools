"""Action to test continuous rotation on the spot."""

from functools import partial
from typing import TYPE_CHECKING

from cogip.models import models
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner


class TestRotationAction(Action):
    """
    Action to rotate the robot continuously on the spot.

    The robot stays at the same (x, y) position and rotates through
    different angles in a loop.
    """

    def __init__(self, planner: "Planner", strategy: Strategy):
        super().__init__("TestRotation", planner, strategy)
        # Start position - center of training table area
        self.pos_x = -500
        self.pos_y = -750

        # Rotation angles (in degrees)
        self.angles = [0, 90, 180, 270]

        self.angular_speed = 50

        self.before_action_func = self.init_action

        # Pre-create all rotation poses with fixed coordinates
        self.rotation_poses: list[Pose] = []
        for angle in self.angles:
            pose = Pose(
                x=self.pos_x,
                y=self.pos_y,
                O=angle,
                max_speed_linear=0,
                max_speed_angular=self.angular_speed,
            )
            pose.after_pose_func = partial(self.append_next_pose, pose)
            self.rotation_poses.append(pose)

    async def init_action(self):
        """Initialize robot position and start rotation loop."""
        # Set robot start position - this updates shared memory and firmware
        pose_init = models.Pose(
            x=self.pos_x,
            y=self.pos_y,
            O=self.angles[0],
        )
        await self.planner.set_pose_start(pose_init)

        self.planner.pose_reached = False
        self.planner.action = self

        # Start with first rotation pose (0°)
        self.poses.append(self.rotation_poses[0])

    async def append_next_pose(self, current_pose: Pose) -> None:
        """Append the next rotation pose in the circular sequence."""
        # Find current pose in the list and get next one
        current_index = self.rotation_poses.index(current_pose)
        next_index = (current_index + 1) % len(self.rotation_poses)
        self.poses.append(self.rotation_poses[next_index])

    def weight(self) -> float:
        """Return action weight for priority."""
        return 1000000.0


class TestRotationStrategy(Strategy):
    """Strategy to execute the rotation test action."""

    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(TestRotationAction(planner, self))
