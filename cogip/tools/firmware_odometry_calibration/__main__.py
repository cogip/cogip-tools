#!/usr/bin/env python3
"""
CLI entry point for the Odometry Calibration tool.

Provides a command-line interface to calibrate robot odometry parameters
by communicating with the firmware via SocketIO through cogip-server.
"""

import asyncio
import logging
from pathlib import Path
from typing import Annotated

import typer
import yaml

from cogip.models import FirmwareParametersGroup
from cogip.tools.firmware_odometry_calibration import logger
from cogip.tools.firmware_odometry_calibration.odometry_calibration import OdometryCalibration


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

    # Load bundled parameters definition YAML
    params_path = Path(__file__).with_name("odometry_parameters.yaml")
    parameters_data = yaml.safe_load(params_path.read_text())

    parameters_group = FirmwareParametersGroup.model_validate(parameters_data["parameters"])

    # Run calibration
    calibration = OdometryCalibration(server_url, parameters_group)
    asyncio.run(calibration.run())


def main():
    """
    Run odometry calibration tool.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-odometry-calibration` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
