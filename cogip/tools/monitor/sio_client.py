import time
from threading import Thread
from typing import Any

import polling2
import socketio
from pydantic import TypeAdapter, ValidationError
from PySide6 import QtCore
from PySide6.QtCore import Signal as QtSignal
from PySide6.QtCore import Slot as QtSlot
from socketio.exceptions import ConnectionError

from cogip import logger
from cogip.models import models
from cogip.models.actuators import PositionalActuatorEnum
from cogip.tools.planner.scservos import SCServoEnum


class SocketioClient(QtCore.QObject):
    """
    This class controls the socket.io port used to communicate with the server.
    Its main purpose is to get the shell and tool menus to update the interface,
    get the robot position to update its position, and send the commands
    to the robot and to the tools.

    Attributes:
        signal_connected:
            Qt signal emitted on server connection state changes
        signal_exit:
            Qt signal emitted to exit Monitor
        signal_add_robot:
            Qt signal emitted to add a new robot
        signal_del_robot:
            Qt signal emitted to remove a robot
        signal_pose_current:
            Qt signal emitted on pose current update
        signal_robot_path:
            Qt signal emitted on robot path update
        signal_tool_menu:
            Qt signal emitted to load a new tool menu
        signal_config_request:
            Qt signal emitted on configuration requests
        signal_wizard_request:
            Qt signal emitted to forward wizard requests
        signal_starter_changed:
            Qt signal emitted the starter state has changed
        signal_soft_reset:
            Qt signal emitted on soft reset request
        signal_servo_changed:
            Qt signal emitted on servo command
        signal_lift_changed:
            Qt signal emitted on lift command
    """

    signal_connected: QtSignal = QtSignal(bool)
    signal_exit: QtSignal = QtSignal()
    signal_add_robot: QtSignal = QtSignal(int, bool, bool)
    signal_del_robot: QtSignal = QtSignal(int)
    signal_pose_current: QtSignal = QtSignal(models.Pose)
    signal_robot_path: QtSignal = QtSignal(list)
    signal_tool_menu: QtSignal = QtSignal(models.ShellMenu)
    signal_config_request: QtSignal = QtSignal(dict)
    signal_wizard_request: QtSignal = QtSignal(dict)
    signal_close_wizard: QtSignal = QtSignal()
    signal_starter_changed: QtSignal = QtSignal(bool)
    signal_soft_reset: QtSignal = QtSignal()
    signal_servo_changed: QtSignal = QtSignal(str, float)
    signal_lift_changed: QtSignal = QtSignal(str, float)

    def __init__(self, url: str):
        """
        Class constructor.

        Arguments:
            url: URL to socket.io server
        """
        super().__init__()

        self._url = url
        self.sio = socketio.Client()
        self.register_events()

    @QtCore.Property(str, constant=True)
    def url(self) -> str:
        return self._url

    def start(self):
        """
        Connect to socket.io server.
        """
        # Poll in background to wait for the first connection.
        # Disconnections/re-connections are handled directly by the client.
        self.retry_connection = True
        Thread(target=self.try_connect).start()

    def try_connect(self):
        while self.retry_connection:
            try:
                self.sio.connect(self._url, namespaces=["/monitor", "/dashboard"])
            except ConnectionError as ex:
                logger.error(str(ex))
                time.sleep(2)
                continue
            break

    def stop(self):
        """
        Disconnect from socket.io server.
        """
        self.retry_connection = False
        if self.sio.connected:
            self.sio.disconnect()

    @QtSlot(str)
    def tool_command(self, command: str):
        """
        Send a command to the robot.

        Arguments:
            command: Command to send
        """
        self.sio.emit("tool_cmd", command, namespace="/dashboard")

    @QtSlot(str, str, str, "QVariant", bool)
    def send_config_update(self, namespace: str, sio_event: str, name: str, value: object, is_integer: bool = False):
        """
        Forward a configuration update to the server.

        Arguments:
            namespace: Socket.IO namespace to target
            sio_event: Event name to emit (defaults to 'config_updated' when empty)
            name: Property name
            value: New property value
            is_integer: Whether the value should be converted to an integer
                (integers and floats are sent as floats from QML)
        """
        value = int(value) if is_integer else value
        payload = {
            "namespace": namespace,
            "sio_event": sio_event or "config_updated",
            "name": name,
            "value": value,
        }
        self.sio.emit("config_updated", payload, namespace="/dashboard")

    @QtSlot(dict)
    def wizard_response(self, response: dict[str, Any]):
        if not response.get("namespace"):
            return
        match response["type"]:
            case "choice_integer":
                response["value"] = int(response["value"])
            case "choice_str_group":
                response["type"] = "choice_str"
        self.sio.emit("wizard", response, namespace="/dashboard")

    @QtSlot(bool)
    def starter_changed(self, pushed: bool):
        self.sio.emit("starter_changed", pushed, namespace="/dashboard")

    def register_events(self):
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
                self.retry_connection = False
                self.signal_exit.emit()
                return
            logger.error(f"Monitor connection error: {data}")
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
            self.signal_connected.emit(False)
            logger.info("Monitor disconnected from cogip-server")

        @self.sio.on("add_robot", namespace="/monitor")
        def on_add_robot(robot_id: int, virtual_planner: bool, virtual_detector: bool) -> None:
            """
            Add a new robot.
            """
            self.signal_add_robot.emit(int(robot_id), virtual_planner, virtual_detector)

        @self.sio.on("del_robot", namespace="/monitor")
        def on_del_robot(robot_id: int) -> None:
            """
            Remove a robot.
            """
            self.signal_del_robot.emit(robot_id)

        @self.sio.on("pose_current", namespace="/dashboard")
        def on_pose_current(robot_id: int, data: list[dict[str, float]]) -> None:
            """
            Callback on pose current message.
            """
            try:
                pose_current = models.Pose(**data)
                self.signal_pose_current.emit(pose_current)
            except ValidationError as exc:
                logger.warning("Failed to decode pose current: %s", exc)

        @self.sio.on("path", namespace="/dashboard")
        def on_path(robot_id: int, data: list[dict[str, float]]) -> None:
            """
            Callback on robot path message.
            """
            try:
                path = TypeAdapter(list[models.Pose]).validate_python(data)
                self.signal_robot_path.emit(path)
            except ValidationError as exc:
                logger.warning("Failed to decode robot path: %s", exc)

        @self.sio.on("tool_menu", namespace="/dashboard")
        def on_tool_menu(data):
            """
            Callback on tool menu message.
            """
            try:
                menu = models.ShellMenu.model_validate(data)
            except ValidationError as exc:
                logger.warning("Failed to decode tool menu: %s", exc)
                return

            logger.info("Tool menu '%s' received with %d entries", menu.name, len(menu.entries))
            self.signal_tool_menu.emit(menu)

        @self.sio.on("config", namespace="/dashboard")
        def on_config(config):
            """
            Callback on config request.
            """
            logger.debug("Config received: %s", config)
            self.signal_config_request.emit(config)

        @self.sio.on("wizard", namespace="/dashboard")
        def on_wizard_request(data: dict[str, Any]) -> None:
            """
            Wizard request.
            """
            if (
                (choices := data.get("choices"))
                and isinstance(choices, list)
                and choices
                and isinstance(choices[0], list)
            ):
                data["type"] = "choice_str_group"
            self.signal_wizard_request.emit(data)

        @self.sio.on("close_wizard", namespace="/dashboard")
        def on_close_wizard() -> None:
            """
            Close wizard.
            """
            self.signal_close_wizard.emit()

        @self.sio.on("score", namespace="/dashboard")
        def on_score(data: int) -> None:
            """
            Score.
            """
            self.signal_wizard_request.emit(
                {
                    "name": "Score",
                    "type": "message",
                    "value": str(data),
                    "namespace": "",
                }
            )

        @self.sio.on("starter_changed", namespace="/dashboard")
        def on_starter_changed(pushed: bool) -> None:
            """
            Change the state of a starter.
            """
            self.signal_starter_changed.emit(pushed)

        @self.sio.on("soft_reset", namespace="/dashboard")
        def on_soft_reset() -> None:
            """
            Soft reset.
            """
            self.signal_soft_reset.emit()

        @self.sio.on("servo", namespace="/monitor")
        def on_servo(servo_id: int, position: int) -> None:
            """
            Callback on servo message.
            """
            servo_id = SCServoEnum(servo_id)
            logger.info(f"Servo command received: {(servo_id, position)}")
            logger.info(f"Servo ID: {servo_id}, Position: {position}")

            match (servo_id, position):
                case (SCServoEnum.FRONT_ARM_LEFT, 1):
                    orientation = 90
                case (SCServoEnum.FRONT_ARM_LEFT, 0):
                    orientation = 0
                case (SCServoEnum.FRONT_ARM_RIGHT, 1):
                    orientation = -90
                case (SCServoEnum.FRONT_ARM_RIGHT, 0):
                    orientation = 0
                case (SCServoEnum.BACK_ARM_LEFT, 1):
                    orientation = -90
                case (SCServoEnum.BACK_ARM_LEFT, 0):
                    orientation = 0
                case (SCServoEnum.BACK_ARM_RIGHT, 1):
                    orientation = 90
                case (SCServoEnum.BACK_ARM_RIGHT, 0):
                    orientation = 0
                case _:
                    logger.warning(f"Unknown servo ID: {servo_id} or position: {position}")
                    return

            self.signal_servo_changed.emit(servo_id.name.title(), float(orientation))

        @self.sio.on("lift", namespace="/monitor")
        def on_lift(actuator_id: int, position: int) -> None:
            """
            Callback on lift message.
            """
            lift_id = PositionalActuatorEnum(actuator_id)
            logger.info(f"Lift command received: {(lift_id, position)}")
            self.signal_lift_changed.emit(lift_id.name.title(), float(position))
