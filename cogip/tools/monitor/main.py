#!/usr/bin/env python3
# flake8: noqa: E402
import faulthandler
import os
import sys
from pathlib import Path

# Remove info logs from QWebEngineView.
# This needs to be set in os.environ before importing typer.
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.webenginecontext.info=false"

import typer
from PySide6 import QtGui, QtWidgets

from cogip.entities.table import TableEntity
from .mainwindow import MainWindow
from .robots import RobotManager
from .socketiocontroller import SocketioController


def main_opt(
    url: str = typer.Argument(
        "http://localhost:8091",
        envvar="COGIP_SOCKETIO_SERVER_URL",
        help="Socket.IO Server URL",
    ),
) -> None:
    """
    Launch COGIP Monitor.
    """
    faulthandler.enable()

    # Create socketio controller
    controller = SocketioController(url)

    # Create QApplication
    app = QtWidgets.QApplication(sys.argv)

    # Set icon theme so that icons are visible in Docker containers.
    if Path("/usr/share/icons/Yaru-dark").exists():
        QtGui.QIcon.setThemeName("Yaru-dark")

    # Set dark theme
    palette = app.palette()
    palette.setColor(QtGui.QPalette.ColorRole.Window, "#2a2a2a")
    palette.setColor(QtGui.QPalette.ColorRole.WindowText, "#ffffff")
    palette.setColor(QtGui.QPalette.ColorRole.Base, "#2a2a2a")
    palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, "#272727")
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, "#ffffdc")
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, "#000000")
    palette.setColor(QtGui.QPalette.ColorRole.Text, "#ffffff")
    palette.setColor(QtGui.QPalette.ColorRole.Button, "#2a2a2a")
    palette.setColor(QtGui.QPalette.ColorRole.ButtonText, "#ffffff")
    palette.setColor(QtGui.QPalette.ColorRole.BrightText, "#ffffff")
    palette.setColor(QtGui.QPalette.ColorRole.Highlight, "#e95420")
    palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, "#ffffff")
    palette.setColor(QtGui.QPalette.ColorRole.Light, "#343434")
    palette.setColor(QtGui.QPalette.ColorRole.Midlight, "#2f2f2f")
    palette.setColor(QtGui.QPalette.ColorRole.Dark, "#252525")
    palette.setColor(QtGui.QPalette.ColorRole.Mid, "#2f2f2f")
    palette.setColor(QtGui.QPalette.ColorRole.Shadow, "#020202")
    palette.setColor(QtGui.QPalette.ColorRole.Link, "#308cc6")
    palette.setColor(QtGui.QPalette.ColorRole.LinkVisited, "#ff00ff")
    palette.setColor(QtGui.QPalette.ColorRole.NoRole, "#000000")
    palette.setColor(QtGui.QPalette.ColorRole.PlaceholderText, "#9b9b9b")
    palette.setColor(QtGui.QPalette.ColorRole.Accent, "#308cc6")
    app.setPalette(palette)

    # Create UI
    win = MainWindow(url)
    win.setWindowIcon(QtGui.QIcon("assets/cogip-logo.png"))

    # Create table entity
    table_entity = TableEntity()
    win.game_view.add_asset(table_entity)

    # Create robot entity
    robot_manager = RobotManager(win)

    # Connect UI signals to Controller slots
    win.signal_send_command.connect(controller.new_command)
    win.signal_config_updated.connect(controller.config_updated)
    win.signal_wizard_response.connect(controller.wizard_response)
    win.signal_actuators_opened.connect(controller.actuators_started)
    win.signal_actuators_closed.connect(controller.actuators_closed)
    win.signal_new_actuator_command.connect(controller.new_actuator_command)
    win.signal_starter_changed.connect(controller.starter_changed)

    # Connect UI signals to GameView slots
    win.signal_add_obstacle.connect(win.game_view.add_obstacle)
    win.signal_load_obstacles.connect(win.game_view.load_obstacles)
    win.signal_save_obstacles.connect(win.game_view.save_obstacles)

    # Connect Controller signals to robot manager
    controller.signal_new_robot_pose_order.connect(robot_manager.new_robot_pose_order)
    controller.signal_new_dyn_obstacles.connect(robot_manager.set_dyn_obstacles)
    controller.signal_add_robot.connect(robot_manager.add_robot)
    controller.signal_del_robot.connect(robot_manager.del_robot)
    controller.signal_start_sensors_emulation.connect(robot_manager.start_sensors_emulation)
    controller.signal_stop_sensors_emulation.connect(robot_manager.stop_sensors_emulation)

    # Connect Controller signals to UI slots
    controller.signal_new_console_text.connect(win.log_text.append)
    controller.signal_new_menu.connect(win.load_menu)
    controller.signal_add_robot.connect(win.add_robot)
    controller.signal_del_robot.connect(win.del_robot)
    controller.signal_starter_changed.connect(win.starter_changed)
    controller.signal_new_robot_state.connect(win.new_robot_state)
    controller.signal_connected.connect(win.connected)
    controller.signal_exit.connect(win.close)
    controller.signal_config_request.connect(win.config_request)
    controller.signal_wizard_request.connect(win.wizard_request)
    controller.signal_close_wizard.connect(win.close_wizard)
    controller.signal_actuator_state.connect(win.actuator_state)
    controller.signal_planner_reset.connect(win.planner_reset)

    # Connect Controller signals to GameView slots
    controller.signal_new_robot_path.connect(win.game_view.new_robot_path)

    # Show UI
    win.show()
    # win.showFullScreen()
    win.raise_()

    controller.start()

    ret = app.exec()

    controller.stop()
    robot_manager.disable_robots()

    sys.exit(ret)


def main():
    """
    Starts the copilot.

    During installation of cogip-tools, `setuptools` is configured
    to create the `copilot` script using this function as entrypoint.
    """
    typer.run(main_opt)
