import asyncio
from typing import Annotated

import typer

from cogip.scservo_async_sdk import SCServo, ServoError
from . import logger
from .common import get_driver


def cmd_read(
    ctx: typer.Context,
    id: Annotated[int, typer.Argument(help="ID of the servo.")],
):
    asyncio.run(async_read(ctx, id))


async def async_read(ctx: typer.Context, id: int):
    ctx_dict = ctx.ensure_object(dict)
    port = ctx_dict.get("port")
    baud_rate = ctx_dict.get("baud_rate")

    driver = await get_driver(port, baud_rate)
    try:
        servo = SCServo(driver, id)

        status = await servo.read_status()
        if status:
            logger.info(f"[ID:{id:03d}] Status:")
            for k, v in status.items():
                if k == "error" and isinstance(v, int):
                    try:
                        err_flags = ServoError(v)
                        errors = [e.name for e in ServoError if e in err_flags]
                        logger.info(f"  {k}: {v} ({', '.join(errors)})")
                    except Exception:
                        logger.info(f"  {k}: {v}")
                else:
                    logger.info(f"  {k}: {v}")
        else:
            logger.error(f"[ID:{id:03d}] Failed to read status")

    finally:
        await driver.close()
