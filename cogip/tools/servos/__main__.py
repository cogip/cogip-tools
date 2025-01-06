#!/usr/bin/env python3
import logging
from pathlib import Path
from typing import Annotated, Optional

import typer
from watchfiles import PythonFilter, run_process

from . import logger
from .detector import Detector


def changes_callback(changes):
    logger.info(f"Changes detected: {changes}")


def run(*args, **kwargs) -> None:
    detector = Detector(*args, **kwargs)
    detector.connect()


def main_opt(
    server_url: Annotated[
        Optional[str],  # noqa
        typer.Option(
            help="Socket.IO Server URL",
            envvar="COGIP_SOCKETIO_SERVER_URL",
        ),
    ] = None,
    id: Annotated[
        int,
        typer.Option(
            "-i",
            "--id",
            min=1,
            help="Robot ID.",
            envvar=["ROBOT_ID", "DETECTOR_ID"],
        ),
    ] = 1,
    lidar_port: Annotated[
        Optional[Path],  # noqa
        typer.Option(
            "-p",
            "--lidar-port",
            help="Serial port connected to the Lidar",
            envvar="DETECTOR_LIDAR_PORT",
        ),
    ] = None,
    min_distance: Annotated[
        int,
        typer.Option(
            min=0,
            max=1000,
            help="Minimum distance to detect an obstacle (mm)",
            envvar="DETECTOR_MIN_DISTANCE",
        ),
    ] = 150,
    max_distance: Annotated[
        int,
        typer.Option(
            min=0,
            max=4000,
            help="Maximum distance to detect an obstacle (mm)",
            envvar=["COGIP_MAX_DISTANCE", "DETECTOR_MAX_DISTANCE"],
        ),
    ] = 2500,
    beacon_radius: Annotated[
        int,
        typer.Option(
            min=10,
            max=150,
            help="Radius of the opponent beacon support (a cylinder of 70mm diameter to a cube of 100mm width)",
            envvar="DETECTOR_BEACON_RADIUS",
        ),
    ] = 35,
    refresh_interval: Annotated[
        float,
        typer.Option(
            min=0.1,
            max=2.0,
            help="Interval between each update of the obstacle list (in seconds)",
            envvar="DETECTOR_REFRESH_INTERVAL",
        ),
    ] = 0.2,
    reload: Annotated[
        bool,
        typer.Option(
            "-r",
            "--reload",
            help="Reload app on source file changes.",
            envvar=["COGIP_RELOAD", "DETECTOR_RELOAD"],
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            "-d",
            "--debug",
            help="Turn on debug messages.",
            envvar=["COGIP_DEBUG", "DETECTOR_DEBUG"],
        ),
    ] = False,
):
    if debug:
        logger.setLevel(logging.DEBUG)

    if not server_url:
        server_url = f"http://localhost:809{id}"

    args = (
        server_url,
        lidar_port,
        min_distance,
        max_distance,
        beacon_radius,
        refresh_interval,
    )

    if reload:
        watch_dir = Path(__file__).parent.parent.parent
        run_process(
            watch_dir,
            target=run,
            args=args,
            callback=changes_callback,
            watch_filter=PythonFilter(),
            debug=False,
        )
    else:
        run(*args)


def main():
    """
    Launch COGIP Obstacle Detector.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-detector` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
