from typing import Any

import socketio

from cogip import models
from .. import logger, server
from ..context import Context


class CopilotNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to copilot.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/copilot")
        self.cogip_server = cogip_server
        self.context = Context()
        self.context.copilot_sid = None

    async def on_connect(self, sid, environ):
        if self.context.copilot_sid:
            message = "A copilot is already connected"
            logger.error(f"Copilot connection refused: {message}")
            raise ConnectionRefusedError(message)

    async def on_connected(self, sid):
        logger.info("Copilot connected.")
        self.context.copilot_sid = sid
        if self.context.planner_sid:
            await self.emit("copilot_connected", namespace="/planner")

    async def on_disconnect(self, sid):
        self.context.copilot_sid = None
        self.context.shell_menu = None
        await self.emit("copilot_disconnected", namespace="/planner")
        logger.info("Copilot disconnected.")

    async def on_reset(self, sid) -> None:
        """
        Callback on reset event.
        """
        logger.info("[copilot => planner] reset.")
        await self.emit("reset", namespace="/planner")

    async def on_register_menu(self, sid, data: dict[str, Any]):
        """
        Callback on register_menu.
        """
        await self.cogip_server.register_menu("copilot", data)

    async def on_pose_reached(self, sid) -> None:
        """
        Callback on pose reached message.
        """
        logger.info("[copilot => planner] Pose reached.")
        await self.emit("pose_reached", namespace="/planner")

    async def on_intermediate_pose_reached(self, sid) -> None:
        """
        Callback on intermediate pose reached message.
        """
        logger.info("[copilot => planner] Intermediate pose reached.")
        await self.emit("intermediate_pose_reached", namespace="/planner")

    async def on_blocked(self, sid) -> None:
        """
        Callback on blocked message.
        """
        logger.info("[copilot => planner] Blocked.")
        await self.emit("blocked", namespace="/planner")

    async def on_menu(self, sid, menu):
        """
        Callback on menu event.
        """
        self.context.shell_menu = models.ShellMenu.model_validate(menu)
        await self.emit("shell_menu", (self.context.robot_id, menu), namespace="/dashboard")

    async def on_state(self, sid, state):
        """
        Callback on state event.
        """
        await self.emit("state", (self.context.robot_id, state), namespace="/dashboard")

    async def on_actuator_state(self, sid, actuator_state: dict[str, Any]):
        """
        Callback on actuator_state message.
        """
        await self.emit("actuator_state", actuator_state, namespace="/planner")
        await self.emit("actuator_state", actuator_state, namespace="/dashboard")

    async def on_pid(self, sid, pid: dict[str, Any]):
        """
        Callback on pid message.
        """
        await self.emit("pid", pid, namespace="/dashboard")

    async def on_config(self, sid, config: dict[str, Any]):
        """
        Callback on config message.
        """
        await self.emit("config", config, namespace="/dashboard")

    async def on_game_end(self, sid) -> None:
        """
        Callback on game end message.
        """
        logger.info("[copilot => planner] Game end.")
        await self.emit("game_end", namespace="/planner")
