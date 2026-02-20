import asyncio
import logging

from .constants import Instruction, Memory, TorqueEnable
from .driver import SCServoDriver
from .protocol import Packet

logger = logging.getLogger(__name__)


def from_sign_magnitude(val: int, sign_bit: int = 15) -> int:
    if val & (1 << sign_bit):
        return -(val & ~(1 << sign_bit))
    return val


def to_sign_magnitude(val: int, sign_bit: int = 15) -> int:
    mask = 1 << sign_bit
    if val < 0:
        return (-val) | mask
    return val


def make_word(low: int, high: int, endian: str = "big") -> int:
    if endian == "big":
        return (low << 8) | high
    return low | (high << 8)


class SCServo:
    def __init__(self, driver: SCServoDriver, id: int, endian: str = "big"):
        self.driver = driver
        self.id = id
        self.endian = endian

    async def _read(self, address: int, length: int) -> tuple[bytes | None, int]:
        pkt = Packet(self.id, Instruction.READ, [address, length])
        resp = await self.driver.send_packet(pkt)
        if resp:
            # We return data if length matches, even if error is set
            # because some errors (like overload) might not prevent reading data
            if len(resp.params) == length:
                return bytes(resp.params), resp.instruction
            elif resp.instruction != 0:
                # If error set and no data (or mismatch), return None data but error code
                return None, resp.instruction
        return None, -1

    async def _write(self, address: int, data: list[int]) -> int:
        params = [address] + data
        pkt = Packet(self.id, Instruction.WRITE, params)
        resp = await self.driver.send_packet(pkt)
        if resp:
            return resp.instruction
        return -1

    async def _reg_write(self, address: int, data: list[int]) -> int:
        params = [address] + data
        pkt = Packet(self.id, Instruction.REG_WRITE, params)
        resp = await self.driver.send_packet(pkt)
        if resp:
            return resp.instruction
        return -1

    async def action(self) -> int:
        pkt = Packet(self.id, Instruction.ACTION, [])
        # If specific ID, it returns status packet.
        resp = await self.driver.send_packet(pkt)
        if resp:
            return resp.instruction
        return -1

    async def ping(self) -> int:
        pkt = Packet(self.id, Instruction.PING, [])
        resp = await self.driver.send_packet(pkt)
        if resp:
            return resp.instruction
        return -1

    async def enable_torque(self, enable: bool = True) -> int:
        val = TorqueEnable.ON if enable else TorqueEnable.OFF
        return await self._write(Memory.TORQUE_ENABLE, [val])

    def _split_word(self, val: int) -> list[int]:
        val = val & 0xFFFF
        if self.endian == "big":
            return [(val >> 8) & 0xFF, val & 0xFF]
        return [val & 0xFF, (val >> 8) & 0xFF]

    async def set_position(self, position: int, time: int = 0, speed: int = 0) -> int:
        # For SC Series (Big Endian):
        # Write to GOAL_POSITION_L (42)
        # Order: PosH, PosL, TimeH, TimeL, SpeedH, SpeedL

        # Position is simply raw value (no sign conversion needed usually for write in SC protocol)
        data = []
        data.extend(self._split_word(position))
        data.extend(self._split_word(time))
        data.extend(self._split_word(speed))

        return await self._write(Memory.GOAL_POSITION_L, data)

    async def reg_write_position(self, position: int, time: int = 0, speed: int = 0) -> int:
        data = []
        data.extend(self._split_word(position))
        data.extend(self._split_word(time))
        data.extend(self._split_word(speed))

        return await self._reg_write(Memory.GOAL_POSITION_L, data)

    async def read_position(self) -> int | None:
        data, _ = await self._read(Memory.PRESENT_POSITION_L, 2)
        if data:
            raw = make_word(data[0], data[1])
            return from_sign_magnitude(raw, 15)
        return None

    async def read_speed(self) -> int | None:
        data, current_error = await self._read(Memory.PRESENT_SPEED_L, 2)
        if data:
            raw = make_word(data[0], data[1])
            return from_sign_magnitude(raw, 15)
        return None

    async def read_load(self) -> int | None:
        data, _ = await self._read(Memory.PRESENT_LOAD_L, 2)
        if data:
            raw = make_word(data[0], data[1])
            return from_sign_magnitude(raw, 10)

        return None

    async def read_voltage(self) -> int | None:
        # Voltage is 1 byte, unit 0.1V
        data, _ = await self._read(Memory.PRESENT_VOLTAGE, 1)
        if data:
            return data[0]
        return None

    async def read_temperature(self) -> int | None:
        data, _ = await self._read(Memory.PRESENT_TEMPERATURE, 1)
        if data:
            return data[0]
        return None

    async def read_status(self) -> dict:
        # Split reads to avoid reading gaps (undefined registers) which might return garbage or cause offsets

        # Block 1: 56-63 (Pos, Speed, Load, Volt, Temp)
        data_main, error_main = await self._read(Memory.PRESENT_POSITION_L, 8)

        # Block 2: 66 (Moving)
        data_moving, error_moving = await self._read(Memory.MOVING, 1)

        # Block 3: 69-70 (Current)
        data_current, error_current = await self._read(Memory.PRESENT_CURRENT_L, 2)

        result = {}
        # Union of errors (prioritize main)
        if error_main != -1:
            result["error"] = error_main
        elif error_moving != -1:
            result["error"] = error_moving
        elif error_current != -1:
            result["error"] = error_current

        if data_main and len(data_main) == 8:
            raw_pos = make_word(data_main[0], data_main[1], self.endian)
            raw_speed = make_word(data_main[2], data_main[3], self.endian)
            raw_load = make_word(data_main[4], data_main[5], self.endian)
            volt = data_main[6]
            temp = data_main[7]

            result.update(
                {
                    "position": raw_pos,
                    "speed": from_sign_magnitude(raw_speed, 15),
                    "speed_raw": raw_speed,
                    "load": from_sign_magnitude(raw_load, 10),
                    "voltage": volt,
                    "temperature": temp,
                }
            )

        if data_moving:
            result["moving"] = data_moving[0]

        if data_current and len(data_current) == 2:
            raw_current = make_word(data_current[0], data_current[1], self.endian)
            result["current"] = from_sign_magnitude(raw_current, 15)

        return result

    async def set_id(self, new_id: int) -> bool:
        """
        Change the ID of the servo.
        Note: This changes EPROM. Requires Unlock.
        """
        # Unlock EPROM
        await self._write(Memory.LOCK, [0])

        # Write new ID
        res = await self._write(Memory.ID, [new_id])

        # Lock EPROM
        await self._write(Memory.LOCK, [1])

        return res == 0  # or success check

    async def wait_for_stop(
        self,
        interval: float = 0.05,
        timeout: float = 5.0,
        blocked_threshold: int = 5,
        load_threshold: int = 100,
    ) -> str:
        """
        Wait until the servo stops moving.
        Returns reason: "reached", "blocked", "timeout"

        blocked_threshold: Minimal position change per second to consider moving.
                           If moving bit is set but position changes less than this, valid as blocked.
                           HOWEVER, simple approach: check if position changes.
        load_threshold: If load is above this value when stopping, consider it blocked.
        """
        import time

        # Give a small delay for the servo to update its Moving bit after a write command
        await asyncio.sleep(0.1)

        start_time = time.time()

        last_pos = -1
        blocked_counter = 0

        while (time.time() - start_time) < timeout:
            status = await self.read_status()
            if not status:
                await asyncio.sleep(interval)
                continue

            moving = status.get("moving", 1)  # Default to 1 (moving) if key missing
            current_pos = status.get("position", 0)
            current_load = status.get("load", 0)

            # If moving flag goes to 0, we stopped.
            # But did we reach target or hit an obstacle?
            if moving == 0:
                # If load is significant (e.g. > 50 or < -50), it means we are forcing against something
                # Or if error bit is set (like overload, though that's in error byte)
                if abs(current_load) > load_threshold:
                    logger.warning(f"Blocked: Stopped but high load ({current_load} > {load_threshold})")
                    return "blocked"
                return "reached"

            # Check for blocking while moving=1 (stalled but trying)
            # If position hasn't changed significantly for X steps while Moving is 1
            if abs(current_pos - last_pos) < blocked_threshold:
                blocked_counter += 1
            else:
                blocked_counter = 0
                last_pos = current_pos

            # If we haven't moved enough for N cycles (defines blocking sensitivity)
            # interval 0.05 * 10 = 0.5 sec
            if blocked_counter > 10:
                logger.warning(f"Blocked: Stalled at {current_pos} (stuck for 0.5s)")
                return "blocked"

            await asyncio.sleep(interval)

        return "timeout"
