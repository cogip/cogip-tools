import time
from threading import Thread
from typing import Any

import polling2
import socketio
from pydantic import TypeAdapter, ValidationError
from PySide6 import QtCore
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot

from cogip import logger
from cogip.models import models
from cogip.models.actuators import ActuatorCommand, ActuatorState


class SocketioController(QtCore.QObject):
    """
    This class controls the socket.io port used to communicate with the server.
    Its main purpose is to get the shell and tool menus to update the interface,
    get the robot position to update its position, and send the commands
    to the robot and to the tools.

    Attributes:
        signal_new_console_text:
            Qt signal emitted to log messages in UI console
        signal_new_menu:
            Qt signal emitted to load a new shell/tool menu
        signal_new_robot_pose_current:
            Qt signal emitted on robot pose current update
        signal_new_robot_pose_order:
            Qt signal emitted on robot pose order update
        signal_new_robot_state:
            Qt signal emitted on robot state update
        signal_new_robot_path:
            Qt signal emitted on robot path update
        signal_new_dyn_obstacles:
            Qt signal emitted on dynamic obstacles update
        signal_connected:
            Qt signal emitted on server connection state changes
        signal_exit:
            Qt signal emitted to exit Monitor
        signal_add_robot:
            Qt signal emitted to add a new robot
        signal_del_robot:
            Qt signal emitted to remove a robot
        signal_wizard_request:
            Qt signal emitted to forward wizard requests
        signal_start_sensors_emulation:
            Qt signal emitted to start sensors emulation
        signal_stop_sensors_emulation:
            Qt signal emitted to stop sensors emulation
        signal_config_request:
            Qt signal emitted to load a new shell/tool menu
        signal_planner_reset:
            Qt signal emitted on Planner reset command
        signal_starter_changed:
            Qt signal emitted the starter state has changed
    """

    signal_new_console_text: qtSignal = qtSignal(str)
    signal_new_menu: qtSignal = qtSignal(str, models.ShellMenu)
    signal_new_robot_pose_current: qtSignal = qtSignal(int, models.Pose)
    signal_new_robot_pose_order: qtSignal = qtSignal(int, models.Pose)
    signal_new_robot_state: qtSignal = qtSignal(int, models.RobotState)
    signal_new_robot_path: qtSignal = qtSignal(int, list)
    signal_new_dyn_obstacles: qtSignal = qtSignal(list)
    signal_connected: qtSignal = qtSignal(bool)
    signal_exit: qtSignal = qtSignal()
    signal_add_robot: qtSignal = qtSignal(int, bool)
    signal_del_robot: qtSignal = qtSignal(int)
    signal_wizard_request: qtSignal = qtSignal(dict)
    signal_close_wizard: qtSignal = qtSignal()
    signal_start_sensors_emulation: qtSignal = qtSignal(int)
    signal_stop_sensors_emulation: qtSignal = qtSignal(int)
    signal_config_request: qtSignal = qtSignal(dict)
    signal_actuator_state: qtSignal = qtSignal(object)
    signal_planner_reset: qtSignal = qtSignal()
    signal_starter_changed: qtSignal = qtSignal(int, bool)

    def __init__(self, url: str):
        """
        Class constructor.

        Arguments:
            url: URL to socket.io server
        """
        super().__init__()

        self.url = url
        self.sio = socketio.Client()
        self.register_handlers()

        self.menus: dict[str, models.ShellMenu | None] = {}

    def start(self):
        """
        Connect to socket.io server.
        """
        # Poll in background to wait for the first connection.
        # Disconnections/reconnections are handle directly by the client.
        self._retry_connection = True
        Thread(target=self.try_connect).start()

    def try_connect(self):
        while self._retry_connection:
            try:
                self.sio.connect(self.url, namespaces=["/monitor", "/dashboard"])
            except socketio.exceptions.ConnectionError as ex:
                print(ex)
                time.sleep(2)
                continue
            break

    def stop(self):
        """
        Disconnect from socket.io server.
        """
        self._retry_connection = False
        if self.sio.connected:
            self.sio.disconnect()

    @qtSlot(str)
    def new_command(self, menu_name: str, command: str):
        """
        Send a command to the robot.

        Arguments:
            menu_name: menu to update ("shell", "tool", ...)
            command: Command to send
        """
        name, _, robot_id = menu_name.partition(" ")
        if name == "shell":
            self.sio.emit("shell_cmd", command, namespace="/dashboard")
        else:
            self.sio.emit(f"{menu_name}_cmd", command, namespace="/dashboard")
        self.signal_new_console_text.emit(f"Send '{command}' to {menu_name}")

    @qtSlot(dict)
    def config_updated(self, config: dict[str, Any]):
        self.sio.emit("config_updated", config, namespace="/dashboard")

    @qtSlot(dict)
    def wizard_response(self, response: dict[str, Any]):
        self.sio.emit("wizard", response, namespace="/dashboard")

    def new_actuator_command(self, command: ActuatorCommand):
        """
        Send an actuator command to the robot.

        Arguments:
            command: actuator command to send
        """
        self.sio.emit("actuator_command", command.model_dump(mode="json"), namespace="/dashboard")

    def actuators_started(self):
        """
        Request to start emitting actuators state from the robot.
        """
        self.sio.emit("actuators_start", namespace="/dashboard")

    def actuators_closed(self):
        """
        Request to stop emitting actuators state from the robot.
        """
        self.sio.emit("actuators_stop", namespace="/dashboard")

    @qtSlot(int, bool)
    def starter_changed(self, robot_id, pushed: bool):
        self.sio.emit("starter_changed", pushed, namespace="/monitor")

    def on_menu(self, menu_name: str, data):
        menu = models.ShellMenu.model_validate(data)
        if self.menus.get(menu_name) != menu:
            self.menus[menu_name] = menu
            self.signal_new_menu.emit(menu_name, menu)

    def register_handlers(self):
        """
        Define socket.io message handlers.
        """

        @self.sio.on("connect", namespace="/dashboard")
        def dashboard_connect():
            """
            Callback on server connection.
            """
            polling2.poll(lambda: self.sio.connected is True, step=0.2, poll_forever=True)
            logger.info("Dashboard connected to cogip-server")
            self.sio.emit("connected", namespace="/dashboard")

        @self.sio.on("connect", namespace="/monitor")
        def monitor_connect():
            """
            Callback on server connection.
            """
            polling2.poll(lambda: self.sio.connected is True, step=0.2, poll_forever=True)
            logger.info("Monitor connected to cogip-server")
            self.sio.emit("connected", namespace="/monitor")
            self.signal_new_console_text.emit("Connected to server")
            self.signal_connected.emit(True)

        @self.sio.event(namespace="/monitor")
        def connect_error(data):
            """
            Callback on server connection error.
            """
            if (
                data
                and isinstance(data, dict)
                and (message := data.get("message"))
                and message == "A monitor is already connected"
            ):
                logger.error(f"Error: {message}.")
                self._retry_connection = False
                self.signal_exit.emit()
                return
            logger.error(f"Monitor connection error: {data}")
            self.signal_new_console_text.emit("Connection to server failed.")
            self.signal_connected.emit(False)

        @self.sio.event(namespace="/dashboard")
        def dashboard_disconnect():
            """
            Callback on server disconnection.
            """
            logger.info("Dashboard disconnected from cogip-server")

        @self.sio.event(namespace="/monitor")
        def monitor_disconnect():
            """
            Callback on server disconnection.
            """
            self.signal_new_console_text.emit("Disconnected from server.")
            self.signal_connected.emit(False)
            logger.info("Monitor disconnected from cogip-server")

        @self.sio.on("shell_menu", namespace="/dashboard")
        def on_shell_menu(robot_id: int, menu: dict[str, Any]) -> None:
            """
            Callback on shell menu message.
            """
            self.on_menu(f"shell {robot_id}", menu)

        @self.sio.on("tool_menu", namespace="/dashboard")
        def on_tool_menu(data):
            """
            Callback on tool menu message.
            """
            self.on_menu("tool", data)

        @self.sio.on("config", namespace="/dashboard")
        def on_config(config):
            """
            Callback on config request.
            """
            self.signal_config_request.emit(config)

        @self.sio.on("actuator_state", namespace="/dashboard")
        def on_actuator_state(actuator_state):
            """
            Callback on actuator_state message.
            """
            try:
                state = TypeAdapter(ActuatorState).validate_python(actuator_state)
                self.signal_actuator_state.emit(state)
            except ValidationError as exc:
                logger.warning(f"Failed to decode ActuatorState: {exc}")

        @self.sio.on("pose_current", namespace="/dashboard")
        def on_pose_current(robot_id: int, data: dict[str, Any]) -> None:
            """
            Callback on robot pose current message.
            """
            pose = models.Pose.model_validate(data)
            self.signal_new_robot_pose_current.emit(robot_id, pose)

        @self.sio.on("pose_order", namespace="/dashboard")
        def on_pose_order(robot_id: int, data: dict[str, Any]) -> None:
            """
            Callback on robot pose order message.
            """
            pose = models.Pose.model_validate(data)
            self.signal_new_robot_pose_order.emit(robot_id, pose)

        @self.sio.on("state", namespace="/dashboard")
        def on_state(robot_id: int, data: dict[str, Any]) -> None:
            """
            Callback on robot state message.
            """
            state = models.RobotState.model_validate(data)
            self.signal_new_robot_state.emit(robot_id, state)

        @self.sio.on("path", namespace="/dashboard")
        def on_path(robot_id: int, data: list[dict[str, float]]) -> None:
            """
            Callback on robot path message.
            """
            path = TypeAdapter(list[models.Vertex]).validate_python(data)
            self.signal_new_robot_path.emit(robot_id, path)

        @self.sio.on("obstacles", namespace="/dashboard")
        def on_obstacles(data):
            """
            Callback on obstacles message.
            """
            obstacles = TypeAdapter(models.DynObstacleList).validate_python(data)
            self.signal_new_dyn_obstacles.emit(obstacles)

        @self.sio.on("add_robot", namespace="/monitor")
        def on_add_robot(robot_id: int, virtual: bool) -> None:
            """
            Add a new robot.
            """
            self.signal_add_robot.emit(int(robot_id), virtual)

        @self.sio.on("del_robot", namespace="/monitor")
        def on_del_robot(robot_id: int) -> None:
            """
            Remove a robot.
            """
            self.signal_del_robot.emit(robot_id)

        @self.sio.on("wizard", namespace="/dashboard")
        def on_wizard_request(data: dict[str, Any]) -> None:
            """
            Wizard request.
            """
            self.signal_wizard_request.emit(data)

        @self.sio.on("close_wizard", namespace="/dashboard")
        def on_close_wizard() -> None:
            """
            Close wizard.
            """
            self.signal_close_wizard.emit()

        @self.sio.on("start_sensors_emulation", namespace="/monitor")
        def on_start_sensors_emulation(robot_id: int) -> None:
            """
            Start sensors emulation.
            """
            self.signal_start_sensors_emulation.emit(robot_id)

        @self.sio.on("stop_sensors_emulation", namespace="/monitor")
        def on_stop_sensors_emulation(robot_id: int) -> None:
            """
            Stop sensors emulation.
            """
            self.signal_stop_sensors_emulation.emit(robot_id)

        @self.sio.on("cmd_reset", namespace="/monitor")
        def on_cmd_reset() -> None:
            """
            Reset command from Planner.
            """
            self.signal_planner_reset.emit()

        @self.sio.on("starter_changed", namespace="/monitor")
        def on_starter_changed(robot_id: int, pushed: bool) -> None:
            """
            Change the state of a starter.
            """
            self.signal_starter_changed.emit(robot_id, pushed)

    def emit_sensors_data(self, robot_id: int, data: list[int]) -> None:
        """
        Send sensors data to server.

        Arguments:
            robot_id: ID of the robot
            data: List of distances for each angle
        """
        if self.sio.connected:
            self.sio.emit("sensors_data", data, namespace="/monitor")

    def emit_monitor_obstacles(self, data: list[(int, int)]) -> None:
        """
        Sends obstacles created in monitor to server.

        Arguments:
            robot_id: ID of the robot
            data: List of obstacles
        """
        if self.sio.connected:
            self.sio.emit("monitor_obstacles", data, namespace="/monitor")
