from typing import TYPE_CHECKING

from cogip.models.artifacts import TribuneID
from cogip.tools.planner import actuators
from cogip.tools.planner.actions import base_actions
from cogip.tools.planner.actions.actions import Actions
from cogip.tools.planner.pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner


class GrabTribuneAction(base_actions.GrabTribuneAction):
    def weight(self) -> float:
        return 1000000.0

    async def after_pose3(self):
        await super().after_pose3()
        self.poses.append(
            Pose(
                x=self.start_pose.x,
                y=self.start_pose.y,
                O=self.start_pose.O,
                max_speed_linear=50,
                max_speed_angular=20,
                allow_reverse=False,
                after_pose_func=self.after_pose4,
            )
        )

    async def after_pose4(self):
        await actuators.cart_magnet_off(self.planner)
        await actuators.cart_in(self.planner)


class TestGrabTribuneActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(GrabTribuneAction(planner, self, TribuneID.LocalBottom))
