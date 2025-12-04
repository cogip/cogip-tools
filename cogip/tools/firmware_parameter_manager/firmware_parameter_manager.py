import asyncio

from cogip.models.firmware_parameter import FirmwareParametersGroup
from cogip.protobuf import (
    PB_ParameterGetRequest,
    PB_ParameterGetResponse,
    PB_ParameterSetRequest,
    PB_ParameterSetResponse,
)
from cogip.tools.copilot.pbcom import PBCom, pb_exception_handler
from . import logger

# Service: 0x3000 - 0x3FFF
parameter_set_uuid: int = 0x3004
parameter_set_response_uuid: int = 0x3005
parameter_get_uuid: int = 0x3006
parameter_get_response_uuid: int = 0x3007


class FirmwareParameterManager:
    """
    Manager to handle firmware parameter requests/responses via PBCom.
    Uses asyncio.Future to correlate requests with their responses.
    """

    def __init__(self, pbcom: PBCom, parameter_group: FirmwareParametersGroup):
        self.pbcom = pbcom
        self.parameter_group = parameter_group

        # Dictionary to store Futures waiting for responses
        # Key: firmware parameter hash (int), Value: asyncio.Future
        self.pending_get_requests: dict[int, asyncio.Future] = {}
        self.pending_set_requests: dict[int, asyncio.Future] = {}

        # Register message handlers
        self.pbcom.register_message_handler(parameter_get_response_uuid, self._on_get_response)
        self.pbcom.register_message_handler(parameter_set_response_uuid, self._on_set_response)

    @pb_exception_handler
    async def _on_get_response(self, message: bytes | None = None):
        """
        Callback called when receiving a get_firmware_parameter response.
        """
        if not message:
            logger.warning("Received empty message")
            return

        response = PB_ParameterGetResponse()
        response.ParseFromString(message)

        logger.info(f"Received get_response for firmware parameter hash: 0x{response.key_hash:08x}")

        # Retrieve the Future corresponding to this request
        if response.key_hash in self.pending_get_requests:
            future = self.pending_get_requests.pop(response.key_hash)
            if not future.done():
                future.set_result(response)
        else:
            logger.warning(f"No pending request found for firmware parameter hash: 0x{response.key_hash:08x}")

    @pb_exception_handler
    async def _on_set_response(self, message: bytes | None = None):
        """
        Callback called when receiving a set_firmware_parameter response.
        """
        if not message:
            logger.warning("Received empty set_response")
            return

        response = PB_ParameterSetResponse()
        response.ParseFromString(message)

        logger.info(f"Received set_response for firmware parameter hash: 0x{response.key_hash:08x}")

        # Retrieve the Future corresponding to this request
        if response.key_hash in self.pending_set_requests:
            future = self.pending_set_requests.pop(response.key_hash)
            if not future.done():
                future.set_result(response)
        else:
            logger.warning(f"No pending request found for firmware parameter hash: 0x{response.key_hash:08x}")

    async def get_parameter_value(
        self,
        parameter_name: str,
        timeout: float = 0.1,
    ) -> float | int | bool:
        """
        Sends a get_firmware_parameter request and waits for the response.

        Args:
            parameter_name: Name of the firmware parameter to retrieve
            timeout: Timeout in seconds (default: 0.1)

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

        parameter_hash = hash(parameter)
        self.pending_get_requests[parameter_hash] = future

        try:
            # Create and send the request
            request = PB_ParameterGetRequest()
            parameter.pb_copy(request)

            await self.pbcom.send_can_message(parameter_get_uuid, request)

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
        timeout: float = 0.1,
    ) -> None:
        """
        Sends a set_firmware_parameter request and waits for the response.

        Args:
            parameter_name: Name of the firmware parameter to modify
            value: Value to set (int, float, or bool)
            timeout: Timeout in seconds (default: 0.1)

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

        parameter_hash = hash(parameter)
        self.pending_set_requests[parameter_hash] = future

        try:
            # Create and send the request
            request = PB_ParameterSetRequest(key_hash=parameter_hash)
            parameter.pb_copy(request)
            await self.pbcom.send_can_message(parameter_set_uuid, request)

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
