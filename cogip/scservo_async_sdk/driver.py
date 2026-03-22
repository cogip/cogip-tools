import asyncio
import logging

import serial

from .protocol import Packet, PacketReader

logger = logging.getLogger(__name__)


class SCServoDriver:
    def __init__(self, port: str, baudrate: int = 1000000):
        self.port = port
        self.baudrate = baudrate
        self.serial: serial.Serial | None = None
        self.reader = PacketReader()
        self.response_future: asyncio.Future | None = None
        self.lock = asyncio.Lock()

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def open(self):
        # run_in_executor to avoid blocking event loop during open
        loop = asyncio.get_running_loop()
        self.serial = await loop.run_in_executor(None, self._open_serial)
        loop.add_reader(self.serial.fileno(), self._data_received)

    def _open_serial(self) -> serial.Serial:
        return serial.Serial(
            self.port,
            self.baudrate,
            timeout=0,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
        )

    async def close(self):
        if self.serial:
            loop = asyncio.get_running_loop()
            loop.remove_reader(self.serial.fileno())
            await loop.run_in_executor(None, self.serial.close)
            self.serial = None

    def _data_received(self):
        try:
            data = self.serial.read(self.serial.in_waiting)
        except Exception as e:
            logger.error(f"Serial read error: {e}")
            return

        if data:
            logger.debug(f"RX: {data.hex()}")
            self.reader.feed(data)
            # Try to parse packets
            while True:
                # We only process one packet at a time for simple request-response
                # But multiple packets could arrive if we are slow or there's noise
                pkt = self.reader.scan_packet()
                if pkt:
                    if self.response_future and not self.response_future.done():
                        # We are waiting for a response
                        # Check ID?
                        # For now assume the first valid packet is the response
                        self.response_future.set_result(pkt)
                    else:
                        # Unexpected packet
                        pass
                else:
                    break

    async def send_packet(self, packet: Packet, expect_response: bool = True, timeout: float = 0.5) -> Packet | None:
        async with self.lock:
            if not self.serial:
                raise RuntimeError("Serial port not open")

            # Clear input buffer to avoid reading old data
            self.serial.reset_input_buffer()
            self.reader = PacketReader()  # Clear our buffer too

            data = packet.to_bytes()
            logger.debug(f"TX: {data.hex()}")
            self.serial.write(data)

            if not expect_response:
                return None

            # Broadcast ID usually doesn't reply, handled by expect_response=False caller
            if packet.id == 0xFE:
                return None

            loop = asyncio.get_running_loop()
            self.response_future = loop.create_future()

            try:
                resp = await asyncio.wait_for(self.response_future, timeout)
                # Optional: Validate Response ID matches Request ID
                if resp.id != packet.id:
                    # TODO: handle mismatch, maybe wait more?
                    # For now return it, let upper layer decide
                    pass
                return resp
            except TimeoutError:
                return None
            finally:
                self.response_future = None
