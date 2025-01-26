import sys
import time
from typing import Annotated

import typer
from getch import getch

from cogip.scservo_sdk import COMM_SUCCESS
from . import logger
from .common import init_servo


def cmd_write(
    ctx: typer.Context,
    positions: Annotated[
        list[int] | None,
        typer.Argument(
            min=0,
            max=1000,
            help="Positions.",
            envvar="SCSERVO_WRITE_POSITIONS",
        ),
    ] = None,
    id: Annotated[
        int,
        typer.Option(
            "-i",
            "--id",
            help="ID of the servo.",
            envvar="SCSERVO_ID",
        ),
    ] = 1,
    speed: Annotated[
        int,
        typer.Option(
            "-s",
            "--speed",
            min=0,
            max=2400,
            help="Rotation speed.",
            envvar="SCSERVO_SPEED",
        ),
    ] = 2400,
    loop: Annotated[
        bool,
        typer.Option(
            "-l",
            "--loop",
            help="Loop over given positions.",
            envvar="SCSERVO_WRITE_LOOP",
        ),
    ] = False,
    delay: Annotated[
        float | None,
        typer.Option(
            "--delay",
            help="Delay between each position in seconds. Go to next position on keyboard input if None",
            envvar="SCSERVO_WRITE_DELAY",
        ),
    ] = None,
):
    ctx_dict = ctx.ensure_object(dict)
    port = ctx_dict.get("port")
    baud_rate = ctx_dict.get("baud_rate")
    if positions is None:
        positions = [100, 200, 300]  # Default positions if no arguments are passed

    port_handler, packet_handler = init_servo(port, baud_rate)

    logger.info("Set Servo mode")
    result, error = packet_handler.ServoMode(id)
    if result != COMM_SUCCESS:
        logger.error(packet_handler.getTxRxResult(result))
        sys.exit(1)
    if error != 0:
        logger.warning(packet_handler.getRxPacketError(error))

    exit = False
    last = -1
    while not exit:
        for position in positions:
            if position == last:
                continue
            last = position

            # Write SC Servo target position/speed
            logger.info(f"Set position {position}")
            result, error = packet_handler.WritePos(id, position, 0, speed)
            if result != COMM_SUCCESS:
                logger.error(packet_handler.getTxRxResult(result))
                sys.exit(1)
            if error != 0:
                logger.warning(packet_handler.getRxPacketError(error))

            while True:
                # Read SC Servo current position
                current_position, current_speed, result, _ = packet_handler.ReadPosSpeed(id)
                if result != COMM_SUCCESS:
                    logger.error(packet_handler.getTxRxResult(result))
                    sys.exit(1)

                # Read SC Servo moving status
                moving, result, _ = packet_handler.ReadMoving(id)
                if result != COMM_SUCCESS:
                    logger.error(packet_handler.getTxRxResult(result))
                    sys.exit(1)
                logger.info(f"Target={position} Current={current_position} Speed={current_speed}")

                if not moving:
                    break

            if len(positions) == 1:
                break

            if delay is None:
                print("Press any key to continue (or press ESC to exit) ")
                if getch() == chr(0x1B):
                    exit = True
                    break
            else:
                time.sleep(delay)

        if not loop or len(positions) == 1:
            break

        # Continue in reverse order
        positions.reverse()

    # Close port
    port_handler.closePort()
