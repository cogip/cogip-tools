import asyncio
from typing import Annotated

import typer

from cogip.scservo_async_sdk import SCServo
from . import logger
from .common import get_driver


def cmd_write(
    ctx: typer.Context,
    id: Annotated[int, typer.Argument(help="ID of the servo.")],
    position: Annotated[int, typer.Argument(help="Target position.")],
    time: Annotated[int, typer.Option("-t", "--time", min=0, max=9999, help="Time to reach position in ms.")] = 0,
    speed: Annotated[int, typer.Option("-s", "--speed", min=0, max=1000, help="Speed to reach position.")] = 0,
    wait: Annotated[bool, typer.Option("-w", "--wait", help="Wait for the move to complete.")] = False,
):
    asyncio.run(async_write(ctx, id, position, time, speed, wait))


async def async_write(ctx: typer.Context, id: int, position: int, time: int, speed: int, wait_move: bool):
    ctx_dict = ctx.ensure_object(dict)
    port = ctx_dict.get("port")
    baud_rate = ctx_dict.get("baud_rate")

    driver = await get_driver(port, baud_rate)
    try:
        servo = SCServo(driver, id, endian="big")
        logger.info(f"Writing Pos {position} to servo {id} (Time={time}, Speed={speed})...")
        success = await servo.set_position(position, time, speed)

        if success:
            logger.info(f"[ID:{id:03d}] Write Success")
            if wait_move:
                logger.info("Waiting for stop...")
                res = await servo.wait_for_stop()
                logger.info(f"Wait Result: {res}")

                if res == "blocked":
                    # Smart holding: read where we actually stopped and set it as target
                    # This releases the high current load while keeping the object gripped
                    current_pos = await servo.read_position()
                    if current_pos is not None:
                        logger.warning(
                            f"[ID:{id:03d}] Obstacle detected at {current_pos}. Holding position to prevent overload."
                        )
                        await servo.set_position(current_pos)
        else:
            logger.error(f"[ID:{id:03d}] Write Failed")

    finally:
        await driver.close()
