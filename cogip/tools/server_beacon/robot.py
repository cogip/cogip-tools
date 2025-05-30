import asyncio
from typing import TYPE_CHECKING, Any

import socketio
import socketio.exceptions

from cogip import logger
from cogip.tools.planner import actions
from cogip.tools.planner.positions import StartPosition

if TYPE_CHECKING:
    from .server import Server


class Robot:
    def __init__(self, server: "Server", robot_id: int) -> None:
        super().__init__()
        self.server = server
        self.robot_id = robot_id
        self.sio = socketio.AsyncClient(
            reconnection=True,
            reconnection_delay=1,
            reconnection_delay_max=1,
            randomization_factor=0,
            logger=False,
            engineio_logger=False,
        )
        self.exiting = False
        self.register_sio_events()

    async def run(self):
        try:
            while not self.exiting:
                try:
                    await self.sio.connect(
                        f"http://robot{self.robot_id}:809{self.robot_id}",
                        namespaces=["/beacon", "/dashboard"],
                    )
                except socketio.exceptions.ConnectionError:
                    await asyncio.sleep(1)
                    continue
                break

            await self.sio.wait()
        except asyncio.CancelledError:
            await self.sio.disconnect()
            pass

    def register_sio_events(self) -> None:
        @self.sio.event(namespace="/beacon")
        async def connect():
            """
            Callback on server connection.
            """
            while True:
                if self.sio.connected:
                    break
                await asyncio.sleep(0.2)

            logger.info(f"Beacon handler: connected to robot {self.robot_id}")
            await self.sio.emit("connected", namespace="/beacon")
            await self.server.sio.emit("add_robot", self.robot_id, namespace="/dashboard")

        @self.sio.event(namespace="/beacon")
        def connect_error(data):
            """
            Callback on server connection error.
            """
            logger.debug(f"Beacon handler: connection to robot {self.robot_id} failed.")

        @self.sio.event(namespace="/beacon")
        async def disconnect():
            """
            Callback on server disconnection.
            """
            logger.info(f"Beacon handler: disconnected from robot {self.robot_id}")
            await self.server.sio.emit("del_robot", self.robot_id, namespace="/dashboard")

        # @self.sio.event(namespace="/dashboard")
        # async def state(robot_id: int, state: dict[str, Any]):
        #     await self.server.sio.emit("state", (robot_id, state), namespace="/dashboard")

        @self.sio.event(namespace="/dashboard")
        async def pose_current(robot_id: int, pose: dict[str, Any]):
            await self.server.sio.emit("pose_current", (robot_id, pose), namespace="/dashboard")

        # @self.sio.event(namespace="/dashboard")
        # async def pose_order(robot_id: int, pose: dict[str, Any]):
        #     await self.server.sio.emit("pose_order", (robot_id, pose), namespace="/dashboard")

        # @self.sio.event(namespace="/dashboard")
        # async def obstacles(robot_id, obstacles: list[dict[str, Any]]):
        #     await self.server.sio.emit("obstacles", (robot_id, obstacles), namespace="/dashboard")

        # @self.sio.event(namespace="/dashboard")
        # async def path(robot_id: int, path: list[dict[str, Any]]):
        #     await self.server.sio.emit("path", (robot_id, path), namespace="/dashboard")

        @self.sio.event(namespace="/beacon")
        async def pami_reset():
            for robot_id, robot in self.server.robots.items():
                if robot.sio.connected:
                    strategy: actions.Strategy | None = None
                    match robot_id:
                        case 2:
                            strategy = actions.Strategy.Pami2
                        case 3:
                            strategy = actions.Strategy.Pami3
                        case 4:
                            strategy = actions.Strategy.Pami4
                        case 5:
                            strategy = actions.Strategy.Pami5

                    if strategy:
                        await robot.sio.emit(
                            "wizard",
                            {
                                "name": "Choose Strategy",
                                "value": strategy.name,
                            },
                            namespace="/beacon",
                        )

                    await robot.sio.emit(
                        "wizard",
                        {
                            "name": "Choose Avoidance",
                            "value": "Disabled",
                        },
                        namespace="/beacon",
                    )

        @self.sio.event(namespace="/beacon")
        async def pami_table(table):
            for robot_id, robot in self.server.robots.items():
                if robot_id == 1:
                    continue
                if robot.sio.connected:
                    await robot.sio.emit(
                        "wizard",
                        {
                            "name": "Choose Table",
                            "type": "choice_str",
                            "value": table,
                        },
                        namespace="/beacon",
                    )
                    position: StartPosition | None = None
                    match robot_id:
                        case 2:
                            position = StartPosition.PAMI2
                        case 3:
                            position = StartPosition.PAMI3
                        case 4:
                            position = StartPosition.PAMI4
                        case 5:
                            position = StartPosition.PAMI5

                    if position:
                        await robot.sio.emit(
                            "wizard",
                            {
                                "name": "Choose Start Position",
                                "value": position.name,
                            },
                            namespace="/beacon",
                        )

        @self.sio.event(namespace="/beacon")
        async def pami_camp(camp):
            for robot_id, robot in self.server.robots.items():
                if robot_id == 1:
                    continue
                if robot.sio.connected:
                    await robot.sio.emit(
                        "wizard",
                        {
                            "name": "Choose Camp",
                            "type": "camp",
                            "value": camp,
                        },
                        namespace="/beacon",
                    )

        @self.sio.event(namespace="/beacon")
        async def pami_play(timestamp: str):
            for robot_id, robot in self.server.robots.items():
                if robot_id == 1:
                    continue
                if robot.sio.connected:
                    await robot.sio.emit("command", ("play", timestamp), namespace="/beacon")

        @self.sio.event(namespace="/beacon")
        async def start_countdown(robot_id: int, countdown: int, timestamp: str, color: str | None = None):
            logger.info(f"Start countdown: {countdown}")
            await self.server.sio.emit(
                "start_countdown",
                (robot_id, countdown, timestamp, color),
                namespace="/dashboard",
            )
