#!/usr/bin/env python3
# flake8: noqa: E402
import faulthandler
import os
import sys

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

    # Create UI
    win = MainWindow(url)
    win.setWindowIcon(QtGui.QIcon("assets/cogip-logo.png"))

    # Create table entity
    table_entity = TableEntity()
    win.game_view.add_asset(table_entity)

    # Create robot entity
    robot_manager = RobotManager(win.game_view)

    # Connect UI signals to Controller slots
    win.signal_send_command.connect(controller.new_command)
    win.signal_config_updated.connect(controller.config_updated)
    win.signal_wizard_response.connect(controller.wizard_response)
    win.signal_actuators_opened.connect(controller.actuators_started)
    win.signal_actuators_closed.connect(controller.actuators_closed)
    win.signal_new_actuator_command.connect(controller.new_actuator_command)
    win.signal_starter_changed.connect(controller.starter_changed)
    win.game_view.emit_obstacles.connect(controller.emit_monitor_obstacles)

    # Connect UI signals to GameView slots
    win.signal_add_obstacle.connect(win.game_view.add_obstacle)
    win.signal_load_obstacles.connect(win.game_view.load_obstacles)
    win.signal_save_obstacles.connect(win.game_view.save_obstacles)

    # Connect Controller signals to robot manager
    controller.signal_new_robot_pose_current.connect(robot_manager.new_robot_pose_current)
    controller.signal_new_robot_pose_order.connect(robot_manager.new_robot_pose_order)
    controller.signal_new_dyn_obstacles.connect(robot_manager.set_dyn_obstacles)
    controller.signal_add_robot.connect(robot_manager.add_robot)
    controller.signal_del_robot.connect(robot_manager.del_robot)
    controller.signal_start_sensors_emulation.connect(robot_manager.start_sensors_emulation)
    controller.signal_stop_sensors_emulation.connect(robot_manager.stop_sensors_emulation)
    robot_manager.sensors_emit_data_signal.connect(controller.emit_sensors_data)

    # Connect Controller signals to UI slots
    controller.signal_new_console_text.connect(win.log_text.append)
    controller.signal_new_menu.connect(win.load_menu)
    controller.signal_add_robot.connect(win.add_robot)
    controller.signal_del_robot.connect(win.del_robot)
    controller.signal_starter_changed.connect(win.starter_changed)
    controller.signal_new_robot_pose_current.connect(win.new_robot_pose)
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

    sys.exit(ret)


def main():
    """
    Starts the copilot.

    During installation of cogip-tools, `setuptools` is configured
    to create the `copilot` script using this function as entrypoint.
    """
    typer.run(main_opt)
