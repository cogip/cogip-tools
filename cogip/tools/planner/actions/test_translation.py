"""Action to test forward-only and backward-only translations."""

from functools import partial
from typing import TYPE_CHECKING

from cogip.models import models
from cogip.models.models import MotionDirection
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner


class TestTranslationAction(Action):
    """
    Action to test forward-only and backward-only translations.

    The robot alternates between:
    1. Backward-only translation (robot turns around then backs up)
    2. Forward-only translation (robot goes forward directly)
    """

    def __init__(self, planner: "Planner", strategy: Strategy):
        super().__init__("TestTranslation", planner, strategy)

        # Start position - center of training table area
        self.start_x = -800
        self.start_y = -1200
        self.start_angle = 0

        # Target position for translations
        self.target_x = -300
        self.target_y = -1200

        # Speed settings
        self.linear_speed = 50
        self.angular_speed = 50

        self.before_action_func = self.init_action

        # Pre-create all translation poses
        self.translation_poses: list[Pose] = []

        # Pose 1: Go to target with BACKWARD_ONLY
        # Robot will turn around (180°) then back up to target
        pose_backward = Pose(
            x=self.target_x,
            y=self.target_y,
            O=self.start_angle,
            max_speed_linear=self.linear_speed,
            max_speed_angular=self.angular_speed,
            motion_direction=MotionDirection.BACKWARD_ONLY,
        )
        pose_backward.after_pose_func = partial(self.append_next_pose, pose_backward)
        self.translation_poses.append(pose_backward)

        # Pose 2: Return to start with FORWARD_ONLY
        # Robot will go forward directly (no initial rotation needed)
        pose_forward = Pose(
            x=self.start_x,
            y=self.start_y,
            O=self.start_angle,
            max_speed_linear=self.linear_speed,
            max_speed_angular=self.angular_speed,
            motion_direction=MotionDirection.FORWARD_ONLY,
        )
        pose_forward.after_pose_func = partial(self.append_next_pose, pose_forward)
        self.translation_poses.append(pose_forward)

    async def init_action(self):
        """Initialize robot position and start translation loop."""
        # Set robot start position - this updates shared memory and firmware
        pose_init = models.Pose(
            x=self.start_x,
            y=self.start_y,
            O=self.start_angle,
        )
        await self.planner.set_pose_start(pose_init)

        self.planner.pose_reached = False
        self.planner.action = self

        # Start with first pose (backward-only to target)
        self.poses.append(self.translation_poses[0])

    async def append_next_pose(self, current_pose: Pose) -> None:
        """Append the next translation pose in the alternating sequence."""
        # Find current pose in the list and get next one
        current_index = self.translation_poses.index(current_pose)
        next_index = (current_index + 1) % len(self.translation_poses)
        self.poses.append(self.translation_poses[next_index])

    def weight(self) -> float:
        """Return action weight for priority."""
        return 1000000.0


class TestTranslationStrategy(Strategy):
    """Strategy to execute the translation test action."""

    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(TestTranslationAction(planner, self))
