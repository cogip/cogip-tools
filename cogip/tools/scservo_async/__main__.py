#!/usr/bin/env python3
import logging
from pathlib import Path
from typing import Annotated

import typer

from . import logger
from .action import cmd_action
from .config import cmd_set_id
from .ping import cmd_ping
from .read import cmd_read
from .reg_write import cmd_reg_write
from .torque import cmd_torque
from .wait import cmd_wait
from .write import cmd_write

app = typer.Typer()
app.command(name="ping")(cmd_ping)
app.command(name="read")(cmd_read)
app.command(name="write")(cmd_write)
app.command(name="reg_write")(cmd_reg_write)
app.command(name="action")(cmd_action)
app.command(name="torque")(cmd_torque)
app.command(name="wait")(cmd_wait)
app.command(name="set-id")(cmd_set_id)


@app.callback()
def common(
    ctx: typer.Context,
    port: Annotated[
        Path,
        typer.Option(
            "-p",
            "--port",
            help="Serial port.",
            envvar="SCSERVO_PORT",
        ),
    ] = Path("/dev/ttyUSB0"),
    baud_rate: Annotated[
        int,
        typer.Option(
            "-b",
            "--baud-rate",
            help="Baud rate (usually 921600 or 1000000).",
            envvar="SCSERVO_BAUD_RATE",
        ),
    ] = 1000000,
    debug: Annotated[
        bool,
        typer.Option(
            "-d",
            "--debug",
            help="Turn on debug messages",
            envvar="SCSERVO_DEBUG",
        ),
    ] = False,
):
    ctx_dict = ctx.ensure_object(dict)
    ctx_dict["debug"] = debug
    ctx_dict["port"] = port
    ctx_dict["baud_rate"] = baud_rate

    if debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger("cogip.scservo_async_sdk").setLevel(logging.DEBUG)


def main():
    """
    Launch COGIP SCServo Async Tools.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-scservo-async` script using this function as entrypoint.
    """
    app()


if __name__ == "__main__":
    main()
