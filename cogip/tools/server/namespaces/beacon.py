import socketio

from .. import logger, server
from ..context import Context


class BeaconNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to beacon server.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/beacon")
        self.cogip_server = cogip_server
        self.context = Context()

    async def on_connect(self, sid, environ):
        if self.context.beacon_sid:
            message = "A beacon server is already connected"
            logger.error(f"Beacon verser connection refused: {message}")
            raise ConnectionRefusedError(message)
        self.context.beacon_sid = sid

    async def on_connected(self, sid):
        logger.info("Beacon connected.")

    def on_disconnect(self, sid):
        self.context.beacon_sid = None
        logger.info("Beacon disconnected.")

    async def on_reset(self, sid):
        """
        Callback on reset message.
        """
        logger.info("[beacon => planner] reset.")
        await self.emit("reset", namespace="/planner")

    async def on_command(self, sid, cmd):
        """
        Callback on command.
        """
        logger.info(f"[beacon => planner] Command: {cmd}")
        await self.emit("command", cmd, namespace="/planner")

    async def on_wizard(self, sid, message):
        """
        Callback on wizard message.
        """
        await self.emit("wizard", message, namespace="/planner")
