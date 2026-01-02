import asyncio
from typing import TYPE_CHECKING, Any

import polling2
import socketio
from google.protobuf.json_format import ParseDict

from cogip.protobuf import (
    PB_ParameterGetResponse,
    PB_ParameterSetResponse,
)
from . import logger

if TYPE_CHECKING:
    from .firmware_parameter_manager import FirmwareParameterManager


class SioEvents(socketio.AsyncClientNamespace):
    """
    Handle all SocketIO events received by FirmwareParameterManager.
    """

    def __init__(self, manager: "FirmwareParameterManager"):
        super().__init__("/parameters")
        self.manager = manager
        self.connected = False

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
        On connection error, check if a firmware parameter manager is already connected and exit,
        or retry connection.
        """
        if isinstance(data, dict) and "message" in data:
            message = data["message"]
        else:
            message = data
        logger.error(f"Connection to cogip-server failed: {message}")

    async def on_get_parameter_response(self, data: dict[str, Any]):
        """
        Handle get_parameter_response from copilot.
        Resolve the pending Future with the response.
        """
        response = ParseDict(data, PB_ParameterGetResponse())

        logger.info(f"[SIO] Received get_response for firmware parameter hash: 0x{response.key_hash:08x}")

        # Retrieve the Future corresponding to this request
        if response.key_hash in self.manager.pending_get_requests:
            future = self.manager.pending_get_requests.pop(response.key_hash)
            if not future.done():
                future.set_result(response)
        else:
            logger.warning(f"No pending request found for firmware parameter hash: 0x{response.key_hash:08x}")

    async def on_set_parameter_response(self, data: dict[str, Any]):
        """
        Handle set_parameter_response from copilot.
        Resolve the pending Future with the response.
        """
        response = ParseDict(data, PB_ParameterSetResponse())

        logger.info(f"[SIO] Received set_response for firmware parameter hash: 0x{response.key_hash:08x}")

        # Retrieve the Future corresponding to this request
        if response.key_hash in self.manager.pending_set_requests:
            future = self.manager.pending_set_requests.pop(response.key_hash)
            if not future.done():
                future.set_result(response)
        else:
            logger.warning(f"No pending request found for firmware parameter hash: 0x{response.key_hash:08x}")
