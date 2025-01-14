from typing import TYPE_CHECKING

from cogip.models import artifacts, models
from cogip.tools.planner.actions import base_actions
from cogip.tools.planner.actions.actions import Action, Actions
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner


start_pose = Pose()


class DropInDropoffZoneAction(base_actions.DropInDropoffZoneAction):
    def __init__(self, planner: "Planner", actions: Actions, dropoff_zone_id: artifacts.DropoffZoneID, slot: int):
        super().__init__(planner, actions, dropoff_zone_id, slot)
        if slot == 0:
            self.before_action_func = self.record_start_pose
        if slot == 2:
            self.before_action_func = self.record_start_pose

    def weight(self) -> float:
        if self.slot + 1 == self.dropoff_zone.free_slots:
            return 1000000.0
        return 0

    async def record_start_pose(self):
        global start_pose
        start_pose = models.Pose(
            x=self.planner.pose_current.x,
            y=self.planner.pose_current.y,
            O=self.planner.pose_current.angle,
        )


class ParkingAction(Action):
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("Parking action", planner, actions)
        self.before_action_func = self.before_action

    async def before_action(self):
        global start_pose
        self.poses.append(
            Pose(
                x=start_pose.x,
                y=start_pose.y,
                O=start_pose.O,
                max_speed_linear=66,
                max_speed_angular=66,
                allow_reverse=True,
            )
        )

    def weight(self) -> float:
        return 1


class TestDropoffActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(DropInDropoffZoneAction(planner, self, artifacts.DropoffZoneID.Bottom, 0))
        self.append(DropInDropoffZoneAction(planner, self, artifacts.DropoffZoneID.Bottom, 1))
        self.append(DropInDropoffZoneAction(planner, self, artifacts.DropoffZoneID.Bottom, 2))
        self.append(ParkingAction(planner, self))
