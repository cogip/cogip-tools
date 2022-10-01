from threading import Thread
import time
from typing import List, Optional

from pydantic import parse_obj_as
from PySide6 import QtCore
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot
import socketio

from cogip.models import models


class SocketioController(QtCore.QObject):
    """
    This class controls the socket.io port used to communicate with the Copilot.
    Its main purpose is to get the shell menu to update the interface,
    get the robot position to update its position, and send the commands
    to the robot through the Copilot.

    Attributes:
        signal_new_console_text:
            Qt signal emitted to log messages in UI console
        signal_new_menu:
            Qt signal emitted to load a new menu
        signal_new_robot_pose:
            Qt signal emitted on robot pose update
        signal_new_robot_state:
            Qt signal emitted on robot state update
        signal_new_dyn_obstacles:
            Qt signal emitted on dynamic obstacles update
        signal_connected:
            Qt signal emitted on Copilot connection state changes
        signal_exit:
            Qt signal emitted to exit Monitor
        signal_start_lidar_emulation:
            Qt signal emitted to start Lidar emulation
        signal_stop_lidar_emulation:
            Qt signal emitted to stop Lidar emulation
        last_cycle:
            Record the last cycle to avoid sending the same data several times
    """
    signal_new_console_text: qtSignal = qtSignal(str)
    signal_new_menu: qtSignal = qtSignal(models.ShellMenu)
    signal_new_robot_pose: qtSignal = qtSignal(models.Pose)
    signal_new_robot_state: qtSignal = qtSignal(models.RobotState)
    signal_new_dyn_obstacles: qtSignal = qtSignal(list)
    signal_connected: qtSignal = qtSignal(bool)
    signal_exit: qtSignal = qtSignal()
    signal_start_lidar_emulation: qtSignal = qtSignal()
    signal_stop_lidar_emulation: qtSignal = qtSignal()
    last_cycle: int = 0

    def __init__(self, url: str):
        """
        Class constructor.

        Arguments:
            url: URL to Copilot socket.io server
        """
        super().__init__()

        self.url = url
        self.sio = socketio.Client()
        self.register_handlers()

        self.menu: Optional[models.ShellMenu] = None

    def start(self):
        """
        Connect to socket.io server.
        """
        # Poll in background to wait for the first connection.
        # Deconnections/reconnections are handle directly by the client.
        self._retry_connection = True
        Thread(target=self.try_connect).start()

    def try_connect(self):
        while(self._retry_connection):
            try:
                self.sio.connect(self.url, socketio_path="sio/socket.io", auth={"type": "monitor"})
            except socketio.exceptions.ConnectionError:
                time.sleep(2)
                continue
            break

    def stop(self):
        """
        Disconnect from socket.io server.
        """
        self.sio.disconnect()

    @qtSlot(str)
    def new_command(self, command: str):
        """
        Send a command to the robot.

        Arguments:
            command: Command to send
        """
        self.signal_new_console_text.emit(f"Send '{command}'")
        self.sio.emit("cmd", command)

    def register_handlers(self):
        """
        Define socket.io message handlers.
        """

        @self.sio.event
        def connect():
            """
            Callback on Copilot connection.
            Send a break message: if the robot is booting, it will abort
            automatic start of the planner.
            """
            self.signal_new_console_text.emit("Connected to Copilot")
            self.sio.emit("break")
            self.signal_connected.emit(True)

        @self.sio.event
        def connect_error(data):
            """
            Callback on Copilot connection error.
            """
            if (
                data and
                isinstance(data, dict) and
                (message := data.get("message")) and
                message == "A monitor is already connected"
               ):
                print(f"Error: {message}.")
                self._retry_connection = False
                self.signal_exit.emit()
                return
            print("Connection error:", data)
            self.signal_new_console_text.emit("Connection to Copilot failed.")
            self.signal_connected.emit(False)

        @self.sio.event
        def disconnect():
            """
            Callback on Copilot disconnection.
            """
            self.signal_new_console_text.emit("Disconnected from Copilot.")
            self.signal_connected.emit(False)

        @self.sio.on("menu")
        def on_menu(data):
            """
            Callback on menu message.
            """
            menu = models.ShellMenu.parse_obj(data)
            if self.menu != menu:
                self.menu = menu
                self.signal_new_menu.emit(menu)

        @self.sio.on("pose")
        def on_pose(data):
            """
            Callback on robot pose message.
            """
            pose = models.Pose.parse_obj(data)
            self.signal_new_robot_pose.emit(pose)

        @self.sio.on("state")
        def on_state(data):
            """
            Callback on robot state message.
            """
            state = models.RobotState.parse_obj(data)
            if state.cycle != self.last_cycle:
                self.last_cycle = state.cycle
                self.signal_new_robot_state.emit(state)

        @self.sio.on("obstacles")
        def on_obstacles(data):
            """
            Callback on obstacles message.
            """
            obstacles = parse_obj_as(models.DynObstacleList, data)
            self.signal_new_dyn_obstacles.emit(obstacles)

        @self.sio.on("start_lidar_emulation")
        def on_start_lidar_emulation():
            """
            Start Lidar emulation.
            """
            self.signal_start_lidar_emulation.emit()

        @self.sio.on("stop_lidar_emulation")
        def on_stop_lidar_emulation():
            """
            Stop Lidar emulation.
            """
            self.signal_stop_lidar_emulation.emit()

    def emit_lidar_data(self, data: List[int]) -> None:
        """
        Send Lidar data to Copilot.

        Arguments:
            data: List of distances for each angle
        """
        if self.sio.connected:
            self.sio.emit("lidar_data", data)
