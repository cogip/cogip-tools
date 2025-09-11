import asyncio
import os

import socketio
from socketio.exceptions import ConnectionRefusedError
from uvicorn.main import Server as UvicornServer

from cogip.tools.planner.camp import Camp
from cogip.tools.planner.start_positions import StartPositionEnum
from cogip.tools.planner.table import TableEnum
from . import logger, namespaces
from .robot import Robot


class Server:
    original_uvicorn_exit_handler = UvicornServer.handle_exit
    exiting: bool = False
    robots: dict[int, Robot] = {}
    robot_tasks: set[asyncio.Task] = set()

    def __init__(self):
        """
        Class constructor.

        Create SocketIO server and robot servers connections
        """
        UvicornServer.handle_exit = Server.handle_exit

        self.sio = socketio.AsyncServer(
            always_connect=False,
            async_mode="asgi",
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False,
        )
        self.app = socketio.ASGIApp(self.sio)
        self.sio.register_namespace(namespaces.DashboardNamespace(self))

        self.camp = Camp.Colors.blue
        self.table = TableEnum.Game

        for i in range(1, int(os.environ["SERVER_BEACON_MAX_ROBOTS"]) + 1):
            robot = Robot(self, i)
            task = asyncio.create_task(robot.run())
            Server.robots[i] = robot
            Server.robot_tasks.add(task)
            task.add_done_callback(Server.robot_tasks.discard)

        @self.sio.event
        def connect(sid, environ, auth):
            logger.warning(f"A client tried to connect to namespace / (sid={sid})")
            raise ConnectionRefusedError("Connection refused to namespace /")

        @self.sio.on("*")
        def catch_all(event, sid, data):
            logger.warning(f"A client tried to send data to namespace / (sid={sid}, event={event})")

    @staticmethod
    def handle_exit(*args, **kwargs):
        """Overload function for Uvicorn handle_exit"""
        Server.exiting = True
        for _, robot in Server.robots.items():
            robot.exiting = True
            robot.sio.reconnection_attempts = -1
        for task in Server.robot_tasks:
            task.cancel()

        Server.original_uvicorn_exit_handler(*args, **kwargs)

    async def choose_camp(self):
        """
        Choose camp command from the menu.
        Send camp wizard message.
        """
        await self.sio.emit(
            "wizard",
            {
                "name": "Choose Camp",
                "type": "camp",
                "value": self.camp.name,
            },
            namespace="/dashboard",
        )

    async def choose_table(self):
        """
        Choose table command from the menu.
        Send table wizard message.
        """
        await self.sio.emit(
            "wizard",
            {
                "name": "Choose Table",
                "type": "choice_str",
                "choices": [e.name for e in TableEnum],
                "value": self.table.name,
            },
            namespace="/dashboard",
        )

    async def reset_robots(self):
        for robot_id, robot in self.robots.items():
            if robot.sio.connected:
                position: StartPositionEnum | None = None
                match robot_id:
                    case 1:
                        position = StartPositionEnum.Bottom
                    case 2:
                        position = StartPositionEnum.PAMI2
                    case 3:
                        position = StartPositionEnum.PAMI3
                    case 4:
                        position = StartPositionEnum.PAMI4
                    case 5:
                        position = StartPositionEnum.PAMI5
                if position:
                    await robot.sio.emit(
                        "wizard",
                        {
                            "name": "Choose Start Position",
                            "value": position.name,
                        },
                        namespace="/beacon",
                    )
