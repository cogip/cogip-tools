import asyncio
from typing import Annotated

import typer

from cogip.scservo_async_sdk import SCServo
from . import logger
from .common import get_driver

# SCS series memory map: addresses < EEPROM_END are EEPROM (need LOCK=0 to
# write), addresses >= EEPROM_END are SRAM (writable directly). Register 48
# is the LOCK itself (SRAM), so this bound also lets us treat explicit
# LOCK writes without recursing.
EEPROM_END = 40


def cmd_write_reg(
    ctx: typer.Context,
    id: Annotated[int, typer.Argument(help="ID of the servo.")],
    address: Annotated[int, typer.Argument(min=0, max=255, help="Register address to write to.")],
    bytes_: Annotated[list[int], typer.Argument(help="One or more byte values to write (each 0-255).")],
):
    """
    Write raw bytes to a servo register.

    Useful for advanced configuration not covered by the high-level commands,
    e.g. Max Torque (addr 16-17, big-endian, range 0-1000), Unloading
    Conditions (addr 19), LOCK (addr 48).

    EEPROM is unlocked and re-locked automatically when the target address
    falls inside the EEPROM range (addr < 40). SRAM addresses (addr >= 40)
    are written directly, so explicit writes to the LOCK register at 48
    keep their literal effect.

    Multi-byte writes follow the SC protocol big-endian convention: pass the
    high byte first.

    Example: set Max Torque to 600 (60%) on servo 31 in one shot:
        write-reg 31 16 2 88   # 600 = 0x0258 -> high=0x02, low=0x58
    """
    asyncio.run(async_write_reg(ctx, id, address, bytes_))


async def async_write_reg(ctx: typer.Context, id: int, address: int, bytes_: list[int]):
    ctx_dict = ctx.ensure_object(dict)
    port = ctx_dict.get("port")
    baud_rate = ctx_dict.get("baud_rate")

    if not bytes_:
        logger.error("At least one byte value is required.")
        return

    if any(b < 0 or b > 255 for b in bytes_):
        logger.error("Each byte value must be in 0-255.")
        return

    is_eeprom = address < EEPROM_END

    driver = await get_driver(port, baud_rate)
    try:
        servo = SCServo(driver, id, endian="big")

        if is_eeprom:
            logger.info(f"[ID:{id:03d}] EEPROM target, unlocking (LOCK=0)...")
            if await servo._write(48, [0]) is None:
                logger.error(f"[ID:{id:03d}] Failed to unlock EEPROM, aborting")
                return

        try:
            logger.info(f"[ID:{id:03d}] Writing {bytes_} to register {address}...")
            if await servo._write(address, list(bytes_)) is None:
                logger.error(f"[ID:{id:03d}] Write Failed (no status packet)")
            else:
                logger.info(f"[ID:{id:03d}] Write Success")
        finally:
            if is_eeprom:
                logger.info(f"[ID:{id:03d}] Re-locking EEPROM (LOCK=1)...")
                if await servo._write(48, [1]) is None:
                    logger.error(f"[ID:{id:03d}] Failed to re-lock EEPROM")
    finally:
        await driver.close()
