from typing import Any

import socketio

from .. import logger, server
from ..context import Context


class DetectorNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to detector.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/detector")
        self.cogip_server = cogip_server
        self.context = Context()

    async def on_connect(self, sid, environ):
        if self.context.detector_sid:
            message = "A detector is already connected"
            logger.error(f"Detector connection refused: {message}")
            raise ConnectionRefusedError(message)

        self.context.detector_sid = sid

    async def on_connected(self, sid, virtual: bool):
        logger.info(f"Detector connected (virtual={virtual}).")
        self.context.virtual_detector = virtual

    async def on_disconnect(self, sid):
        self.context.detector_sid = None
        logger.info("Detector disconnected.")

    async def on_register_menu(self, sid, data: dict[str, Any]):
        """
        Callback on register_menu.
        """
        await self.cogip_server.register_menu("detector", data)

    async def on_config(self, sid, config: dict[str, Any]):
        """
        Callback on config message.
        """
        await self.emit("config", config, namespace="/dashboard")
