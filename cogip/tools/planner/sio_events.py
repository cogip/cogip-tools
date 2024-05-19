import asyncio
from typing import TYPE_CHECKING, Any

import polling2
import socketio
from pydantic import TypeAdapter, ValidationError

from cogip import models
from cogip.models.actuators import ActuatorState
from . import context, logger
from .menu import (
    cameras_menu,
    menu,
    pami_actuators_menu,
    robot_actuators_menu,
    wizard_test_menu,
)

if TYPE_CHECKING:
    from .planner import Planner


class SioEvents(socketio.AsyncClientNamespace):
    """
    Handle all SocketIO events received by Planner.
    """

    def __init__(self, planner: "Planner"):
        super().__init__("/planner")
        self.planner = planner
        self.game_context = context.GameContext()

    async def on_connect(self):
        """
        On connection to cogip-server.
        """
        await asyncio.to_thread(
            polling2.poll,
            lambda: self.client.connected is True,
            step=0.2,
            poll_forever=True,
        )
        logger.info("Connected to cogip-server")
        await self.emit("connected")
        await self.emit("register_menu", {"name": "planner", "menu": menu.model_dump()})
        await self.emit("register_menu", {"name": "wizard", "menu": wizard_test_menu.model_dump()})
        if self.planner.robot_id == 1:
            await self.emit("register_menu", {"name": "actuators", "menu": robot_actuators_menu.model_dump()})
        else:
            await self.emit("register_menu", {"name": "actuators", "menu": pami_actuators_menu.model_dump()})
        await self.emit("register_menu", {"name": "cameras", "menu": cameras_menu.model_dump()})

    async def on_disconnect(self):
        """
        On disconnection from cogip-server.
        """
        await self.planner.stop()
        logger.info("Disconnected from cogip-server")

    async def on_connect_error(self, data: dict[str, Any]):
        """
        On connection error, check if a Planner is already connected and exit,
        or retry connection.
        """
        if (
            data
            and isinstance(data, dict)
            and (message := data.get("message"))
            and message == "A planner is already connected"
        ):
            logger.error(f"Connection to cogip-server failed: {message}")
            self.planner.retry_connection = False
            return
        else:
            logger.error(f"Connection to cogip-server failed: {data = }")

    async def on_copilot_connected(self):
        """
        Copilot connected, start planner.
        """
        await self.planner.start()

    async def on_copilot_disconnected(self):
        """
        Copilot disconnected, stop planner.
        """
        await self.planner.stop()

    def on_starter_changed(self, pushed: bool):
        """
        Signal received from the Monitor when the starter state changes in emulation mode.
        """
        if not self.planner.virtual:
            return
        if pushed:
            self.planner.starter.pin.drive_low()
        else:
            self.planner.starter.pin.drive_high()

    async def on_reset(self):
        """
        Callback on reset message from copilot.
        """
        await self.planner.reset()

    async def on_pose_current(self, pose: dict[str, Any]):
        """
        Callback on pose current message.
        """
        self.planner.set_pose_current(models.Pose.model_validate(pose))

    async def on_pose_reached(self):
        """
        Callback on pose reached message.
        """
        await self.planner.sio_receiver_queue.put(self.planner.set_pose_reached())

    async def on_command(self, cmd: str):
        """
        Callback on command message from dashboard.
        """
        await self.planner.command(cmd)

    async def on_config_updated(self, config: dict[str, Any]):
        """
        Callback on config update from dashboard.
        """
        self.planner.update_config(config)

    async def on_obstacles(self, obstacles: dict[str, Any]):
        """
        Callback on obstacles message.
        """
        self.planner.set_obstacles(TypeAdapter(list[models.Vertex]).validate_python(obstacles))

    async def on_wizard(self, message: dict[str, Any]):
        """
        Callback on wizard message.
        """
        await self.planner.wizard_response(message)

    async def on_game_end(self):
        """
        Callback on game end message.
        """
        await self.planner.game_end()

    async def on_actuator_state(self, actuator_state: dict[str, Any]):
        """
        Callback on actuator_state message.
        """
        try:
            state = TypeAdapter(ActuatorState).validate_python(actuator_state)
        except ValidationError as exc:
            logger.warning(f"Failed to decode ActuatorState: {exc}")
            return

        await self.planner.update_actuator_state(state)
