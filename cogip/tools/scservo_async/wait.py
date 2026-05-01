import asyncio
from typing import Annotated

import typer

from cogip.scservo_async_sdk import SCServo, SCServoDriver


async def wait(
    ctx: typer.Context,
    ids: list[int],
    timeout: float,
):
    ctx_dict = ctx.ensure_object(dict)
    port = ctx_dict.get("port")
    baud_rate = ctx_dict.get("baud_rate")

    async with SCServoDriver(str(port), baud_rate) as driver:
        tasks = []
        for id in ids:
            servo = SCServo(driver, id, endian="big")
            tasks.append(servo.wait_for_stop(timeout=timeout))

        results = await asyncio.gather(*tasks)

        for id, res in zip(ids, results):
            print(f"Servo {id}: {res}")


def cmd_wait(
    ids: Annotated[list[int], typer.Argument(help="List of Servo IDs to wait for")],
    ctx: typer.Context,
    timeout: Annotated[float, typer.Option("-t", "--timeout", help="Timeout in seconds")] = 5.0,
):
    """
    Wait for one or more servos to stop moving (reached target or blocked).
    """
    asyncio.run(wait(ctx, ids, timeout))
