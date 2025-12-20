#!/usr/bin/env python3
"""
CLI entry point for the PID Calibration tool.

Provides a command-line interface to calibrate robot PID parameters
by communicating with the firmware via SocketIO through cogip-server.
"""

from __future__ import annotations
import asyncio
import logging
import os
from importlib.resources import files
from typing import Annotated

import typer
import yaml

from cogip.models.firmware_parameter import FirmwareParametersGroup
from cogip.tools.firmware_pid_calibration import logger
from cogip.tools.firmware_pid_calibration.pid_calibration import PidCalibration


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
    graph: Annotated[
        bool,
        typer.Option(
            "-g",
            "--graph",
            help="Show real-time telemetry graph window",
        ),
    ] = False,
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
        host = os.environ.get("COGIP_SERVER_HOST", "localhost")
        server_url = f"http://{host}:809{robot_id}"

    # Load bundled parameters definition YAML
    params_resource = files("cogip.tools.firmware_pid_calibration").joinpath("pid_parameters.yaml")
    with params_resource.open() as f:
        parameters_data = yaml.safe_load(f)

    parameters_group = FirmwareParametersGroup.model_validate(parameters_data["parameters"])

    if graph:
        # Use qasync to integrate Qt with asyncio
        import sys

        from PySide6.QtWidgets import QApplication
        from qasync import QEventLoop

        # Check if display is available, use offscreen fallback if not
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            logger.warning("No display available, using offscreen Qt platform")
            os.environ["QT_QPA_PLATFORM"] = "offscreen"

        app = QApplication(sys.argv)

        # Create calibration with graph enabled
        calibration = PidCalibration(server_url, parameters_group, enable_graph=True)

        # Run with Qt event loop integration
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(calibration.run())
        except (asyncio.CancelledError, RuntimeError):
            # Suppress errors from abrupt shutdown (window close, Ctrl+C)
            pass
        finally:
            # Clean up Qt/pyqtgraph resources
            import pyqtgraph as pg

            if calibration._graph_widget:
                calibration._graph_widget.close()
                calibration._graph_widget.deleteLater()
            app.processEvents()
            pg.exit()  # Clean up pyqtgraph threads
    else:
        # Standard asyncio without Qt
        calibration = PidCalibration(server_url, parameters_group, enable_graph=False)
        asyncio.run(calibration.run())


def main():
    """
    Run PID calibration tool.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-pid-calibration` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
