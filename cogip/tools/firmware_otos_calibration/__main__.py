#!/usr/bin/env python3
"""
CLI entry point for the OTOS Calibration tool.

Provides a command-line interface to calibrate the SparkFun OTOS sensor
scalars through cogip-server (pose_order / pose_reached motion control
and firmware parameter manager).
"""

import asyncio
import logging
from pathlib import Path
from typing import Annotated

import typer
import yaml

from cogip.models import FirmwareParametersGroup
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

    params_path = Path(__file__).with_name("otos_parameters.yaml")
    parameters_data = yaml.safe_load(params_path.read_text())

    parameters_group = FirmwareParametersGroup.model_validate(parameters_data["parameters"])

    calibration = OTOSCalibration(server_url, parameters_group)
    asyncio.run(calibration.run())


def main():
    """Run OTOS calibration tool."""
    typer.run(main_opt)


if __name__ == "__main__":
    main()
