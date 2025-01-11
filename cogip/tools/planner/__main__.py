#!/usr/bin/env python3
import asyncio
import logging
from pathlib import Path
from typing import Annotated, Optional

import typer
from watchfiles import PythonFilter, run_process

from . import logger
from .planner import Planner


def changes_callback(changes):
    logger.info(f"Changes detected: {changes}")


def run(*args, **kwargs) -> None:
    planner = Planner(*args, **kwargs)
    asyncio.run(planner.connect())


def main_opt(
    id: Annotated[
        int,
        typer.Option(
            "-i",
            "--id",
            min=1,
            max=9,
            help="Robot ID.",
            envvar=["ROBOT_ID"],
        ),
    ],
    server_url: Annotated[
        Optional[str],  # noqa
        typer.Option(
            help="Socket.IO Server URL",
            envvar="COGIP_SOCKETIO_SERVER_URL",
        ),
    ] = None,
    robot_width: Annotated[
        int,
        typer.Option(
            min=100,
            max=1000,
            help="Width of the robot (in mm)",
            envvar="PLANNER_ROBOT_WIDTH",
        ),
    ] = 295,
    robot_length: Annotated[
        int,
        typer.Option(
            min=100,
            max=1000,
            help="Length of the robot (in mm)",
            envvar="PLANNER_ROBOT_LENGTH",
        ),
    ] = 295,
    obstacle_radius: Annotated[
        int,
        typer.Option(
            min=50,
            max=500,
            help="Radius of a dynamic obstacle (in mm)",
            envvar="PLANNER_OBSTACLE_RADIUS",
        ),
    ] = 150,
    obstacle_bb_margin: Annotated[
        float,
        typer.Option(
            min=0,
            max=1,
            help="Obstacle bounding box margin in percent of the radius",
            envvar="PLANNER_OBSTACLE_BB_MARGIN",
        ),
    ] = 0.2,
    obstacle_bb_vertices: Annotated[
        int,
        typer.Option(
            min=3,
            max=20,
            help="Number of obstacle bounding box vertices",
            envvar="PLANNER_OBSTACLE_BB_VERTICES",
        ),
    ] = 6,
    max_distance: Annotated[
        int,
        typer.Option(
            min=0,
            max=4000,
            help="Maximum distance to take avoidance points into account (mm)",
            envvar=["COGIP_MAX_DISTANCE", "PLANNER_MAX_DISTANCE"],
        ),
    ] = 2500,
    obstacle_updater_interval: Annotated[
        float,
        typer.Option(
            min=0.05,
            max=2.0,
            help="Interval between each obstacles list update (seconds)",
            envvar="PLANNER_OBSTACLE_UPDATER_INTERVAL",
        ),
    ] = 0.2,
    path_refresh_interval: Annotated[
        float,
        typer.Option(
            min=0.1,
            max=2.0,
            help="Interval between each update of robot paths (in seconds)",
            envvar="PLANNER_PATH_REFRESH_INTERVAL",
        ),
    ] = 0.2,
    plot: Annotated[
        bool,
        typer.Option(
            "-p",
            "--plot",
            help="Display avoidance graph in realtime",
            envvar=["PLANNER_PLOT"],
        ),
    ] = False,
    starter_pin: Annotated[
        Optional[int],  # noqa
        typer.Option(
            help="GPIO pin connected to the starter",
            envvar="PLANNER_STARTER_PIN",
        ),
    ] = None,
    oled_bus: Annotated[
        Optional[int],  # noqa
        typer.Option(
            "-op",
            "--oled-bus",
            help="PAMI OLED display i2c bus (integer, ex: 3)",
            envvar="PLANNER_OLED_BUS",
        ),
    ] = None,
    oled_address: Annotated[
        Optional[int],  # noqa
        typer.Option(
            "-oa",
            "--oled-address",
            parser=lambda value: int(value, 16),
            help="PAMI OLED display i2c address (hex, ex: 0x3C)",
            envvar="PLANNER_OLED_ADDRESS",
        ),
    ] = None,
    reload: Annotated[
        bool,
        typer.Option(
            "-r",
            "--reload",
            help="Reload app on source file changes",
            envvar=["COGIP_RELOAD", "PLANNER_RELOAD"],
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            "-d",
            "--debug",
            help="Turn on debug messages",
            envvar=["COGIP_DEBUG", "PLANNER_DEBUG"],
        ),
    ] = False,
):
    if debug:
        logger.setLevel(logging.DEBUG)

    if not server_url:
        server_url = f"http://localhost:809{id}"

    args = (
        id,
        server_url,
        robot_width,
        robot_length,
        obstacle_radius,
        obstacle_bb_margin,
        obstacle_bb_vertices,
        max_distance,
        obstacle_updater_interval,
        path_refresh_interval,
        plot,
        starter_pin,
        oled_bus,
        oled_address,
        debug,
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
    Launch COGIP Game Planner.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-planner` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
