"""Action to move in a rectangle pattern alternating forward and backward motion."""

from functools import partial
from typing import TYPE_CHECKING

from cogip.models import models
from cogip.models.models import MotionDirection
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner


class TestRectangleAlternatingAction(Action):
    """
    Action to move the robot in a rectangle pattern, alternating between
    forward-only and backward-only motion on each side.

    This demonstrates the MotionDirection enum capabilities.
    """


    def __init__(self, planner: "Planner", strategy: Strategy):
        super().__init__("TestRectangleAlternating", planner, strategy)
        # Coordinates fit within training table: x=[-1000, 0], y=[-1500, 0]
        self.start_x = -900
        self.start_y = -1400
        self.width = 800
        self.height = 800
        self.angle = 0
        self.linear_speed = 50
        self.angular_speed = 50

        self.before_action_func = self.init_start_position

        # Define the corners with alternating directions
        self.corners = [
            # Corner 1: move up, go backward
            (self.start_x + self.width, self.start_y, self.angle, MotionDirection.BACKWARD_ONLY),
            # Corner 2: move left, go forward
            (self.start_x + self.width, self.start_y + self.height, self.angle, MotionDirection.FORWARD_ONLY),
            # Corner 3: move down, go backward
            (self.start_x, self.start_y + self.height, self.angle, MotionDirection.BACKWARD_ONLY),
            # Corner 4: move right, go forward
            (self.start_x, self.start_y, self.angle, MotionDirection.FORWARD_ONLY),
            # Diagonal: to opposite corner with bidirectional
            (self.start_x + self.width, self.start_y + self.height, self.angle, MotionDirection.BIDIRECTIONAL),
            # Diagonal: back to start with bidirectional
            (self.start_x, self.start_y, self.angle, MotionDirection.BIDIRECTIONAL),
        ]

        # Create poses for each corner
        for i, (x, y, angle, direction) in enumerate(self.corners):
            pose = Pose(
                x=x,
                y=y,
                O=angle,
                max_speed_linear=self.linear_speed,
                max_speed_angular=self.angular_speed,
                motion_direction=direction,
            )
            # Each pose re-appends itself to create infinite loop
            pose.after_pose_func = partial(self.append_pose, pose)
            self.poses.append(pose)

    async def init_start_position(self):
        """Initialize robot at starting position."""
        pose_init = models.Pose(
            x=self.start_x,
            y=self.start_y,
            O=self.angle,
        )
        await self.planner.set_pose_start(pose_init)
        self.planner.pose_reached = False
        self.planner.action = self

    async def append_pose(self, pose: Pose) -> None:
        """Re-append the pose to continue the loop."""
        self.poses.append(pose)

    def weight(self) -> float:
        """Return action weight for priority."""
        return 1000000.0


class TestRectangleAlternatingStrategy(Strategy):
    """Strategy to execute the rectangle alternating action."""

    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(TestRectangleAlternatingAction(planner, self))
