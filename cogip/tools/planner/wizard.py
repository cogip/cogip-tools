import re
from typing import TYPE_CHECKING, Any

from cogip.tools.planner.positions import StartPosition
from cogip.tools.planner.table import TableEnum
from cogip.utils.asyncloop import AsyncLoop
from .actions import Strategy
from .camp import Camp
from .context import GameContext

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner


class GameWizard:
    def __init__(self, planner: "Planner"):
        self.planner = planner
        self.game_context = GameContext()
        self.step = 0
        self.game_strategy = self.planner.properties.strategy
        self.waiting_starter_pressed_loop = AsyncLoop(
            "Waiting starter pressed thread",
            0.1,
            self.check_starter_pressed,
            logger=True,
        )
        self.waiting_calibration_loop = AsyncLoop(
            "Waiting calibration thread",
            0.1,
            self.check_calibration,
            logger=True,
        )
        self.waiting_start_loop = AsyncLoop(
            "Waiting start thread",
            0.1,
            self.check_start,
            logger=True,
        )

        self.steps = [
            (self.request_table, self.response_table),
            (self.request_camp, self.response_camp),
            (self.request_start_pose, self.response_start_pose),
            (self.request_strategy, self.response_strategy),
            (self.request_starter_for_calibration, self.response_starter_for_calibration),
            (self.request_wait_for_calibration, self.response_wait_for_calibration),
            (self.request_starter_for_game, self.response_starter_for_game),
            (self.request_wait_for_game, self.response_wait_for_game),
        ]

    async def start(self):
        self.step = 0
        self.game_strategy = self.planner.properties.strategy
        await self.waiting_starter_pressed_loop.stop()
        await self.waiting_calibration_loop.stop()
        await self.waiting_start_loop.stop()
        await self.planner.sio_ns.emit("game_reset")
        await self.planner.sio_ns.emit("pami_reset")
        await self.next()

    async def next(self):
        self.step += 1
        if self.step <= len(self.steps):
            step_request, _ = self.steps[self.step - 1]
            await step_request()

    async def response(self, message: dict[str, Any]):
        _, step_response = self.steps[self.step - 1]
        await step_response(message)
        await self.next()

    async def request_table(self):
        message = {
            "name": "Game Wizard: Choose Table",
            "type": "choice_str",
            "choices": [e.name for e in TableEnum],
            "value": self.planner.properties.table.name,
        }
        await self.planner.sio_ns.emit("wizard", message)

    async def response_table(self, message: dict[str, Any]):
        value = message["value"]
        new_table = TableEnum[value]
        self.properties.table = new_table
        self.planner.shared_properties["table"] = new_table
        await self.planner.soft_reset()
        await self.planner.sio_ns.emit("pami_table", value)

    async def request_camp(self):
        message = {
            "name": "Game Wizard: Choose Camp",
            "type": "camp",
            "value": self.game_context.camp.color.name,
        }
        await self.planner.sio_ns.emit("wizard", message)

    async def response_camp(self, message: dict[str, Any]):
        value = message["value"]
        self.game_context.camp.color = Camp.Colors[value]
        await self.planner.soft_reset()
        await self.planner.sio_ns.emit("pami_camp", value)

    async def request_start_pose(self):
        available_start_poses = self.game_context.get_available_start_poses()
        message = {
            "name": "Game Wizard: Choose Start Position",
            "type": "choice_integer",
            "choices": [start_pose.name for start_pose in available_start_poses],
            "value": self.planner.start_position.name,
        }
        await self.planner.sio_ns.emit("wizard", message)

    async def response_start_pose(self, message: dict[str, Any]):
        value = message["value"]
        start_position = StartPosition[value]
        self.planner.start_position = start_position
        await self.planner.set_pose_start(self.game_context.get_start_pose(start_position).pose)

    async def request_strategy(self):
        choices: list[tuple[str, str, str]] = []  # list of (value, category, name). Name can be used for display.
        for strategy in Strategy:
            split = re.findall(r"[A-Z][a-z]*|[a-z]+|[0-9]+", strategy.name)
            choices.append((strategy.name, split[0], " ".join(split)))
        message = {
            "name": "Game Wizard: Choose Strategy",
            "type": "choice_str",
            "choices": choices,
            "value": self.planner.properties.strategy.name,
        }
        await self.planner.sio_ns.emit("wizard", message)

    async def response_strategy(self, message: dict[str, Any]):
        value = message["value"]
        self.game_strategy = Strategy[value]
        self.planner.properties.strategy = Strategy.TestAlign
        await self.planner.soft_reset()

    async def request_starter_for_calibration(self):
        if self.planner.starter.is_pressed:
            self.waiting_calibration_loop.start()
            await self.next()
            return

        message = {
            "name": "Game Wizard: Calibration - Starter Check",
            "type": "message",
            "value": "Please insert starter in Robot",
        }
        await self.planner.sio_ns.emit("wizard", message)

        self.check_starter_pressed = False
        self.waiting_starter_pressed_loop.start()

    async def response_starter_for_calibration(self, message: dict[str, Any]):
        if not self.planner.starter.is_pressed:
            self.step -= 1

    async def request_wait_for_calibration(self):
        self.waiting_calibration_loop.start()

        message = {
            "name": "Game Wizard: Calibration - Waiting Start",
            "type": "message",
            "value": "Remove starter to start calibration",
        }
        await self.planner.sio_ns.emit("wizard", message)

    async def response_wait_for_calibration(self, message: dict[str, Any]):
        self.step -= 1

    async def request_starter_for_game(self):
        if self.planner.starter.is_pressed:
            self.waiting_start_loop.start()
            await self.next()
            return

        message = {
            "name": "Game Wizard: Game - Starter Check",
            "type": "message",
            "value": "Please insert starter in Robot",
        }
        await self.planner.sio_ns.emit("wizard", message)

        self.waiting_starter_pressed_loop.start()

    async def response_starter_for_game(self, message: dict[str, Any]):
        if not self.planner.starter.is_pressed:
            self.step -= 1

    async def request_wait_for_game(self):
        message = {
            "name": "Game Wizard: Waiting Start",
            "type": "message",
            "value": "Remove starter to start the game",
        }
        await self.planner.sio_ns.emit("wizard", message)
        self.waiting_start_loop.start()

    async def response_wait_for_game(self, message: dict[str, Any]):
        self.step -= 1

    async def check_starter_pressed(self):
        if not self.planner.starter.is_pressed:
            return

        self.waiting_starter_pressed_loop.exit = True
        await self.waiting_starter_pressed_loop.stop()
        await self.planner.sio_ns.emit("close_wizard")
        await self.next()

    async def check_calibration(self):
        if self.planner.starter.is_pressed:
            return

        self.waiting_calibration_loop.exit = True
        await self.waiting_calibration_loop.stop()
        await self.planner.sio_ns.emit("close_wizard")
        self.game_context.playing = True
        await self.planner.sio_receiver_queue.put(self.planner.set_pose_reached())
        await self.next()

    async def check_start(self):
        if self.planner.starter.is_pressed:
            return

        self.waiting_start_loop.exit = True
        await self.waiting_start_loop.stop()
        await self.planner.sio_ns.emit("close_wizard")
        self.planner.properties.strategy = self.game_strategy
        self.game_context.playing = False
        await self.planner.soft_reset()
        await self.planner.sio_ns.emit("game_start")
        await self.planner.sio_ns.emit("pami_play")
        await self.planner.cmd_play()
