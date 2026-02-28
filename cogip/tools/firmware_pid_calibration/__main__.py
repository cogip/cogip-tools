#!/usr/bin/env python3
"""
CLI entry point for the PID Calibration tool.

Provides a command-line interface to calibrate robot PID parameters
by communicating with the firmware via SocketIO through cogip-server.

Architecture:
    - Main thread: Qt event loop (QApplication.exec()) for telemetry graph
    - Background thread: asyncio event loop for SocketIO + calibration logic
    - TelemetryGraphBridge: Qt signals for thread-safe asyncio -> Qt communication
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from threading import Thread
from typing import Annotated

import typer
import yaml
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication

from cogip.models import FirmwareParametersGroup
from cogip.tools.firmware_pid_calibration import logger
from cogip.tools.firmware_pid_calibration.pid_calibration import PidCalibration
from cogip.tools.firmware_telemetry.graph import create_telemetry_graph


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
    params_path = Path(__file__).with_name("pid_parameters.yaml")
    parameters_data = yaml.safe_load(params_path.read_text())
    parameters_group = FirmwareParametersGroup.model_validate(parameters_data["parameters"])

    # Create Qt application (must be in main thread)
    app = QApplication(sys.argv)

    # Create telemetry graph widget + bridge
    graph_config_path = Path(__file__).with_name("pid_graph_pose_layout.yaml")
    widget, bridge = create_telemetry_graph(graph_config_path)

    # Create calibration controller with graph bridge
    calibration = PidCalibration(server_url, parameters_group, graph_bridge=bridge)

    def run_asyncio():
        """Run the asyncio event loop in a background thread."""
        try:
            asyncio.run(calibration.run())
        except SystemExit:
            pass
        finally:
            QtCore.QTimer.singleShot(0, app.quit)

    # Start asyncio in background thread
    asyncio_thread = Thread(target=run_asyncio, daemon=True)
    asyncio_thread.start()

    # Restore SIGINT handling so Ctrl+C works despite socketio/engineio
    # wrapping the signal handler. The QTimer ensures Python gets a chance
    # to run signal handlers while the Qt event loop is running.
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    tick = QtCore.QTimer()
    tick.start(50)
    tick.timeout.connect(lambda: None)

    # Show graph and run Qt event loop (blocks main thread)
    widget.show()
    ret = app.exec()

    asyncio_thread.join(timeout=5.0)
    sys.exit(ret)


def main():
    """
    Run PID calibration tool.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-pid-calibration` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()
