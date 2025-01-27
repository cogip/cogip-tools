import sys
from typing import Annotated

import typer
from getch import getch

from cogip.scservo_sdk import COMM_SUCCESS
from . import logger
from .common import init_servo


def cmd_wheel(
    ctx: typer.Context,
    id: Annotated[
        int,
        typer.Option(
            "-i",
            "--id",
            help="ID of the servo.",
            envvar="SCSERVO_ID",
        ),
    ] = 1,
):
    ctx_dict = ctx.ensure_object(dict)
    port = ctx_dict.get("port")
    baud_rate = ctx_dict.get("baud_rate")
    speeds = [500, 0, -500, 0]
    port_handler, packet_handler = init_servo(port, baud_rate)

    logger.info("Set PWM mode")
    result, error = packet_handler.PWMMode(id)
    if result != COMM_SUCCESS:
        logger.error(packet_handler.getTxRxResult(result))
        sys.exit(1)
    if error != 0:
        logger.warning(packet_handler.getRxPacketError(error))

    exit = False
    while not exit:
        for speed in speeds:
            # Set SC Servo PWM
            logger.info(f"Set PWM {speed}")
            result, error = packet_handler.WritePWM(id, speed)
            if result != COMM_SUCCESS:
                logger.error(packet_handler.getTxRxResult(result))
                sys.exit(1)

            print("Press any key to continue (or press ESC to exit) ")
            if getch() == chr(0x1B):
                exit = True
                break

    packet_handler.WritePWM(id, 0)

    # Close port
    port_handler.closePort()
