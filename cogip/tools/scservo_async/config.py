import asyncio
from typing import Annotated

import typer

from cogip.scservo_async_sdk import SCServo
from . import logger
from .common import get_driver


def cmd_set_id(
    ctx: typer.Context,
    current_id: Annotated[int, typer.Argument(help="Current ID of the servo.")],
    new_id: Annotated[int, typer.Argument(help="New ID to assign.")],
):
    """
    Change the ID of a servo.
    """
    asyncio.run(async_set_id(ctx, current_id, new_id))


async def async_set_id(ctx: typer.Context, current_id: int, new_id: int):
    ctx_dict = ctx.ensure_object(dict)
    port = ctx_dict.get("port")
    baud_rate = ctx_dict.get("baud_rate")

    driver = await get_driver(port, baud_rate)
    try:
        servo = SCServo(driver, current_id, endian="big")
        logger.info(f"Changing ID from {current_id} to {new_id}...")

        # Note: SCServo.set_id handles EPROM locking/unlocking
        success = await servo.set_id(new_id)

        if success:
            logger.info(f"Success! ID changed to {new_id}.")
        else:
            logger.error("ID Change Failed (Servo did not acknowledge or returned error).")

    finally:
        await driver.close()
