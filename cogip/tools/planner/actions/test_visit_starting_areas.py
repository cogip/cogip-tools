from functools import partial
from typing import TYPE_CHECKING

from cogip.tools.planner.actions.actions import Action, Actions
from cogip.tools.planner.pose import Pose
from cogip.tools.planner.start_positions import StartPositionEnum

if TYPE_CHECKING:
    from ..planner import Planner


class VisitStartingAreasAction(Action):
    """
    Action that goes from the starting position to the next one.
    """

    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("VisitStartingAreas action", planner, actions)
        self.before_action_func = self.compute_poses

    async def compute_poses(self) -> None:
        start_positions = [p.name for p in StartPositionEnum if self.planner.start_positions.is_valid(p)]
        start_positions_count = len(start_positions)
        default_start_position_index = 0
        for i in range(start_positions_count):
            start_position = StartPositionEnum((i + 1) % start_positions_count + 1)
            if start_position == self.planner.shared_properties.start_position:
                default_start_position_index = i
            pose = self.planner.start_positions.get(start_position)
            new_pose = Pose(x=pose.x, y=pose.y, O=pose.O, max_speed_linear=66, max_speed_angular=66)
            new_pose.after_pose_func = partial(self.append_pose, new_pose)
            self.poses.append(new_pose)

        self.poses = self.poses[default_start_position_index:] + self.poses[:default_start_position_index]
        default_start_position = self.poses.pop(0)
        self.poses.append(default_start_position)

    async def append_pose(self, pose: Pose) -> None:
        self.poses.append(pose)

    def weight(self) -> float:
        return 1000000.0


class TestVisitStartingAreasActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(VisitStartingAreasAction(planner, self))
