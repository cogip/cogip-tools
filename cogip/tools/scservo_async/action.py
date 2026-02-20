import asyncio
from typing import Annotated

import typer

from cogip.scservo_async_sdk import SCServo
from . import logger
from .common import get_driver


def cmd_action(
    ctx: typer.Context,
    id: Annotated[int, typer.Argument(help="ID of the servo (or 254 for Broadcast).")] = 254,
):
    asyncio.run(async_action(ctx, id))


async def async_action(ctx: typer.Context, id: int):
    ctx_dict = ctx.ensure_object(dict)
    port = ctx_dict.get("port")
    baud_rate = ctx_dict.get("baud_rate")

    driver = await get_driver(port, baud_rate)
    try:
        servo = SCServo(driver, id)
        logger.info(f"Sending Action to ID {id}...")
        res = await servo.action()
        if res == 0:
            logger.info("Action sent successfully")
        elif res == -1:
            # Broadcast often returns None/False because no response
            if id == 254:
                logger.info("Action broadcast sent (No response expected).")
            else:
                logger.error("Action failed (No response)")
        else:
            logger.warning(f"Action sent with Error: {res}")
    finally:
        await driver.close()
