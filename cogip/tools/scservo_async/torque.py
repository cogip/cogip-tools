import asyncio
from typing import Annotated

import typer

from cogip.scservo_async_sdk import SCServo, SCServoDriver


async def torque(
    ctx: typer.Context,
    id: int,
    enable: bool,
):
    ctx_dict = ctx.ensure_object(dict)
    port = ctx_dict.get("port")
    baud_rate = ctx_dict.get("baud_rate")

    async with SCServoDriver(str(port), baud_rate) as driver:
        # Defaults to big endian as per our previous discovery for SC series
        result = await SCServo(driver, id, endian="big").enable_torque(enable)
        if result == 0:
            print(f"Torque {'enabled' if enable else 'disabled'} for ID {id}: Success")
        elif result > 0:
            print(f"Torque {'enabled' if enable else 'disabled'} for ID {id}: Warning (Status: {result})")
        else:
            print(f"Torque {'enabled' if enable else 'disabled'} for ID {id}: Failed")


def cmd_torque(
    id: Annotated[int, typer.Argument(help="Servo ID")],
    enable: Annotated[bool, typer.Argument(help="Enable (True/1/on) or Disable (False/0/off) torque")],
    ctx: typer.Context,
):
    """
    Enable or disable torque for a specific servo.
    """
    asyncio.run(torque(ctx, id, enable))
