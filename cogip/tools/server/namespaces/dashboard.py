from typing import Any

import socketio

from .. import logger, server
from ..context import Context


class DashboardNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to dashboards.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/dashboard")
        self.cogip_server = cogip_server
        self.context = Context()

    async def on_connect(self, sid, environ):
        pass

    async def on_connected(self, sid):
        logger.info("Dashboard connected.")
        await self.emit("tool_menu", self.context.tool_menus[self.context.current_tool_menu].model_dump(), to=sid)

        if self.context.shell_menu:
            await self.emit("shell_menu", (self.context.robot_id, self.context.shell_menu.model_dump()), to=sid)

        if self.context.virtual_planner:
            await self.emit("virtual", (self.context.robot_id, self.context.virtual), to=sid)

    def on_disconnect(self, sid):
        logger.info("Dashboard disconnected.")

    async def on_tool_cmd(self, sid, cmd: str) -> None:
        """
        Callback on tool command message from dashboard.
        """
        # Find entry in current menu
        entry = None
        for entry in self.context.tool_menus[self.context.current_tool_menu].entries:
            if entry.cmd == cmd:
                break

        # Check if it corresponds to a menu or a command
        if entry and entry.cmd in self.context.tool_menus:
            # Enter a menu
            self.context.current_tool_menu = cmd
            await self.emit(
                "tool_menu",
                self.context.tool_menus[self.context.current_tool_menu].model_dump(),
                namespace="/dashboard",
            )
        else:
            # Forward command to corresponding namespace
            if cmd == "exit":
                self.context.current_tool_menu = "root"
                await self.emit(
                    "tool_menu",
                    self.context.tool_menus[self.context.current_tool_menu].model_dump(),
                    namespace="/dashboard",
                )
            else:
                split_ns = self.context.current_tool_menu.split("/")
                namespace = split_ns.pop(0)
                await self.emit("command", cmd, namespace=f"/{namespace}")

    async def on_shell_cmd(self, sid, cmd: str) -> None:
        """
        Callback on shell command message from dashboard.
        """
        await self.emit("shell_command", cmd, namespace="/copilot")

    async def on_config_updated(self, sid, config: dict[str, Any]) -> None:
        namespace = config.pop("namespace")
        sio_event = config.pop("sio_event")
        await self.emit(sio_event, config, namespace=namespace)

    async def on_actuators_start(self, sid):
        """
        Callback on actuators_start message.
        """
        await self.emit("actuators_start", namespace="/copilot")

    async def on_actuators_stop(self, sid):
        """
        Callback on actuators_stop message.
        """
        await self.emit("actuators_stop", namespace="/copilot")

    async def on_actuator_command(self, sid, data):
        """
        Callback on actuator_command message.
        """
        await self.emit("actuator_command", data, namespace="/copilot")

    async def on_wizard(self, sid, data: dict[str, Any]):
        """
        Callback on wizard message.
        """
        namespace = data.pop("namespace")
        await self.emit("wizard", data, namespace=namespace)
        await self.emit("close_wizard")

    async def on_starter_changed(self, sid, pushed: bool):
        """
        Callback on starter_changed message.
        """
        await self.emit("starter_changed", pushed, namespace="/planner")
        await self.emit("starter_changed", (self.context.robot_id, pushed), namespace="/dashboard", skip_sid=[sid])
