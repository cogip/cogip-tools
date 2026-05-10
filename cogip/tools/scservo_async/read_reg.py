import asyncio
from typing import Annotated

import typer

from cogip.scservo_async_sdk import SCServo
from . import logger
from .common import get_driver


def cmd_read_reg(
    ctx: typer.Context,
    id: Annotated[int, typer.Argument(help="ID of the servo.")],
    address: Annotated[int, typer.Argument(min=0, max=255, help="Register address to read from.")],
    length: Annotated[int, typer.Argument(min=1, max=64, help="Number of bytes to read.")] = 1,
):
    """
    Read raw bytes from a servo register.

    Useful to inspect EEPROM/SRAM fields not covered by the high-level
    commands, e.g. Max Torque (addr 16, length 2), Unloading Conditions
    (addr 19, length 1), LOCK (addr 48, length 1).

    Multi-byte fields follow the SC protocol big-endian convention: the
    first returned byte is the high byte. The output also prints the
    little-/big-endian word interpretation when length=2 to save you the
    mental arithmetic.
    """
    asyncio.run(async_read_reg(ctx, id, address, length))


async def async_read_reg(ctx: typer.Context, id: int, address: int, length: int):
    ctx_dict = ctx.ensure_object(dict)
    port = ctx_dict.get("port")
    baud_rate = ctx_dict.get("baud_rate")

    driver = await get_driver(port, baud_rate)
    try:
        servo = SCServo(driver, id, endian="big")
        logger.info(f"[ID:{id:03d}] Reading {length} byte(s) from register {address}...")
        data, status = await servo._read(address, length)
        if data is None:
            logger.error(f"[ID:{id:03d}] Read Failed (no status packet)")
            return
        bytes_repr = " ".join(f"0x{b:02X}" for b in data)
        logger.info(f"[ID:{id:03d}] {length} byte(s) @ addr {address}: {bytes_repr}")
        if length == 2:
            be = (data[0] << 8) | data[1]
            le = (data[1] << 8) | data[0]
            logger.info(f"[ID:{id:03d}]   word (big-endian)    = {be} (0x{be:04X})")
            logger.info(f"[ID:{id:03d}]   word (little-endian) = {le} (0x{le:04X})")
    finally:
        await driver.close()
