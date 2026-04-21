#!/usr/bin/env python3
"""
CLI entry point for the OTOS Calibration tool.

Provides a command-line interface to calibrate the SparkFun OTOS sensor
scalars through cogip-server (pose_order / pose_reached motion control
and firmware parameter manager).
"""

import asyncio
import logging
from typing import Annotated

import typer

from cogip.tools.firmware_otos_calibration import logger
from cogip.tools.firmware_otos_calibration.otos_calibration import OTOSCalibration


def main_opt(
    *,
    server_url: Annotated[
        str | None,
        typer.Option(
            "-s",
            "--server-url",
            help="cogip-server URL",
            envvar="COGIP_SOCKETIO_SERVER_URL",
        ),
    ] = None,
    robot_id: Annotated[
        int,
        typer.Option(
            "-i",
            "--id",
            min=1,
            help="Robot ID.",
            envvar=["ROBOT_ID"],
        ),
    ] = 1,
    debug: Annotated[
        bool,
        typer.Option(
            "-d",
            "--debug",
            help="Turn on debug messages",
            envvar="CALIBRATION_DEBUG",
        ),
    ] = False,
):
    if debug:
        logger.setLevel(logging.DEBUG)

    if not server_url:
        server_url = f"http://localhost:809{robot_id}"

    # Parameter catalog comes from the firmware announce stream at connect
    # time, so no local YAML is needed.
    calibration = OTOSCalibration(server_url)
    asyncio.run(calibration.run())


def main():
    """Run OTOS calibration tool."""
    typer.run(main_opt)


if __name__ == "__main__":
    main()
