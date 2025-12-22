import asyncio

import socketio

from cogip.models import FirmwareParametersGroup
from . import logger
from .sio_events import SioEvents


class FirmwareParameterManager:
    """
    Manager to handle firmware parameter requests/responses via SocketIO through copilot.
    Uses asyncio.Future to correlate requests with their responses.

    This class is designed to be embedded into another Socket.IO client (e.g., Planner,
    Monitor, or any tool that needs firmware parameter access). It registers its own
    namespace (/parameters) on the provided client, allowing the host tool to manage
    the connection lifecycle while benefiting from firmware parameter functionality.

    Note on concurrent usage: The correlation mechanism uses parameter hashes (FNV-1a)
    to match responses to requests. This makes the system naturally resilient to multiple
    clients making concurrent requests - each client maintains its own pending requests
    dictionary and only resolves its own Futures. However, this usage pattern is not
    recommended as it may lead to unpredictable firmware behavior and debugging complexity.
    Prefer having a single client handle firmware parameters at a time.
    """

    def __init__(
        self,
        sio: socketio.AsyncClient,
        parameter_group: FirmwareParametersGroup,
    ):
        """
        Initialize the FirmwareParameterManager.

        Args:
            sio: External Socket.IO client on which to register the /parameters namespace.
                 The host client is responsible for connection management.
            parameter_group: The firmware parameters to manage
        """
        self.sio = sio
        self.parameter_group = parameter_group

        self.sio_events = SioEvents(self)
        self.sio.register_namespace(self.sio_events)

        # Dictionary to store Futures waiting for responses
        # Key: firmware parameter hash (int), Value: asyncio.Future
        self.pending_get_requests: dict[int, asyncio.Future] = {}
        self.pending_set_requests: dict[int, asyncio.Future] = {}

    @property
    def namespace(self) -> str:
        """Return the namespace path to include when connecting the host client."""
        return self.sio_events.namespace

    @property
    def is_connected(self) -> bool:
        """Check if the namespace is connected and ready."""
        return self.sio_events.connected

    async def get_parameter_value(
        self,
        parameter_name: str,
        timeout: float = 1,
    ) -> float | int | bool:
        """
        Sends a get_firmware_parameter request and waits for the response.

        Args:
            parameter_name: Name of the firmware parameter to retrieve
            timeout: Timeout in seconds (default: 1)

        Returns:
            The firmware parameter value (float, int, or bool) after pydantic validation

        Raises:
            KeyError: If the firmware parameter name is not found in the firmware parameter group
            TimeoutError: If no response is received within the timeout
        """
        # Validate that firmware parameter exists in the group
        parameter = self.parameter_group.get(parameter_name)

        # Create a Future for this request
        future = asyncio.Future()

        # Store pending request for response correalation
        parameter_hash = hash(parameter)
        self.pending_get_requests[parameter_hash] = future

        try:
            logger.info(f"[firmware_parameter => server] get: {parameter}")
            await self.sio.emit("get_parameter_value", parameter.model_dump(by_alias=True), namespace="/parameters")

            logger.info(f"Sent get_parameter request for hash: 0x{parameter_hash:08x}")

            # Wait for the response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)

            # Update parameter with response data (pydantic validation happens here)
            parameter.pb_read(response)

            # Return the validated value
            return parameter.value

        except TimeoutError:
            # Clean up on timeout
            if not future.done():
                future.cancel()

            self.pending_get_requests.pop(parameter_hash, None)
            logger.error(f"Timeout waiting for get_firmware_parameter response (hash: 0x{parameter_hash:08x})")
            raise TimeoutError(f"No response received for firmware parameter hash 0x{parameter_hash:08x}")

        except Exception as exc:
            # Clean up on error
            if not future.done():
                future.cancel()

            self.pending_get_requests.pop(parameter_hash, None)
            logger.error(f"Error in get_parameter: {exc}")
            raise

    async def set_parameter_value(
        self,
        parameter_name: str,
        value: int | float | bool,
        timeout: float = 1,
    ) -> None:
        """
        Sends a set_firmware_parameter request and waits for the response.

        Args:
            parameter_name: Name of the firmware parameter to modify
            value: Value to set (int, float, or bool)
            timeout: Timeout in seconds (default: 1)

        Returns:
            True if the firmware parameter was successfully written

        Raises:
            KeyError: If the firmware parameter name is not found in the firmware parameter group
            ValidationError: If the value type doesn't match the firmware parameter type or is invalid
            TimeoutError: If no response is received within the timeout
        """
        # Validate that firmware parameter exists in the group
        parameter = self.parameter_group.get(parameter_name)

        # Set the new value (pydantic validation happens here)
        parameter.value = value

        # Create a Future for this request
        future = asyncio.Future()

        # Store pending request for response correalation
        parameter_hash = hash(parameter)
        self.pending_set_requests[parameter_hash] = future

        try:
            logger.info(f"[firmware_parameter => server] set: {parameter}")
            await self.sio.emit("set_parameter_value", parameter.model_dump(by_alias=True), namespace="/parameters")

            logger.info(f"Sent set_parameter request for hash: 0x{parameter_hash:08x}")

            # Wait for the response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)

            # Update parameter with response data (pydantic validation happens here)
            parameter.pb_read(response)

        except TimeoutError:
            # Clean up on timeout
            if not future.done():
                future.cancel()

            self.pending_set_requests.pop(parameter_hash, None)
            logger.error(f"Timeout waiting for set_firmware_parameter response (hash: 0x{parameter_hash:08x})")
            raise TimeoutError(f"No response received for firmware parameter hash 0x{parameter_hash:08x}")

        except Exception as exc:
            # Clean up on error
            if not future.done():
                future.cancel()

            self.pending_set_requests.pop(parameter_hash, None)
            logger.error(f"Error in set_parameter: {exc}")
            raise

    def cleanup(self):
        """
        Cleans up all pending Futures.
        """
        for future in self.pending_get_requests.values():
            if not future.done():
                future.cancel()
        for future in self.pending_set_requests.values():
            if not future.done():
                future.cancel()

        self.pending_get_requests.clear()
        self.pending_set_requests.clear()
