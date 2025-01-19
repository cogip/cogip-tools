import os
from typing import Any

import socketio
from pydantic import ValidationError
from socketio.exceptions import ConnectionRefusedError
from uvicorn.main import Server as UvicornServer

from cogip import models
from cogip.cpp.libraries.models import Pose as SharedPose
from cogip.cpp.libraries.obstacles import ObstacleCircleList as SharedObstacleCircleList
from cogip.cpp.libraries.obstacles import ObstacleRectangleList as SharedObstacleRectangleList
from cogip.cpp.libraries.shared_memory import SharedMemory
from cogip.utils.asyncloop import AsyncLoop
from . import context, logger, namespaces


class Server:
    _original_uvicorn_exit_handler = UvicornServer.handle_exit  # Backup of original exit handler to overload it
    _shared_memory: SharedMemory | None = None  # Shared memory instance
    _shared_pose_current: SharedPose | None = None
    _shared_circle_obstacles: SharedObstacleCircleList | None = None
    _shared_rectangle_obstacles: SharedObstacleRectangleList | None = None

    @staticmethod
    def handle_exit(*args, **kwargs):
        """Overload function for Uvicorn handle_exit"""
        Server._shared_rectangle_obstacles = None
        Server._shared_circle_obstacles = None
        Server._shared_pose_current = None
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
        self.dashboard_updater_loop = AsyncLoop(
            "Dashboard updater loop",
            float(os.getenv("SERVER_DASHBOARD_UPDATE_INTERVAL", 0.2)),
            self.update_dashboard,
        )

        if Server._shared_memory is None:
            Server._shared_memory = SharedMemory(f"cogip_{self.context.robot_id}", owner=True)
            Server._shared_pose_current = Server._shared_memory.get_pose_current()
            Server._shared_circle_obstacles = Server._shared_memory.get_circle_obstacles()
            Server._shared_rectangle_obstacles = Server._shared_memory.get_rectangle_obstacles()

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

        self.dashboard_updater_loop.start()

        # Overload default Uvicorn exit handler
        UvicornServer.handle_exit = Server.handle_exit

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

    async def update_dashboard(self):
        pose_current = {
            "x": Server._shared_pose_current.x,
            "y": Server._shared_pose_current.y,
            "O": Server._shared_pose_current.angle,
        }
        await self.sio.emit("pose_current", (self.context.robot_id, pose_current), namespace="/dashboard")
        obstacles = []
        obstacles += [
            {
                "x": obstacle.center.x,
                "y": obstacle.center.y,
                "angle": 0,
                "radius": obstacle.radius,
                "id": obstacle.id,
            }
            for obstacle in Server._shared_circle_obstacles
        ]
        obstacles += [
            {
                "x": obstacle.center.x,
                "y": obstacle.center.y,
                "angle": obstacle.center.angle,
                "length_x": obstacle.length_x,
                "length_y": obstacle.length_y,
                "id": obstacle.id,
            }
            for obstacle in Server._shared_rectangle_obstacles
        ]
        await self.sio.emit("obstacles", (self.context.robot_id, obstacles), namespace="/dashboard")
