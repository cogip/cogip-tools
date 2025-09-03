#!/usr/bin/env python3
import asyncio
import logging
import os
from pathlib import Path
from typing import Annotated, Optional

import typer
from watchfiles import PythonFilter, run_process

from . import logger
from .actions import Strategy
from .avoidance.avoidance import AvoidanceStrategy
from .planner import Planner
from .positions import StartPosition
from .properties import properties_schema
from .table import TableEnum


def changes_callback(changes):
    logger.info(f"Changes detected: {changes}")


def run(*args, **kwargs) -> None:
    planner = Planner(*args, **kwargs)
    asyncio.run(planner.connect())


properties = properties_schema["properties"]


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
            min=properties["robot_width"]["minimum"],
            max=properties["robot_width"]["maximum"],
            help=properties["robot_width"]["description"],
            envvar="PLANNER_ROBOT_WIDTH",
        ),
    ] = properties["robot_width"]["default"],
    robot_length: Annotated[
        int,
        typer.Option(
            min=properties["robot_length"]["minimum"],
            max=properties["robot_length"]["maximum"],
            help=properties["robot_length"]["description"],
            envvar="PLANNER_ROBOT_LENGTH",
        ),
    ] = properties["robot_length"]["default"],
    obstacle_radius: Annotated[
        int,
        typer.Option(
            min=properties["obstacle_radius"]["minimum"],
            max=properties["obstacle_radius"]["maximum"],
            help=properties["obstacle_radius"]["description"],
            envvar="PLANNER_OBSTACLE_RADIUS",
        ),
    ] = properties["obstacle_radius"]["default"],
    obstacle_bb_margin: Annotated[
        float,
        typer.Option(
            min=properties["obstacle_bb_margin"]["minimum"],
            max=properties["obstacle_bb_margin"]["maximum"],
            help=properties["obstacle_bb_margin"]["description"],
            envvar="PLANNER_OBSTACLE_BB_MARGIN",
        ),
    ] = properties["obstacle_bb_margin"]["default"],
    obstacle_bb_vertices: Annotated[
        int,
        typer.Option(
            min=properties["obstacle_bb_vertices"]["minimum"],
            max=properties["obstacle_bb_vertices"]["maximum"],
            help=properties["obstacle_bb_vertices"]["description"],
            envvar="PLANNER_OBSTACLE_BB_VERTICES",
        ),
    ] = properties["obstacle_bb_vertices"]["default"],
    obstacle_updater_interval: Annotated[
        float,
        typer.Option(
            min=properties["obstacle_updater_interval"]["minimum"],
            max=properties["obstacle_updater_interval"]["maximum"],
            help=properties["obstacle_updater_interval"]["description"],
            envvar="PLANNER_OBSTACLE_UPDATER_INTERVAL",
        ),
    ] = properties["obstacle_updater_interval"]["default"],
    path_refresh_interval: Annotated[
        float,
        typer.Option(
            min=properties["path_refresh_interval"]["minimum"],
            max=properties["path_refresh_interval"]["maximum"],
            help=properties["path_refresh_interval"]["description"],
            envvar="PLANNER_PATH_REFRESH_INTERVAL",
        ),
    ] = properties["path_refresh_interval"]["default"],
    starter_pin: Annotated[
        Optional[int],  # noqa
        typer.Option(
            help="GPIO pin connected to the starter",
            envvar="PLANNER_STARTER_PIN",
        ),
    ] = None,
    led_red_pin: Annotated[
        Optional[int],  # noqa
        typer.Option(
            "-lr",
            "--led-red-pin",
            help="GPIO pin connected to the red LED",
            envvar="PLANNER_LED_RED_PIN",
        ),
    ] = None,
    led_green_pin: Annotated[
        Optional[int],  # noqa
        typer.Option(
            "-lg",
            "--led-green-pin",
            help="GPIO pin connected to the green LED",
            envvar="PLANNER_LED_GREEN_PIN",
        ),
    ] = None,
    led_blue_pin: Annotated[
        Optional[int],  # noqa
        typer.Option(
            "-lb",
            "--led-blue-pin",
            help="GPIO pin connected to the blue LED",
            envvar="PLANNER_LED_BLUE_PIN",
        ),
    ] = None,
    flag_motor_pin: Annotated[
        Optional[int],  # noqa
        typer.Option(
            "-fm",
            "--flag-motor-pin",
            help="GPIO pin connected to flag motor",
            envvar="PLANNER_FLAG_MOTOR_PIN",
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
    bypass_detector: Annotated[
        bool,
        typer.Option(
            "-bd",
            "--bypass-detector",
            help=properties["bypass_detector"]["description"],
            envvar=["PLANNER_BYPASS_DETECTOR"],
        ),
    ] = properties["bypass_detector"]["default"],
    scservos_port: Annotated[
        Path | None,
        typer.Option(
            "-sp",
            "--scservos-port",
            help="SC Servos serial port.",
            envvar="PLANNER_SCSERVOS_PORT",
        ),
    ] = None,
    scservos_baud_rate: Annotated[
        int,
        typer.Option(
            "-sb",
            "--scservos-baud-rate",
            help="SC Servos baud rate (usually 921600 or 1000000).",
            envvar="PLANNER_SCSERVOS_BAUD_RATE",
        ),
    ] = 921600,
    disable_fixed_obstacles: Annotated[
        bool,
        typer.Option(
            "-df",
            "--disable-fixed-obstacles",
            help=properties["disable_fixed_obstacles"]["description"],
            envvar=["PLANNER_DISABLE_FIXED_OBSTACLES"],
        ),
    ] = properties["disable_fixed_obstacles"]["default"],
    table: Annotated[
        TableEnum,
        typer.Option(
            "-t",
            "--table",
            help="Default table on startup",
            envvar="PLANNER_TABLE",
        ),
    ] = TableEnum.Game.name,
    strategy: Annotated[
        Strategy,
        typer.Option(
            "-s",
            "--strategy",
            help="Default strategy on startup",
            envvar="PLANNER_STRATEGY",
        ),
    ] = Strategy.TestVisitStartingAreas.name,
    start_position: Annotated[
        StartPosition,
        typer.Option(
            "-p",
            "--start-position",
            help="Default start position on startup",
            envvar="PLANNER_START_POSITION",
        ),
    ] = StartPosition.Bottom.name,
    avoidance_strategy: Annotated[
        AvoidanceStrategy,
        typer.Option(
            "-a",
            "--avoidance-strategy",
            help="Default avoidance strategy on startup",
            envvar="PLANNER_AVOIDANCE_STRATEGY",
        ),
    ] = AvoidanceStrategy.AvoidanceCpp.name,
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

    # Make sure robot ID is also available as environment variable for context creation
    os.environ["ROBOT_ID"] = str(id)

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
        obstacle_updater_interval,
        path_refresh_interval,
        starter_pin,
        led_red_pin,
        led_green_pin,
        led_blue_pin,
        flag_motor_pin,
        oled_bus,
        oled_address,
        bypass_detector,
        scservos_port,
        scservos_baud_rate,
        disable_fixed_obstacles,
        table,
        strategy,
        start_position,
        avoidance_strategy,
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
