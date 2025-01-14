#!/usr/bin/env python3
import asyncio
import logging
import os
from pathlib import Path
from typing import Annotated

import typer
import uvicorn

from . import logger


def main_opt(
    max_robots: Annotated[
        int,
        typer.Option(
            min=1,
            help="Maximum number of robots to detect (from 1 to max)",
            envvar="SERVER_BEACON_MAX_ROBOTS",
        ),
    ] = 4,
    record_dir: Annotated[
        Path,
        typer.Option(
            help="Directory where games will be recorded",
            envvar="SERVER_BEACON_RECORD_DIR",
        ),
    ] = Path("/var/tmp/cogip"),
    reload: Annotated[
        bool,
        typer.Option(
            "-r",
            "--reload",
            help="Reload app on source file changes",
            envvar=["COGIP_RELOAD", "SERVER_BEACON_RELOAD"],
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            "-d",
            "--debug",
            help="Turn on debug messages",
            envvar=["COGIP_DEBUG", "SERVER_BEACON_DEBUG"],
        ),
    ] = False,
):
    if debug:
        logger.setLevel(logging.DEBUG)

    os.environ["SERVER_BEACON_MAX_ROBOTS"] = str(max_robots)
    os.environ["SERVER_BEACON_RECORD_DIR"] = str(record_dir)

    try:
        uvicorn.run(
            "cogip.tools.server_beacon.app:app",
            host="0.0.0.0",
            port=8090,
            workers=1,
            log_level="info" if debug else "warning",
            reload=reload,
        )
    except asyncio.CancelledError:
        pass


def main():
    """
    Launch COGIP SocketIO beacon server.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-server-beacon` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
