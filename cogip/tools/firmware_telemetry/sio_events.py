import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import polling2
import socketio
from google.protobuf.json_format import ParseDict

from cogip.models import TelemetryData
from cogip.protobuf import PB_TelemetryData
from . import logger

if TYPE_CHECKING:
    from .firmware_telemetry_manager import FirmwareTelemetryManager


class SioEvents(socketio.AsyncClientNamespace):
    """
    Handle all SocketIO events received by FirmwareTelemetryManager.
    """

    def __init__(self, manager: "FirmwareTelemetryManager"):
        super().__init__("/telemetry")
        self.manager = manager
        self.connected = False
        self._telemetry_callback: Callable[[TelemetryData], None] | None = None

    def set_telemetry_callback(self, callback: Callable[[TelemetryData], None] | None) -> None:
        """
        Set callback to be called for each telemetry data point.

        Args:
            callback: Function to call with each TelemetryData, or None to clear.
        """
        self._telemetry_callback = callback

    async def on_connect(self):
        """
        On connection to cogip-server.
        """
        await asyncio.to_thread(
            polling2.poll,
            lambda: self.client.connected is True,
            step=1,
            poll_forever=True,
        )
        logger.info("Connected to cogip-server")
        await self.emit("connected")

        self.connected = True

    async def on_disconnect(self) -> None:
        """
        On disconnection from cogip-server.
        """
        logger.info("Disconnected from cogip-server")
        self.connected = False

    async def on_connect_error(self, data: dict[str, Any]) -> None:
        """
        On connection error.
        """
        if isinstance(data, dict) and "message" in data:
            message = data["message"]
        else:
            message = data
        logger.error(f"Connection to cogip-server failed: {message}")

    async def on_telemetry_data(self, data: dict[str, Any]):
        """
        Handle telemetry_data from copilot.
        Store the telemetry data point and call callback if registered.
        """
        telemetry = ParseDict(data, PB_TelemetryData())
        telemetry_data = TelemetryData.from_protobuf(telemetry)
        self.manager.store.update(telemetry_data)

        if self._telemetry_callback:
            self._telemetry_callback(telemetry_data)
