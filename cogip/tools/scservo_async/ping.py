import asyncio
from typing import Annotated

import typer

from cogip.scservo_async_sdk import SCServo
from . import logger
from .common import get_driver


def cmd_ping(
    ctx: typer.Context,
    id: Annotated[int, typer.Argument(help="ID of the servo.")],
):
    asyncio.run(async_ping(ctx, id))


async def async_ping(ctx: typer.Context, id: int):
    ctx_dict = ctx.ensure_object(dict)
    port = ctx_dict.get("port")
    baud_rate = ctx_dict.get("baud_rate")

    driver = await get_driver(port, baud_rate)
    try:
        servo = SCServo(driver, id)
        logger.info(f"Pinging servo {id} on {port}@{baud_rate}...")
        res = await servo.ping()
        if res == 0:
            logger.info(f"[ID:{id:03d}] Ping Success")
        elif res == -1:
            logger.error(f"[ID:{id:03d}] Ping Failed (No Response)")
        else:
            logger.warning(f"[ID:{id:03d}] Ping Success with Error: {res}")
    finally:
        await driver.close()
