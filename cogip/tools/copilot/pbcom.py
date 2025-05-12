import asyncio
import base64
import binascii
from collections.abc import Callable

import can
from google.protobuf.message import DecodeError as ProtobufDecodeError

from . import logger


def pb_exception_handler(func):
    async def inner_function(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except ProtobufDecodeError as exc:
            logger.error(f"Protobuf decode error: {exc}")
        except Exception as exc:
            logger.error(f"{func}: Unknown Protobuf decode error in {type(exc)}: {exc}")

    return inner_function


class PBCom:
    can_is_fd: bool = True  # CAN frames are FD frames

    def __init__(
        self,
        can_channel: str,
        can_bitrate: int,
        canfd_data_bitrate: int,
        message_handlers: dict[int, Callable],
    ):
        self.can_bus = can.Bus(
            interface="socketcan",
            channel=can_channel,
            bitrate=can_bitrate,
            data_bitrate=canfd_data_bitrate,
            fd=self.can_is_fd,
        )
        self.message_handlers = message_handlers

        # Create asyncio queues
        self.messages_received = asyncio.Queue()  # Queue for messages received
        self.messages_to_send = asyncio.Queue()  # Queue for messages waiting to be sent

    async def run(self):
        """
        Start PBCom.
        """
        self.loop = asyncio.get_running_loop()
        self.can_reader = can.AsyncBufferedReader()
        self.notifier = can.Notifier(bus=self.can_bus, listeners=[self.can_reader], timeout=None, loop=self.loop)

        try:
            await asyncio.gather(
                self.payload_decoder(),
                self.can_receiver(),
                self.can_sender(),
            )
        except asyncio.CancelledError:
            self.can_bus.shutdown()

    async def payload_decoder(self):
        """
        Async worker decoding messages received from the robot.
        """
        uuid: int
        encoded_payload: bytes

        try:
            while True:
                uuid, encoded_payload = await self.messages_received.get()
                request_handler = self.message_handlers.get(uuid)
                if not request_handler:
                    logger.warning(f"No handler found for message uuid '{uuid}'")
                else:
                    if not encoded_payload:
                        await request_handler()
                    else:
                        await request_handler(encoded_payload)

                self.messages_received.task_done()
        except asyncio.CancelledError:
            raise

    async def send_can_message(self, *args) -> None:
        await self.messages_to_send.put(args)

    async def can_receiver(self):
        """
        Async worker reading messages from the robot on CAN bus.

        Messages is base64-encoded.
        After decoding, first byte is the message type, following bytes are
        the Protobuf encoded message (if any).
        """
        try:
            while True:
                # Read next message
                can_message = await self.can_reader.get_message()

                # Get message uuid on first bytes
                uuid = can_message.arbitration_id

                if can_message.dlc == 0:
                    await self.messages_received.put((uuid, None))
                    continue

                # Base64 decoding
                try:
                    pb_message = base64.decodebytes(can_message.data)
                except binascii.Error:
                    logger.error("Failed to decode base64 message.")
                    continue

                # Send Protobuf message for decoding
                await self.messages_received.put((uuid, pb_message))
        except asyncio.CancelledError:
            raise

    async def can_sender(self):
        """
        Async worker encoding and sending Protobuf messages to the robot on CAN bus.

        See `can_receiver` for message encoding.
        """
        try:
            while True:
                uuid, pb_message = await self.messages_to_send.get()
                logger.info(f"Send 0x{uuid:4x}:\n{pb_message}")
                if pb_message:
                    response_serialized = await self.loop.run_in_executor(None, pb_message.SerializeToString)
                    response_base64 = await self.loop.run_in_executor(None, base64.encodebytes, response_serialized)
                else:
                    response_base64 = None
                try:
                    self.can_bus.send(can.Message(arbitration_id=uuid, data=response_base64, is_fd=self.can_is_fd))
                except Exception as e:
                    logger.error(e)
                self.messages_to_send.task_done()
        except asyncio.CancelledError:
            raise
