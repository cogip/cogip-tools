from typing import Any

import socketio

from .. import logger, server


class FirmwareTelemetryNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to firmware telemetry clients.
    Supports multiple simultaneous client connections.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/telemetry")
        self.cogip_server = cogip_server

    async def on_connect(self, sid, environ):
        """Allow multiple client connections."""
        pass

    async def on_connected(self, sid):
        logger.info(f"Telemetry client connected: {sid}")

    async def on_disconnect(self, sid):
        logger.info(f"Telemetry client disconnected: {sid}")

    async def on_telemetry_enable(self, sid, data: dict[str, Any] | None = None):
        """
        Callback on telemetry_enable message.
        Forward to copilot.
        """
        logger.info("[telemetry => copilot] Telemetry enable")
        await self.emit("telemetry_enable", data or {}, namespace="/copilot")

    async def on_telemetry_disable(self, sid, data: dict[str, Any] | None = None):
        """
        Callback on telemetry_disable message.
        Forward to copilot.
        """
        logger.info("[telemetry => copilot] Telemetry disable")
        await self.emit("telemetry_disable", data or {}, namespace="/copilot")
