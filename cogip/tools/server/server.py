import os
from typing import Any

import socketio
from pydantic import ValidationError
from socketio.exceptions import ConnectionRefusedError
from uvicorn.main import Server as UvicornServer

from cogip import models
from cogip.cpp.libraries.shared_memory import SharedMemory
from . import context, logger, namespaces


class Server:
    _original_uvicorn_exit_handler = UvicornServer.handle_exit  # Backup of original exit handler to overload it
    _shared_memory: SharedMemory | None = None  # Shared memory instance

    @staticmethod
    def handle_exit(*args, **kwargs):
        """Overload function for Uvicorn handle_exit"""
        Server._shared_memory = None
        Server._original_uvicorn_exit_handler(*args, **kwargs)

    def __init__(self):
        """
        Class constructor.

        Create SocketIO server.
        """
        self.context = context.Context()
        self.context.robot_id = int(os.environ["ROBOT_ID"])
        self.root_menu = models.ShellMenu(name="Root Menu", entries=[])
        self.context.tool_menus["root"] = self.root_menu
        self.context.current_tool_menu = "root"

        if Server._shared_memory is None:
            Server._shared_memory = SharedMemory(f"cogip_{self.context.robot_id}", owner=True)

        self.sio = socketio.AsyncServer(
            always_connect=False,
            async_mode="asgi",
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False,
        )
        self.app = socketio.ASGIApp(self.sio)
        self.sio.register_namespace(namespaces.DashboardNamespace(self))
        self.sio.register_namespace(namespaces.MonitorNamespace(self))
        self.sio.register_namespace(namespaces.CopilotNamespace(self))
        self.sio.register_namespace(namespaces.DetectorNamespace(self))
        self.sio.register_namespace(namespaces.PlannerNamespace(self))
        self.sio.register_namespace(namespaces.RobotcamNamespace(self))
        self.sio.register_namespace(namespaces.BeaconNamespace(self))

        # Overload default Uvicorn exit handler
        UvicornServer.handle_exit = self.handle_exit

        @self.sio.event
        def connect(sid, environ, auth):
            logger.warning(f"A client tried to connect to namespace / (sid={sid})")
            raise ConnectionRefusedError("Connection refused to namespace /")

        @self.sio.on("*")
        def catch_all(event, sid, data):
            logger.warning(f"A client tried to send data to namespace / (sid={sid}, event={event})")

    async def register_menu(self, namespace: str, data: dict[str, Any]) -> None:
        if not (name := data.get("name")):
            logger.warning(f"register_menu: missing 'name' in data: {data}")
            return
        if not (menu_dict := data.get("menu")):
            logger.warning(f"register_menu: missing 'menu' in data: {data}")
            return
        try:
            menu = models.ShellMenu.model_validate(menu_dict)
        except ValidationError as exc:
            logger.warning(f"register_menu: cannot validate 'menu': {exc}")
            return

        ns_name = f"{namespace}/{name}"
        entry = models.MenuEntry(cmd=ns_name, desc=f"{menu.name} Menu")
        if ns_name not in self.context.tool_menus:
            self.root_menu.entries.append(entry)
        exit_entry = models.MenuEntry(cmd="exit", desc="Exit Menu")
        menu.entries.append(exit_entry)
        self.context.tool_menus[ns_name] = menu
        await self.sio.emit(
            "tool_menu",
            self.context.tool_menus[self.context.current_tool_menu].model_dump(),
            namespace="/dashboard",
        )
