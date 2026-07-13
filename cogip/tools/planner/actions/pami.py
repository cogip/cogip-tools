import asyncio
from typing import TYPE_CHECKING

from colorzero import Color

from cogip.models.artifacts import Pantry, PantryID
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.actions.utils import set_countdown_color
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.camp import Camp
from cogip.tools.planner.pose import AdaptedPose, Pose
from cogip.tools.planner.table import TableEnum

if TYPE_CHECKING:
    from ..planner import Planner


class Pami3Action(Action):
    """
    Action for PAMI 3.

    Plan:
        - BA: disable pantry
        - B1: wait initial_delay seconds (for PAMI 4, 5 and 6 to move)
        - B1: disable avoidance
        - P1: move to X=same Y=-1425 angle=180
        - A1: restore avoidance
        - B2: wait for pami_event (if wait==True)
        - B2: wait start_delay seconds (probably 0)
        - P2: go to PantryID.LocalSide
        - A2: enable flag motor
    """

    def __init__(self, planner: "Planner", strategy: Strategy, start_delay: int, wait: bool = True):
        super().__init__("PAMI 3 action", planner, strategy, interruptable=False)
        self.wait = wait
        self.before_action_func = self.before_action
        self.start_delay = start_delay
        self.initial_delay = 15
        self.pantry_id = PantryID.LocalSide

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    @property
    def pantry(self) -> Pantry:
        return self.planner.game_context.pantries[self.pantry_id]

    async def before_action(self):
        self.pantry.enabled = False
        if self.planner.shared_properties.table == TableEnum.Training:
            self.planner.game_context.pantries[PantryID.LocalSide].enabled = False

        self.start_pose = self.pose_current.model_copy()

        pose1 = AdaptedPose(
            x=self.start_pose.x,
            y=-1425,
            max_speed_linear=70,
            max_speed_angular=70,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)
        self.logger.info(f"{self.name}: pose1: x={pose1.x: 5.2f} y={pose1.y: 5.2f} O={pose1.O: 3.2f}°")

        pose2 = Pose(
            x=self.pantry.x,
            y=self.pantry.y,
            max_speed_linear=100,
            max_speed_angular=100,
            bypass_final_orientation=True,
            stop_before_distance=170,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        if Camp().color == Camp.Colors.blue:
            pose2.y += 20
        else:
            pose2.y -= 20
        if self.planner.shared_properties.table == TableEnum.Training:
            pose2.x = -880
            pose2.y = -1350
        self.poses.append(pose2)
        self.logger.info(f"{self.name}: pose2: x={pose2.x: 5.2f} y={pose2.y: 5.2f} O={pose2.O: 3.2f}°")

    async def before_pose1(self):
        self.logger.info(f"{self.name}: before_pose1")
        self.set_avoidance(AvoidanceStrategy.Disabled)
        await asyncio.sleep(self.initial_delay)

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

    async def before_pose2(self):
        self.logger.info(f"{self.name}: before_pose2")
        if self.wait:
            await self.planner.pami_event.wait()

        self.planner.led.color = Color("lightblue")
        await set_countdown_color(self.planner, "orange")
        await asyncio.sleep(self.start_delay)
        self.planner.led.color = Color("green")
        await set_countdown_color(self.planner, "green")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")
        self.planner.led.color = Color("red")
        await set_countdown_color(self.planner, "red")
        self.strategy.clear()
        self.planner.flag_motor.on()

    def weight(self) -> float:
        return 9_999_999.0


class Pami4Action(Action):
    """
    Action for PAMI 4.

    Plan:
        - BA: disable pantry
        - B1: wait initial_delay seconds (for PAMI 6 to move)
        - B1: disable avoidance
        - P1: move to X=same Y=-1245 angle=bypass
        - P2: move to X=680 Y=-1245 angle=180
        - A2: restore avoidance
        - B3: wait for pami_event (if wait==True)
        - B3: wait start_delay seconds (probably 0)
        - P3: step out: X=450
        - P4: go to PantryID.LocalBottom
        - A4: enable flag motor
    """

    def __init__(self, planner: "Planner", strategy: Strategy, start_delay: int, wait: bool = True):
        super().__init__("PAMI 4 action", planner, strategy, interruptable=False)
        self.wait = wait
        self.before_action_func = self.before_action
        self.start_delay = start_delay
        self.initial_delay = 5
        self.pantry_id = PantryID.LocalBottom

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    @property
    def pantry(self) -> Pantry:
        return self.planner.game_context.pantries[self.pantry_id]

    async def before_action(self):
        self.pantry.enabled = False
        if self.planner.shared_properties.table == TableEnum.Training:
            self.planner.game_context.pantries[PantryID.LocalSide].enabled = False

        self.start_pose = self.pose_current.model_copy()

        pose1 = AdaptedPose(
            x=self.start_pose.x,
            y=-1245,
            max_speed_linear=70,
            max_speed_angular=70,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)
        self.logger.info(f"{self.name}: pose1: x={pose1.x: 5.2f} y={pose1.y: 5.2f} O={pose1.O: 3.2f}°")

        pose2 = AdaptedPose(
            x=680,
            y=-1245,
            O=180,
            max_speed_linear=70,
            max_speed_angular=70,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            pose2.x -= 1000
        self.poses.append(pose2)
        self.logger.info(f"{self.name}: pose2: x={pose2.x: 5.2f} y={pose2.y: 5.2f} O={pose2.O: 3.2f}°")

        pose3 = AdaptedPose(
            x=450,
            y=-1245,
            max_speed_linear=100,
            max_speed_angular=100,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose3,
            after_pose_func=self.after_pose3,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            pose3.x -= 1000
        self.poses.append(pose3)
        self.logger.info(f"{self.name}: pose3: x={pose3.x: 5.2f} y={pose3.y: 5.2f} O={pose3.O: 3.2f}°")

        pose4 = Pose(
            x=self.pantry.x + 20,
            y=self.pantry.y,
            max_speed_linear=100,
            max_speed_angular=100,
            bypass_final_orientation=True,
            stop_before_distance=170,
            before_pose_func=self.before_pose4,
            after_pose_func=self.after_pose4,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            pose4.x = -880
            pose4.y = -1000
        self.poses.append(pose4)
        self.logger.info(f"{self.name}: pose4: x={pose4.x: 5.2f} y={pose4.y: 5.2f} O={pose4.O: 3.2f}°")

    async def before_pose1(self):
        self.logger.info(f"{self.name}: before_pose1")
        self.set_avoidance(AvoidanceStrategy.Disabled)
        await asyncio.sleep(self.initial_delay)

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")

    async def before_pose2(self):
        self.logger.info(f"{self.name}: before_pose2")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

    async def before_pose3(self):
        self.logger.info(f"{self.name}: before_pose3")
        if self.wait:
            await self.planner.pami_event.wait()

        self.planner.led.color = Color("lightblue")
        await set_countdown_color(self.planner, "orange")
        await asyncio.sleep(self.start_delay)
        self.planner.led.color = Color("green")
        await set_countdown_color(self.planner, "green")

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3")

    async def before_pose4(self):
        self.logger.info(f"{self.name}: before_pose4")

    async def after_pose4(self):
        self.logger.info(f"{self.name}: after_pose4")
        self.planner.led.color = Color("red")
        await set_countdown_color(self.planner, "red")
        self.strategy.clear()
        self.planner.flag_motor.on()

    def weight(self) -> float:
        return 9_999_999.0


class Pami5Action(Action):
    """
    Action for PAMI 5.

    Plan:
        - BA: disable pantry
        - B1: disable avoidance
        - B1: wait initial_delay seconds (for PAMI 4 and 6 to move)
        - P1: move to X=same Y=-1115 angle=bypass
        - P2: move to X=680 Y=-1115 angle=180
        - A2: restore avoidance
        - B3: wait for pami_event (if wait==True)
        - B3: wait start_delay seconds (for PAMI 5 to move)
        - P3: step out: X=450
        - P4: go to PantryID.LocalCenter
        - A4: enable flag motor
    """

    def __init__(self, planner: "Planner", strategy: Strategy, start_delay: int, wait: bool = True):
        super().__init__("PAMI 5 action", planner, strategy, interruptable=False)
        self.wait = wait
        self.before_action_func = self.before_action
        self.start_delay = start_delay
        self.initial_delay = 10
        self.pantry_id = PantryID.LocalCenter

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    @property
    def pantry(self) -> Pantry:
        return self.planner.game_context.pantries[self.pantry_id]

    async def before_action(self):
        self.pantry.enabled = False
        if self.planner.shared_properties.table == TableEnum.Training:
            self.planner.game_context.pantries[PantryID.LocalSide].enabled = False
            self.planner.game_context.pantries[PantryID.LocalBottom].enabled = False

        self.start_pose = self.pose_current.model_copy()

        pose1 = AdaptedPose(
            x=self.start_pose.x,
            y=-1115,
            max_speed_linear=70,
            max_speed_angular=70,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)
        self.logger.info(f"{self.name}: pose1: x={pose1.x: 5.2f} y={pose1.y: 5.2f} O={pose1.O: 3.2f}°")

        pose2 = AdaptedPose(
            x=680,
            y=-1115,
            O=180,
            max_speed_linear=70,
            max_speed_angular=70,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            pose2.x -= 1000
        self.poses.append(pose2)
        self.logger.info(f"{self.name}: pose2: x={pose2.x: 5.2f} y={pose2.y: 5.2f} O={pose2.O: 3.2f}°")

        pose3 = AdaptedPose(
            x=450,
            y=-1115,
            max_speed_linear=100,
            max_speed_angular=100,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose3,
            after_pose_func=self.after_pose3,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            pose3.x -= 1000
        self.poses.append(pose3)
        self.logger.info(f"{self.name}: pose3: x={pose3.x: 5.2f} y={pose3.y: 5.2f} O={pose3.O: 3.2f}°")

        pose4 = Pose(
            x=self.pantry.x,
            y=self.pantry.y,
            max_speed_linear=100,
            max_speed_angular=100,
            bypass_final_orientation=True,
            stop_before_distance=170,
            before_pose_func=self.before_pose4,
            after_pose_func=self.after_pose4,
        )
        if Camp().color == Camp.Colors.blue:
            pose4.y += 20
        else:
            pose4.y -= 20
        if self.planner.shared_properties.table == TableEnum.Training:
            pose4.x = -880
            pose4.y = -625
        self.poses.append(pose4)
        self.logger.info(f"{self.name}: pose4: x={pose4.x: 5.2f} y={pose4.y: 5.2f} O={pose4.O: 3.2f}°")

    async def before_pose1(self):
        self.logger.info(f"{self.name}: before_pose1")
        self.set_avoidance(AvoidanceStrategy.Disabled)

        await asyncio.sleep(self.initial_delay)

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")

    async def before_pose2(self):
        self.logger.info(f"{self.name}: before_pose2")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

    async def before_pose3(self):
        self.logger.info(f"{self.name}: before_pose3")
        if self.wait:
            await self.planner.pami_event.wait()

        self.planner.led.color = Color("lightblue")
        await set_countdown_color(self.planner, "orange")
        await asyncio.sleep(self.start_delay)
        self.planner.led.color = Color("green")
        await set_countdown_color(self.planner, "green")

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3")

    async def before_pose4(self):
        self.logger.info(f"{self.name}: before_pose4")

    async def after_pose4(self):
        self.logger.info(f"{self.name}: after_pose4")
        self.planner.led.color = Color("red")
        await set_countdown_color(self.planner, "red")
        self.strategy.clear()
        self.planner.flag_motor.on()

    def weight(self) -> float:
        return 9_999_999.0


class Pami6Action(Action):
    """
    Action for PAMI 6.

    Plan:
        - BA: disable pantry
        - B1: disable avoidance
        - B1: wait initial_delay seconds (probably 0)
        - P1: move to X=same Y=-1135 angle=bypass
        - P2: move to X=680 Y=-985 angle=180
        - A2: restore avoidance
        - B3: wait for pami_event (if wait==True)
        - B3: wait start_delay seconds (wait for PAMI 4 and 5 to move)
        - P3: step out: X=450 Y=-985 angle=bypass
        - P4: go to PantryID.MiddleCenter
        - A4: enable flag motor
    """

    def __init__(self, planner: "Planner", strategy: Strategy, start_delay: int, wait: bool = True):
        super().__init__("PAMI 6 action", planner, strategy, interruptable=False)
        self.wait = wait
        self.before_action_func = self.before_action
        self.start_delay = start_delay
        self.initial_delay = 0
        self.pantry_id = PantryID.MiddleCenter

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    @property
    def pantry(self) -> Pantry:
        return self.planner.game_context.pantries[self.pantry_id]

    async def before_action(self):
        self.pantry.enabled = False
        if self.planner.shared_properties.table == TableEnum.Training:
            self.planner.game_context.pantries[PantryID.LocalSide].enabled = False

        self.start_pose = self.pose_current.model_copy()

        pose1 = AdaptedPose(
            x=self.start_pose.x,
            y=-1065,
            max_speed_linear=70,
            max_speed_angular=70,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)
        self.logger.info(f"{self.name}: pose1: x={pose1.x: 5.2f} y={pose1.y: 5.2f} O={pose1.O: 3.2f}°")

        pose2 = AdaptedPose(
            x=680,
            y=-985,
            O=180,
            max_speed_linear=70,
            max_speed_angular=70,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            pose2.x -= 1000
        self.poses.append(pose2)
        self.logger.info(f"{self.name}: pose2: x={pose2.x: 5.2f} y={pose2.y: 5.2f} O={pose2.O: 3.2f}°")

        pose3 = AdaptedPose(
            x=450,
            y=-985,
            max_speed_linear=100,
            max_speed_angular=100,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose3,
            after_pose_func=self.after_pose3,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            pose3.x -= 1000
        self.poses.append(pose3)
        self.logger.info(f"{self.name}: pose3: x={pose3.x: 5.2f} y={pose3.y: 5.2f} O={pose3.O: 3.2f}°")

        pose4 = AdaptedPose(
            x=self.pantry.x,
            y=self.pantry.y,
            max_speed_linear=100,
            max_speed_angular=100,
            bypass_final_orientation=True,
            stop_before_distance=170,
            before_pose_func=self.before_pose4,
            after_pose_func=self.after_pose4,
        )
        if self.planner.shared_properties.table == TableEnum.Training:
            pose4.x = -880
            pose4.y = -200

        self.poses.append(pose4)
        self.logger.info(f"{self.name}: pose4: x={pose4.x: 5.2f} y={pose4.y: 5.2f} O={pose4.O: 3.2f}°")

    async def before_pose1(self):
        self.logger.info(f"{self.name}: before_pose1")
        self.set_avoidance(AvoidanceStrategy.Disabled)
        await asyncio.sleep(self.initial_delay)

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")

    async def before_pose2(self):
        self.logger.info(f"{self.name}: before_pose2")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")

    async def before_pose3(self):
        self.logger.info(f"{self.name}: before_pose3")
        if self.wait:
            await self.planner.pami_event.wait()

        self.planner.led.color = Color("lightblue")
        await set_countdown_color(self.planner, "orange")
        await asyncio.sleep(self.start_delay)
        self.planner.led.color = Color("green")
        await set_countdown_color(self.planner, "green")

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3")
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

    async def before_pose4(self):
        self.logger.info(f"{self.name}: before_pose4")

    async def after_pose4(self):
        self.logger.info(f"{self.name}: after_pose4")
        self.planner.led.color = Color("red")
        await set_countdown_color(self.planner, "red")
        self.strategy.clear()
        self.planner.flag_motor.on()

    def weight(self) -> float:
        return 9_999_999.0


class Pami3Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami3Action(planner, self, start_delay=5))


class Pami4Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami4Action(planner, self, start_delay=0))


class Pami5Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami5Action(planner, self, start_delay=5))


class Pami6Strategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(Pami6Action(planner, self, start_delay=0))


# Standalone strategies


class Pami3StandaloneStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        action = Pami3Action(planner, self, start_delay=0, wait=False)
        action.initial_delay = 0
        self.append(action)


class Pami4StandaloneStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        action = Pami4Action(planner, self, start_delay=0, wait=False)
        action.initial_delay = 0
        self.append(action)


class Pami5StandaloneStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        action = Pami5Action(planner, self, start_delay=0, wait=False)
        action.initial_delay = 0
        self.append(action)


class Pami6StandaloneStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        action = Pami6Action(planner, self, start_delay=0, wait=False)
        action.initial_delay = 0
        self.append(action)
