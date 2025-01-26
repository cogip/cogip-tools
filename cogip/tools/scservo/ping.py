import sys
from typing import Annotated

import typer

from cogip.scservo_sdk import COMM_SUCCESS
from . import logger
from .common import init_servo


def cmd_ping(
    ctx: typer.Context,
    id: Annotated[
        int,
        typer.Argument(
            help="ID of the servo.",
            envvar="SCSERVO_ID",
        ),
    ],
):
    ctx_dict = ctx.ensure_object(dict)
    port = ctx_dict.get("port")
    baud_rate = ctx_dict.get("baud_rate")

    port_handler, packet_handler = init_servo(port, baud_rate)

    # Try to ping the servo, get model number.
    model_number, result, error = packet_handler.ping(id)
    if result != COMM_SUCCESS:
        logger.error(packet_handler.getTxRxResult(result))
        sys.exit(1)

    logger.info(f"[ID:{id:03d}] Ping succeeded. SC Servo model number: {model_number}")

    if error != 0:
        logger.warning(packet_handler.getRxPacketError(error))

    # Close port
    port_handler.closePort()
