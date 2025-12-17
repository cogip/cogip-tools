import socketio
from socketio.exceptions import ConnectionRefusedError

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
        if self.context.planner_sid and self.context.detector_sid and not self.context.robot_added:
            await self.emit(
                "add_robot",
                (self.context.robot_id, self.context.virtual_planner, self.context.virtual_detector),
                namespace="/monitor",
            )
            self.context.robot_added = True

    def on_disconnect(self, sid):
        self.context.monitor_sid = None
        self.context.robot_added = False
        logger.info("Monitor disconnected.")
