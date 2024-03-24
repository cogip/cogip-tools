import asyncio
from typing import TYPE_CHECKING, Any

import socketio
import socketio.exceptions

from cogip import logger

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

        @self.sio.event(namespace="/dashboard")
        async def state(robot_id: int, state: dict[str, Any]):
            await self.server.sio.emit("state", (robot_id, state), namespace="/dashboard")

        @self.sio.event(namespace="/dashboard")
        async def pose_current(robot_id: int, pose: dict[str, Any]):
            await self.server.sio.emit("pose_current", (robot_id, pose), namespace="/dashboard")

        @self.sio.event(namespace="/dashboard")
        async def pose_order(robot_id: int, pose: dict[str, Any]):
            await self.server.sio.emit("pose_order", (robot_id, pose), namespace="/dashboard")

        @self.sio.event(namespace="/dashboard")
        async def obstacles(obstacles: list[dict[str, Any]]):
            await self.server.sio.emit("obstacles", (self.robot_id, obstacles), namespace="/dashboard")

        @self.sio.event(namespace="/dashboard")
        async def path(robot_id: int, path: list[dict[str, Any]]):
            await self.server.sio.emit("path", (robot_id, path), namespace="/dashboard")