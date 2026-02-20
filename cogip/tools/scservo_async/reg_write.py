import asyncio
from typing import Annotated

import typer

from cogip.scservo_async_sdk import SCServo
from . import logger
from .common import get_driver


def cmd_reg_write(
    ctx: typer.Context,
    id: Annotated[int, typer.Argument(help="ID of the servo.")],
    position: Annotated[int, typer.Argument(help="Target position.")],
    time: Annotated[int, typer.Option("-t", "--time", min=0, max=9999, help="Time to reach position in ms.")] = 0,
    speed: Annotated[int, typer.Option("-s", "--speed", min=0, max=1000, help="Speed to reach position.")] = 0,
):
    asyncio.run(async_reg_write(ctx, id, position, time, speed))


async def async_reg_write(ctx: typer.Context, id: int, position: int, time: int, speed: int):
    ctx_dict = ctx.ensure_object(dict)
    port = ctx_dict.get("port")
    baud_rate = ctx_dict.get("baud_rate")

    driver = await get_driver(port, baud_rate)
    try:
        servo = SCServo(driver, id)
        logger.info(f"RegWriting Pos {position} to servo {id} (Time={time}, Speed={speed})...")
        res = await servo.reg_write_position(position, time, speed)

        if res == 0:
            logger.info(f"[ID:{id:03d}] RegWrite Success")
        elif res == -1:
            logger.error(f"[ID:{id:03d}] RegWrite Failed (No response)")
        else:
            logger.warning(f"[ID:{id:03d}] RegWrite Success with Error: {res}")

    finally:
        await driver.close()
