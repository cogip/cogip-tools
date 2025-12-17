import socketio
from socketio.exceptions import ConnectionRefusedError

from .. import logger, server
from ..context import Context


class RobotcamNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to robotcam.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/robotcam")
        self.cogip_server = cogip_server
        self.context = Context()
        self.context.robotcam_sid = None

    async def on_connect(self, sid, environ):
        if self.context.robotcam_sid:
            message = "A robotcam is already connected"
            logger.error(f"Robotcam connection refused: {message}")
            raise ConnectionRefusedError(message)
        self.context.robotcam_sid = sid

    async def on_connected(self, sid):
        logger.info("Robotcam connected.")

    def on_disconnect(self, sid):
        self.context.robotcam_sid = None
        logger.info("Robotcam disconnected.")
