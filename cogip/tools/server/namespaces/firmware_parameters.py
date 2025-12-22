from typing import Any

import socketio

from .. import logger, server


class FirmwareParametersNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to firmware parameter clients.
    Supports multiple simultaneous client connections.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/parameters")
        self.cogip_server = cogip_server

    async def on_connect(self, sid, environ):
        """Allow multiple client connections."""
        pass

    async def on_connected(self, sid):
        logger.info(f"Parameter client connected: {sid}")

    async def on_disconnect(self, sid):
        logger.info(f"Parameter client disconnected: {sid}")

    async def on_get_parameter_value(self, sid, data: dict[str, Any]):
        """
        Callback on get_parameter_value message.
        Forward to copilot.
        """
        logger.info(f"[parameters => copilot] Get parameter: {data}")
        await self.emit("get_parameter_value", data, namespace="/copilot")

    async def on_set_parameter_value(self, sid, data: dict[str, Any]):
        """
        Callback on set_parameter_value message.
        Forward to copilot.
        """
        logger.info(f"[parameters => copilot] Set parameter: {data}")
        await self.emit("set_parameter_value", data, namespace="/copilot")
