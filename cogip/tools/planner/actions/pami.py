import asyncio
from typing import TYPE_CHECKING

from cogip.models.artifacts import PotSupplyID
from cogip.tools.planner import actuators
from cogip.tools.planner.actions.actions import Action, Actions
from cogip.tools.planner.pose import AdaptedPose, Pose
from cogip.tools.planner.table import TableEnum

if TYPE_CHECKING:
    from ..planner import Planner


class Pami2Action(Action):
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("PAMI2 action", planner, actions)
        self.before_action_func = self.before_action

    async def before_action(self):
        self.start_pose = self.planner.pose_current.model_copy()
        self.game_context.fixed_obstacles.pop()

        pose = Pose(
            x=450 / 2,
            y=self.start_pose.y,
            O=180,
            max_speed_linear=66,
            max_speed_angular=66,
            allow_reverse=False,
        )
        self.poses.append(pose)

        # Opposite dropoff
        pose = AdaptedPose(
            x=450 / 2,
            y=1500 - 450,
            O=90,
            max_speed_linear=66,
            max_speed_angular=66,
            allow_reverse=False,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose,
        )
        self.poses.append(pose)

        if self.game_context._table == TableEnum.Training:
            pose.x -= 1000

        for _, plant_supply in self.game_context.plant_supplies.items():
            plant_supply.enabled = False
        for _, pot_supply in self.game_context.pot_supplies.items():
            pot_supply.enabled = False

        await asyncio.sleep(90)

    async def after_pose(self):
        self.actions.clear()

    def weight(self) -> float:
        return 1000000.0


class Pami3Action(Action):
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("PAMI3 action", planner, actions)
        self.before_action_func = self.before_action

    async def before_action(self):
        self.start_pose = self.planner.pose_current.model_copy()

        # Top planter
        pose = AdaptedPose(
            x=1000 - 150 + self.game_context.properties.robot_width / 2,
            y=-1500 + 600 + 325 / 2,
            O=-90,
            max_speed_linear=66,
            max_speed_angular=66,
            allow_reverse=False,
            bypass_final_orientation=True,
            timeout_ms=7000,
            after_pose_func=self.after_pose,
        )
        self.poses.append(pose)

        if self.game_context._table == TableEnum.Training:
            pose.x -= 1000

        for _, plant_supply in self.game_context.plant_supplies.items():
            plant_supply.enabled = False
        for _, pot_supply in self.game_context.pot_supplies.items():
            pot_supply.enabled = False

        await asyncio.sleep(93)

    async def after_pose(self):
        await actuators.pami_arm_open(self.planner)
        self.actions.clear()

    def weight(self) -> float:
        return 1000000.0


class Pami4Action(Action):
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("PAMI4 action", planner, actions)
        self.before_action_func = self.before_action

    async def before_action(self):
        self.start_pose = self.planner.pose_current.model_copy()

        # Top dropoff
        pose = AdaptedPose(
            x=850,
            y=-1040,
            O=-90,
            max_speed_linear=66,
            max_speed_angular=66,
            allow_reverse=False,
            bypass_final_orientation=True,
            timeout_ms=7000,
            after_pose_func=self.after_pose,
        )
        self.poses.append(pose)

        if self.game_context._table == TableEnum.Training:
            pose.x -= 1000
            self.game_context.pot_supplies[PotSupplyID.LocalMiddle].enabled = False
        else:
            self.game_context.pot_supplies[PotSupplyID.LocalTop].enabled = False

        for _, plant_supply in self.game_context.plant_supplies.items():
            plant_supply.enabled = False
        for _, pot_supply in self.game_context.pot_supplies.items():
            pot_supply.enabled = False

        await asyncio.sleep(92)

    async def after_pose(self):
        self.actions.clear()

    def weight(self) -> float:
        return 1000000.0


class Pami2Actions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami2Action(planner, self))


class Pami3Actions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami3Action(planner, self))


class Pami4Actions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami4Action(planner, self))
