"""Action to move in a rectangle pattern with various motion directions.

Tests all three controller chains in a loop:
- ADAPTIVE_PURE_PURSUIT: BACKWARD_ONLY for all segments
- QUADPID_FEEDFORWARD: BACKWARD_ONLY, FORWARD_ONLY, BIDIRECTIONAL
- QUADPID: BACKWARD_ONLY, FORWARD_ONLY, BIDIRECTIONAL

Adapts to table type:
- Training table: small rectangle in lower-right quadrant
- Game table: large rectangle with one point in each quarter (avoiding fixed obstacles)
"""

import logging
from typing import TYPE_CHECKING

from cogip.models import models
from cogip.models.models import MotionDirection
from cogip.tools.copilot.controller import ControllerEnum
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.table import TableEnum

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner

logger = logging.getLogger(__name__)


class TestRectangleAlternatingAction(Action):
    """
    Action to move the robot in a rectangle pattern with various motion directions.

    This demonstrates the new path API (path_reset, path_add_point, path_start)
    which sends all waypoints at once to the firmware.

    Tests controller chains in a loop:
    - ADAPTIVE_PURE_PURSUIT: BACKWARD_ONLY for all segments
    - QUADPID_FEEDFORWARD: BACKWARD, FORWARD, BIDIRECTIONAL, BIDIRECTIONAL
    - QUADPID: BACKWARD, FORWARD, BIDIRECTIONAL, BIDIRECTIONAL

    Table adaptation:
    - Training table (x=[-1000, 0], y=[-1500, 0]): small 500x500 rectangle
    - Game table (x=[-1000, 1000], y=[-1500, 1500]): large rectangle spanning all 4 quarters
    """

    # Controller chains to test in order
    CONTROLLERS = [
        ControllerEnum.QUADPID_FEEDFORWARD,
        ControllerEnum.QUADPID,
        ControllerEnum.ADAPTIVE_PURE_PURSUIT,
    ]

    def __init__(self, planner: "Planner", strategy: Strategy):
        super().__init__("TestRectangleAlternating", planner, strategy)

        self.angle = 0
        self.linear_speed = 50
        self.angular_speed = 50

        self.before_action_func = self.init_and_start_path
        self.after_action_func = self.switch_to_next_controller

        # Current controller index
        self.controller_index = 0

    def get_corners_for_table(self) -> list[tuple[float, float]]:
        """Get rectangle corners based on current table type.

        Returns:
            List of (x, y) tuples for the 4 corners, starting from bottom-left going clockwise.
        """
        if self.planner.shared_properties.table == TableEnum.Training:
            # Training table: small rectangle in lower-right quadrant
            # Table bounds: x=[-1000, 0], y=[-1500, 0]
            return [
                (-800, -1200),  # Bottom-left (start)
                (-300, -1200),  # Bottom-right
                (-300, -700),  # Top-right
                (-800, -700),  # Top-left
            ]
        else:
            # Game table: one point in each quarter, avoiding fixed obstacles
            # Scene at x=825 spans x=[600, 1050], need 350mm margin → x <= 250
            # Table bounds: x=[-1000, 1000], y=[-1500, 1500]
            return [
                (-500, -750),  # Q3: Bottom-left (start)
                (250, -750),  # Q4: Bottom-right (350mm margin from Scene)
                (250, 750),  # Q1: Top-right (350mm margin from OpponentScene)
                (-500, 750),  # Q2: Top-left (clear area)
            ]

    def get_corners_for_controller(self, controller: ControllerEnum):
        """Get corner waypoints with motion directions based on controller type."""
        corners = self.get_corners_for_table()

        if controller == ControllerEnum.ADAPTIVE_PURE_PURSUIT:
            # ADAPTIVE_PURE_PURSUIT: BACKWARD_ONLY for all segments
            return [
                (corners[1][0], corners[1][1], self.angle, MotionDirection.BACKWARD_ONLY),
                (corners[2][0], corners[2][1], self.angle, MotionDirection.BACKWARD_ONLY),
                (corners[3][0], corners[3][1], self.angle, MotionDirection.BACKWARD_ONLY),
                (corners[0][0], corners[0][1], self.angle, MotionDirection.BACKWARD_ONLY),
            ]
        else:
            # QUADPID and QUADPID_FEEDFORWARD: test all three motion directions
            return [
                # Corner 1: BACKWARD_ONLY
                (corners[1][0], corners[1][1], self.angle, MotionDirection.BACKWARD_ONLY),
                # Corner 2: FORWARD_ONLY
                (corners[2][0], corners[2][1], self.angle, MotionDirection.FORWARD_ONLY),
                # Corner 3: BIDIRECTIONAL
                (corners[3][0], corners[3][1], self.angle, MotionDirection.BIDIRECTIONAL),
                # Corner 4: BIDIRECTIONAL
                (corners[0][0], corners[0][1], self.angle, MotionDirection.BIDIRECTIONAL),
            ]

    async def init_and_start_path(self):
        """Initialize robot at starting position and send all waypoints using new path API."""
        # Get current controller
        current_controller = self.CONTROLLERS[self.controller_index]
        table_name = TableEnum(self.planner.shared_properties.table).name
        ctrl_num = self.controller_index + 1
        ctrl_total = len(self.CONTROLLERS)
        logger.info(f"=== Testing {current_controller.name} on {table_name} ({ctrl_num}/{ctrl_total}) ===")

        # Set the controller
        await self.planner.set_controller(current_controller, force=True)

        # Get corners for current table and set start position (first corner)
        corners = self.get_corners_for_table()
        start_x, start_y = corners[0]

        # Set start position
        pose_init = models.Pose(
            x=start_x,
            y=start_y,
            O=self.angle,
        )
        await self.planner.set_pose_start(pose_init)

        # Reset path on firmware
        await self.planner.path_reset()

        # Get corners with motion directions based on controller
        corners = self.get_corners_for_controller(current_controller)

        # Add all waypoints to the path
        # All points except the last one are intermediate
        num_corners = len(corners)
        for i, (x, y, angle, direction) in enumerate(corners):
            is_last = i == num_corners - 1
            is_intermediate = not is_last
            path_pose = models.PathPose(
                x=x,
                y=y,
                O=angle,
                max_speed_ratio_linear=self.linear_speed,
                max_speed_ratio_angular=self.angular_speed,
                motion_direction=direction,
                is_intermediate=is_intermediate,
                bypass_final_orientation=is_intermediate,  # Skip orientation for intermediate points
            )
            await self.planner.path_add_point(path_pose)

        # Start path execution
        await self.planner.path_start()

        # Restore action state after set_pose_start() cleared it
        self.planner.pose_reached = False
        self.planner.action = self

    async def switch_to_next_controller(self):
        """Switch to the next controller and restart the rectangle."""
        current_controller = self.CONTROLLERS[self.controller_index]
        logger.info(f"=== Finished rectangle with {current_controller.name} ===")

        # Move to next controller (loop back to first if at end)
        self.controller_index = (self.controller_index + 1) % len(self.CONTROLLERS)

        # Re-add this action to continue the loop
        self.strategy.append(self)

    def weight(self) -> float:
        """Return action weight for priority."""
        return 1000000.0


class TestRectangleAlternatingStrategy(Strategy):
    """Strategy to execute the rectangle alternating action with all controller chains."""

    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(TestRectangleAlternatingAction(planner, self))
