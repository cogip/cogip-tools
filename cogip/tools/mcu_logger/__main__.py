#!/usr/bin/env python3
from pathlib import Path
from typing import Annotated

import serial
import typer

from . import logger


def main_opt(
    port: Annotated[
        Path,
        typer.Option(
            "-p",
            "--port",
            help="Serial port connected to the STM32 running mcu-firmware",
            envvar="MCU_LOGGER_PORT",
        ),
    ],
    baud_rate: Annotated[
        int,
        typer.Option(
            "-b",
            "--baud-rate",
            help="Baud rate.",
            envvar="MCU_LOGGER_BAUD_RATE",
        ),
    ] = 115200,
):
    ser = serial.Serial(str(port), baud_rate)

    try:
        while True:
            line = ser.readline().decode("utf-8").strip()
            logger.info(line)
    except KeyboardInterrupt:
        return


def main():
    """
    This tools outputs from a serial port, like mcu-firmware outputs, and forward them to the logger.

    During installation of cogip-tools, a script called `cogip-mcu-logger`
    will be created using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
