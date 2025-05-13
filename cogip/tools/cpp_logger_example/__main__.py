#!/usr/bin/env python3
import logging
from typing import Annotated

import typer

from cogip.cpp.examples.logger_example import emit_logs
from . import logger


def main_opt(
    debug: Annotated[
        bool,
        typer.Option(
            "-d",
            "--debug",
            help="Turn on debug messages.",
        ),
    ] = False,
):
    if debug:
        logger.setLevel(logging.DEBUG)

    logger.info("This is a log message from Python.")
    logger.debug("This is a debug message from Python.")
    logger.warning("This is a warning message from Python.")
    logger.error("This is an error message from Python.")
    emit_logs()


def main():
    """
    Example calling a C++ function that emits logs to a Python logger.

    During installation of cogip-tools, a script called `cogip-cpp-logger-example`
    will be created using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
