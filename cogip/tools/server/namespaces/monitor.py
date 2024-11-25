import socketio

from .. import logger, server
from ..context import Context


class MonitorNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to monitor.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/monitor")
        self.cogip_server = cogip_server
        self.context = Context()
        self.context.monitor_sid = None

    async def on_connect(self, sid, environ):
        if self.context.monitor_sid:
            message = "A monitor is already connected"
            logger.error(f"Monitor connection refused: {message}")
            raise ConnectionRefusedError(message)
        self.context.monitor_sid = sid

    async def on_connected(self, sid):
        logger.info("Monitor connected.")
        await self.emit("add_robot", (self.context.robot_id, self.context.virtual), namespace="/monitor")
        if self.context.virtual:
            await self.emit("start_sensors_emulation", self.context.robot_id, namespace="/monitor")

    def on_disconnect(self, sid):
        self.context.monitor_sid = None
        logger.info("Monitor disconnected.")

    async def on_sensors_data(self, sid, sensors_data: list[int]):
        """
        Callback on sensors data.

        In emulation mode, receive sensors data from the Monitor,
        and forward to the Detector in charge of computing dynamic obstacles.
        """
        await self.emit("sensors_data", sensors_data, namespace="/detector")

    async def on_monitor_obstacles(self, sid, monitor_obstacles: list[(int, int)]):
        """
        Callback on monitor_obstacles.

        In emulation mode, send obstacle list
        """
        await self.emit("monitor_obstacles", monitor_obstacles, namespace="/detector")


    async def on_starter_changed(self, sid, pushed: bool):
        """
        Callback on starter_changed message.
        """
        await self.emit("starter_changed", pushed, namespace="/planner")
