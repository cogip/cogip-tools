from typing import Any

import socketio

from cogip import models
from .. import logger, server
from ..context import Context
from ..recorder import GameRecorder


class CopilotNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to copilot.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/copilot")
        self.cogip_server = cogip_server
        self.context = Context()
        self.recorder = GameRecorder()
        self.context.copilot_sid = None

    async def on_connect(self, sid, environ):
        if self.context.copilot_sid:
            message = "A copilot is already connected"
            logger.error(f"Copilot connection refused: {message}")
            raise ConnectionRefusedError(message)
        self.context.copilot_sid = sid

    async def on_connected(self, sid):
        logger.info("Copilot connected.")
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
        await self.emit("reset", namespace="/planner")
        await self.recorder.async_do_rollover()
        self.recorder.recording = True

    async def on_register_menu(self, sid, data: dict[str, Any]):
        """
        Callback on register_menu.
        """
        await self.cogip_server.register_menu("copilot", data)

    async def on_pose_reached(self, sid) -> None:
        """
        Callback on pose reached message.
        """
        await self.emit("pose_reached", namespace="/planner")

    async def on_menu(self, sid, menu):
        """
        Callback on menu event.
        """
        self.context.shell_menu = models.ShellMenu.model_validate(menu)
        await self.emit("shell_menu", (self.context.robot_id, menu), namespace="/dashboard")

    async def on_pose(self, sid, pose):
        """
        Callback on pose event.
        """
        await self.emit("pose_current", (self.context.robot_id, pose), namespace="/dashboard")
        await self.recorder.async_record({"pose_current": pose})

    async def on_state(self, sid, state):
        """
        Callback on state event.
        """
        await self.emit("state", (self.context.robot_id, state), namespace="/dashboard")
        await self.recorder.async_record({"state": state})

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
        await self.emit("game_end", namespace="/planner")
