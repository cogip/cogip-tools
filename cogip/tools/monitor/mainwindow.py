from functools import partial
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot

from cogip.widgets.chartsview import ChartsView
from cogip.widgets.dashboard import Dashboard
from cogip.widgets.gameview import GameView
from cogip.widgets.help import HelpCameraControlDialog
from cogip.widgets.actuators import ActuatorsDialog
from cogip.widgets.properties import PropertiesDialog
from cogip.widgets.wizard import WizardDialog
from cogip.models import Pose, ShellMenu, RobotState
from cogip.models.actuators import ActuatorsState, ActuatorCommand


class MainWindow(QtWidgets.QMainWindow):
    """MainWindow class

    Build the main window of the monitor.

    It contains:

      - a menu bar,
      - a tool bar with buttons to add/load/save obstacles,
      - a status bar with robot position,
      - a menu with commands available in the current firmware shell menu,
      - a console recording the firmware output.

    Attributes:
        signal_config_updated: Qt signal to update config
        signal_wizard_response: Qt signal to emit wizard response
        signal_send_command: Qt signal to send a command to the firmware
        signal_add_obstacle: Qt signal to add an obstacle
        signal_load_obstacles: Qt signal to load obstacles
        signal_save_obstacles: Qt signal to save obstacles
        signal_load_cake_layers: Qt signal to load cake layers
        signal_save_cake_layers: Qt signal to save cake layers
        signal_new_actuator_command: Qt signal to send actuator command to server
        signal_actuators_closed: Qt signal to stop actuators state request
    """
    signal_config_updated: qtSignal = qtSignal(dict)
    signal_wizard_response: qtSignal = qtSignal(dict)
    signal_send_command: qtSignal = qtSignal(str, str)
    signal_add_obstacle: qtSignal = qtSignal()
    signal_load_obstacles: qtSignal = qtSignal(Path)
    signal_save_obstacles: qtSignal = qtSignal(Path)
    signal_load_cake_layers: qtSignal = qtSignal(Path)
    signal_save_cake_layers: qtSignal = qtSignal(Path)
    signal_new_actuator_command: qtSignal = qtSignal(int, object)
    signal_actuators_closed: qtSignal = qtSignal(int)

    def __init__(self, url: str, *args, **kwargs):
        """
        Class constructor.

        Arguments:
            url: URL of the copilot web server
        """
        super(MainWindow, self).__init__(*args, **kwargs)
        self.robot_status_row: Dict[int, int] = {}
        self.charts_view: Dict[int, ChartsView] = {}
        self.available_chart_views: List[ChartsView] = []
        self.menu_widgets: Dict[str, Dict[str, QtWidgets.QWidget]] = {}

        self.setWindowTitle('COGIP Monitor')

        self.central_widget = QtWidgets.QWidget()
        self.central_layout = QtWidgets.QHBoxLayout()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        obstacles_menu = menubar.addMenu('&Obstacles')
        cake_layers_menu = menubar.addMenu('&Cake Layers')
        self.view_menu = menubar.addMenu('&View')
        help_menu = menubar.addMenu('&Help')

        # Toolbars
        file_toolbar = self.addToolBar('File')
        file_toolbar.setObjectName("File Toolbar")
        obstacles_toolbar = self.addToolBar('Obstacles')
        obstacles_toolbar.setObjectName("Obstacles Toolbar")

        # Status bar
        status_bar = self.statusBar()

        self.connected_label = QtWidgets.QLabel("Disconnected")
        status_bar.addPermanentWidget(self.connected_label, 1)

        status_widget = QtWidgets.QWidget()
        status_bar.addPermanentWidget(status_widget)

        self.status_layout = QtWidgets.QGridLayout()
        status_widget.setLayout(self.status_layout)

        cycle_label = QtWidgets.QLabel("Cycle")
        self.status_layout.addWidget(cycle_label, 0, 1)

        pos_x_label = QtWidgets.QLabel("X")
        self.status_layout.addWidget(pos_x_label, 0, 2)

        pos_y_label = QtWidgets.QLabel("Y")
        self.status_layout.addWidget(pos_y_label, 0, 3)

        pos_angle_label = QtWidgets.QLabel("Angle")
        self.status_layout.addWidget(pos_angle_label, 0, 4)

        # Actions
        # Icons: https://commons.wikimedia.org/wiki/GNOME_Desktop_icons

        # Exit action
        self.exit_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("application-exit"),
            'Exit',
            self
        )
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.setStatusTip('Exit application')
        self.exit_action.triggered.connect(self.close)
        file_menu.addAction(self.exit_action)
        file_toolbar.addAction(self.exit_action)

        # Add obstacle action
        self.add_obstacle_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("list-add"),
            'Add obstacle',
            self
        )
        self.add_obstacle_action.setShortcut('Ctrl+A')
        self.add_obstacle_action.setStatusTip('Add obstacle')
        self.add_obstacle_action.triggered.connect(self.add_obstacle)
        obstacles_menu.addAction(self.add_obstacle_action)
        obstacles_toolbar.addAction(self.add_obstacle_action)

        # Open obstacles action
        self.load_obstacles_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("document-open"),
            'Load obstacles',
            self
        )
        self.load_obstacles_action.setShortcut('Ctrl+O')
        self.load_obstacles_action.setStatusTip('Load obstacles')
        self.load_obstacles_action.triggered.connect(self.load_obstacles)
        obstacles_menu.addAction(self.load_obstacles_action)
        obstacles_toolbar.addAction(self.load_obstacles_action)

        # Save obstacles action
        self.save_obstacles_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("document-save"),
            'Save obstacles',
            self
        )
        self.save_obstacles_action.setShortcut('Ctrl+S')
        self.save_obstacles_action.setStatusTip('Save obstacles')
        self.save_obstacles_action.triggered.connect(self.save_obstacles)
        obstacles_menu.addAction(self.save_obstacles_action)
        obstacles_toolbar.addAction(self.save_obstacles_action)

        # Open cake layers action
        self.load_cake_layers_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("document-open"),
            'Load cake layers',
            self
        )
        self.load_cake_layers_action.setStatusTip('Load cake layers')
        self.load_cake_layers_action.triggered.connect(self.load_cake_layers)
        cake_layers_menu.addAction(self.load_cake_layers_action)

        # Save cake layers action
        self.save_cake_layers_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("document-save"),
            'Save cake layers',
            self
        )
        self.save_cake_layers_action.setStatusTip('Save cake layers')
        self.save_cake_layers_action.triggered.connect(self.save_cake_layers)
        cake_layers_menu.addAction(self.save_cake_layers_action)

        # Console
        dock = QtWidgets.QDockWidget("Console")
        dock.setObjectName("Console")
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        dock.setWidget(self.log_text)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        file_menu.addAction(dock.toggleViewAction())
        obstacles_menu.addAction(dock.toggleViewAction())

        self.menu_tab_widget = QtWidgets.QTabWidget()
        self.central_layout.insertWidget(0, self.menu_tab_widget, 1)

        self.menu_staked_widgets: Dict[str, QtWidgets.QStackedWidget] = {}

        # GameView widget
        self.game_view = GameView()
        self.central_layout.insertWidget(1, self.game_view, 10)

        # Dashboard widget
        self.dashboard = Dashboard(url, self)

        # Help controls widget
        self.help_camera_control = HelpCameraControlDialog(self)

        # Properties windows
        self.properties = {}

        # Actuators control windows
        self.actuators_dialogs: dict[int, ActuatorsDialog] = {}

        # Add view action
        self.view_dashboard_action = QtGui.QAction('Dashboard', self)
        self.view_dashboard_action.setStatusTip('Display/Hide dashboard')
        self.view_dashboard_action.setCheckable(True)
        self.view_dashboard_action.toggled.connect(self.dashboard_toggled)
        self.dashboard.closed.connect(partial(self.view_dashboard_action.setChecked, False))
        self.view_menu.addAction(self.view_dashboard_action)

        # Add help action
        self.help_camera_control_action = QtGui.QAction('Camera control', self)
        self.help_camera_control_action.setStatusTip('Display camera control help')
        self.help_camera_control_action.triggered.connect(self.display_help_camera_control)
        self.dashboard.closed.connect(partial(self.help_camera_control_action.setChecked, False))
        help_menu.addAction(self.help_camera_control_action)

        self.readSettings()

    @qtSlot(bool)
    def charts_toggled(self, robot_id: int, checked: bool):
        """
        Qt Slot

        Show/hide the calibration charts.

        Arguments:
            robot_id: ID of the robot corresponding to the chart view
            checked: Show action has checked or unchecked
        """
        view = self.charts_view.get(robot_id)
        if view is None:
            return

        if checked:
            view.show()
            view.raise_()
            view.activateWindow()
        else:
            view.close()

    @qtSlot(bool)
    def dashboard_toggled(self, checked: bool):
        """
        Qt Slot

        Show/hide the dashboard.

        Arguments:
            checked: Show action was checked or unchecked
        """
        if checked:
            self.dashboard.show()
            self.dashboard.raise_()
            self.dashboard.activateWindow()
        else:
            self.dashboard.close()

    def update_view_menu(self):
        """
        Rebuild all the view menu to update the calibration charts sub-menu.
        """
        self.view_menu.clear()
        if len(self.charts_view):
            calibration_menu = self.view_menu.addMenu("Calibration Charts")
            for robot_id, view in self.charts_view.items():
                action = calibration_menu.addAction(f"Robot {robot_id}")
                action.setCheckable(True)
                action.toggled.connect(partial(self.charts_toggled, robot_id))
                if view.isVisible():
                    action.setChecked(True)
                view.closed.connect(partial(action.setChecked, False))

        self.view_menu.addAction(self.view_dashboard_action)

    def add_robot(self, robot_id: int) -> None:
        """
        Add a new robot status bar.

        Parameters:
            robot_id: ID of the new robot
        """
        self.game_view.add_robot(robot_id)

        # Status bar
        if robot_id in self.robot_status_row:
            return

        row = self.status_layout.rowCount()
        self.robot_status_row[robot_id] = row

        title_text = QtWidgets.QLabel(f"Robot {robot_id}")
        self.status_layout.addWidget(title_text, row, 0)

        cycle_text = QtWidgets.QLabel()
        cycle_text.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        cycle_text.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        self.status_layout.addWidget(cycle_text, row, 1)

        pos_x_text = QtWidgets.QLabel()
        pos_x_text.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        pos_x_text.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        self.status_layout.addWidget(pos_x_text, row, 2)

        pos_y_text = QtWidgets.QLabel()
        pos_y_text.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        pos_y_text.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        self.status_layout.addWidget(pos_y_text, row, 3)

        pos_angle_text = QtWidgets.QLabel()
        pos_angle_text.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        pos_angle_text.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        self.status_layout.addWidget(pos_angle_text, row, 4)

        # Chart view
        view = self.charts_view.get(robot_id)
        if view is None:
            if len(self.available_chart_views) == 0:
                view = ChartsView(self)
                self.available_chart_views.append(view)

            view = self.available_chart_views.pop(0)
            self.charts_view[robot_id] = view
            view.set_robot_id(robot_id)
            settings = QtCore.QSettings("COGIP", "monitor")
            if settings.value(f"charts_checked/{robot_id}") == "true":
                self.charts_toggled(robot_id, True)

        self.update_view_menu()

    def del_robot(self, robot_id: int) -> None:
        """
        Remove a robot.

        Parameters:
            robot_id: ID of the robot to remove
        """
        self.game_view.del_robot(robot_id)

        # Status bar
        row = self.robot_status_row.pop(robot_id)
        if not row:
            return

        for i in range(6):
            if not (item := self.status_layout.itemAtPosition(row, i)):
                continue
            widget = item.widget()
            widget.setParent(None)
            self.status_layout.removeWidget(widget)

        # Chart view
        self.charts_toggled(robot_id, False)
        view = self.charts_view.pop(robot_id, None)
        if view is None:
            return
        self.available_chart_views.append(view)
        view.closed.disconnect()
        self.update_view_menu()

    @qtSlot(Pose)
    def new_robot_pose(self, robot_id: int, pose: Pose):
        """
        Qt Slot

        Update robot position information in the status bar.

        Arguments:
            robot_id: ID of the robot
            pose: Robot pose
        """
        row = self.robot_status_row.get(robot_id)
        if not row:
            return
        self.status_layout.itemAtPosition(row, 2).widget().setText(f"{int(pose.x):> #6d}")
        self.status_layout.itemAtPosition(row, 3).widget().setText(f"{int(pose.y):> #6d}")
        self.status_layout.itemAtPosition(row, 4).widget().setText(f"{int(pose.O):> #4d}")

    @qtSlot(RobotState)
    def new_robot_state(self, robot_id: int, state: RobotState):
        """
        Qt Slot

        Update robot state information in the status bar.

        Arguments:
            robot_id: ID of the robot
            state: Robot state
        """
        row = self.robot_status_row.get(robot_id)
        if not row:
            return
        self.status_layout.itemAtPosition(row, 1).widget().setText(f"{state.cycle or 0:>#6d}")

        charts_view = self.charts_view.get(robot_id)
        if charts_view:
            charts_view.new_robot_state(state)

    @qtSlot(ShellMenu)
    def load_menu(self, menu_name: str, new_menu: ShellMenu):
        """
        Qt Slot

        Display the new menu sent by [SocketioController][cogip.tools.monitor.socketiocontroller.SocketioController].

        Once a menu has been build once, it is cached and reused.

        Arguments:
            menu_name: menu to update ("shell", "tool", ...)
            new_menu: The new menu information sent by the firmware
        """
        if menu_name not in self.menu_staked_widgets:
            self.menu_staked_widgets[menu_name] = QtWidgets.QStackedWidget()
            empty_menu_widget = QtWidgets.QStackedWidget()
            empty_menu_layout = QtWidgets.QVBoxLayout()
            empty_menu_widget.setLayout(empty_menu_layout)
            empty_menu_title = QtWidgets.QLabel("No menu loaded")
            empty_menu_title.setTextFormat(QtCore.Qt.RichText)
            empty_menu_title.setAlignment(QtCore.Qt.AlignHCenter)
            empty_menu_title.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
            empty_menu_title.setStyleSheet("font-weight: bold; color: blue")
            empty_menu_layout.addWidget(empty_menu_title)
            empty_menu_layout.addStretch()
            self.menu_staked_widgets[menu_name].addWidget(empty_menu_widget)
            self.menu_tab_widget.addTab(self.menu_staked_widgets[menu_name], menu_name)

        if menu_name not in self.menu_widgets:
            self.menu_widgets[menu_name] = {}

        widget = self.menu_widgets[menu_name].get(new_menu.name)
        if not widget:
            # Create a new menu
            widget = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout()
            widget.setLayout(layout)
            self.menu_widgets[menu_name][new_menu.name] = widget
            self.menu_staked_widgets[menu_name].addWidget(widget)

        # Clear menu to rebuild it in case it has changed
        layout = widget.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        title = QtWidgets.QLabel(new_menu.name)
        title.setTextFormat(QtCore.Qt.RichText)
        title.setAlignment(QtCore.Qt.AlignHCenter)
        title.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        title.setStyleSheet("font-weight: bold; color: blue")
        layout.addWidget(title)

        for entry in new_menu.entries:
            if entry.cmd[0] == '_':
                continue
            cmd_widget = QtWidgets.QWidget()
            cmd_layout = QtWidgets.QHBoxLayout()
            cmd_layout.setContentsMargins(0, 0, 0, 0)
            cmd_widget.setLayout(cmd_layout)
            layout.addWidget(cmd_widget)

            desc, args = split_command(entry.desc)
            button = QtWidgets.QPushButton(desc)
            cmd_layout.addWidget(button)

            for arg in args:
                edit = QtWidgets.QLineEdit()
                edit.setPlaceholderText(arg)
                edit.setToolTip(arg)
                cmd_layout.addWidget(edit)
                edit.returnPressed.connect(
                    lambda cmd=entry.cmd, layout=cmd_layout:
                        self.build_command(menu_name, cmd, layout)
                )
            button.clicked.connect(
                lambda cmd=entry.cmd, layout=cmd_layout:
                    self.build_command(menu_name, cmd, layout)
            )

        layout.addStretch()

        self.menu_staked_widgets[menu_name].setCurrentWidget(widget)

    def build_command(self, menu_name: str, cmd: str, layout: QtWidgets.QHBoxLayout):
        """
        Build command to send to [SocketioController][cogip.tools.monitor.socketiocontroller.SocketioController].

        It is built based on the command name given in arguments,
        and arguments strings fetched from the command button in the menu.

        Emit the `signal_send_command` signal with the full command string as argument.

        Arguments:
            menu_name: menu to update ("shell", "tool", ...)
            cmd: The command name
            layout: The command button containing the command arguments
        """
        i = 1
        while i < layout.count():
            edit = layout.itemAt(i).widget()
            text = edit.text()
            if text == "":
                return
            cmd += f" {text}"
            i += 1
        self.signal_send_command.emit(menu_name, cmd)

    @qtSlot()
    def add_obstacle(self):
        """
        Qt Slot

        Receive signals from "Add obstacle" action.

        Emit the `signal_add_obstacle` signal.
        """
        self.signal_add_obstacle.emit()

    @qtSlot()
    def load_obstacles(self):
        """
        Qt Slot

        Open a file dialog to select a file and load obstacles from it.
        """
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption="Select file to load obstacles",
            dir="",
            filter="JSON Files (*.json)"
        )
        if filename:
            self.signal_load_obstacles.emit(Path(filename))

    @qtSlot()
    def save_obstacles(self):
        """
        Qt Slot

        Open a file dialog to select a file and save obstacles in it.
        """
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption="Select file to save obstacles",
            dir="",
            filter="JSON Files (*.json)"
        )
        if filename:
            self.signal_save_obstacles.emit(Path(filename))

    @qtSlot()
    def load_cake_layers(self):
        """
        Qt Slot

        Open a file dialog to select a file and load cake layers from it.
        """
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption="Select file to load cake layers",
            dir="",
            filter="JSON Files (*.json)"
        )
        if filename:
            self.signal_load_cake_layers.emit(Path(filename))

    @qtSlot()
    def save_cake_layers(self):
        """
        Qt Slot

        Open a file dialog to select a file and save cake layers in it.
        """
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption="Select file to save cake layers",
            dir="",
            filter="JSON Files (*.json)",
        )
        if filename:
            self.signal_save_cake_layers.emit(Path(filename))

    def display_help_camera_control(self):
        """
        Qt Slot

        Open camera control help dialog.
        """
        self.help_camera_control.show()
        self.help_camera_control.raise_()
        self.help_camera_control.activateWindow()

    @qtSlot()
    def connected(self, state: bool):
        """
        Qt Slot

        Update the status bar with connected/disconnected state.

        Arguments:
            state: True if connected, False if disconnected
        """
        self.connected_label.setText("Connected" if state else "Disconnected")

    @qtSlot(dict)
    def config_request(self, config: Dict[str, Any]):
        properties = self.properties.get(f'{config["namespace"]}/{config["title"]}')
        if not properties:
            properties = PropertiesDialog(config, self)
            self.properties[f'{config["namespace"]}/{config["title"]}'] = properties
            properties.property_updated.connect(self.config_updated)
        else:
            properties.update_values(config)
        properties.show()
        properties.raise_()
        properties.activateWindow()

    @qtSlot(dict)
    def config_updated(self, config: Dict[str, Any]):
        self.signal_config_updated.emit(config)

    @qtSlot(dict)
    def wizard_request(self, message: dict[str, Any]):
        self.wizard = WizardDialog(message, self)
        self.wizard.response.connect(self.wizard_response)
        self.wizard.show()
        self.wizard.raise_()
        self.wizard.activateWindow()

    @qtSlot()
    def close_wizard(self):
        if self.wizard:
            self.wizard.close()
            self.wizard = None

    @qtSlot(dict)
    def wizard_response(self, response: dict[str, Any]):
        self.signal_wizard_response.emit(response)
        self.wizard = None

    def actuators_state(self, actuators_state: ActuatorsState):
        """
        Receive current state of actuators.
        Create the dialog window the first state, update it for subsequent states.

        Arguments:
            actuators_state: current actuators state
        """
        actuators_dialog = self.actuators_dialogs.get(actuators_state.robot_id)
        if not actuators_dialog:
            actuators_dialog = ActuatorsDialog(actuators_state, self)
            self.actuators_dialogs[actuators_state.robot_id] = actuators_dialog
            actuators_dialog.closed.connect(self.actuators_closed)
            actuators_dialog.new_actuator_command.connect(self.new_actuator_command)
        else:
            actuators_dialog.update_actuators(actuators_state)
        actuators_dialog.show()
        actuators_dialog.raise_()
        actuators_dialog.activateWindow()

    def new_actuator_command(self, robot_id: int, command: ActuatorCommand):
        """
        Function called when an actuator control is modified in the actuators dialog.
        Forward the command to server.

        Arguments:
            robot_id: related robot id
            command: actuator command to send
        """
        self.signal_new_actuator_command.emit(robot_id, command)

    def actuators_closed(self, robot_id: int):
        """
        Function called when the actuators dialog is closed.
        Forward information to server, to stop emitting actuators state from the robot.

        Arguments:
            robot_id: related robot id
        """
        self.signal_actuators_closed.emit(robot_id)

    def closeEvent(self, event: QtGui.QCloseEvent):
        settings = QtCore.QSettings("COGIP", "monitor")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        for robot_id, view in self.charts_view.items():
            settings.setValue(f"charts_checked/{robot_id}", view.isVisible())
        settings.setValue("dashboard_checked", self.view_dashboard_action.isChecked())
        settings.setValue("camera_params", json.dumps(self.game_view.get_camera_params()))
        super().closeEvent(event)

    def readSettings(self):
        settings = QtCore.QSettings("COGIP", "monitor")
        self.restoreGeometry(settings.value("geometry"))
        self.restoreState(settings.value("windowState"))
        if settings.value("dashboard_checked") == "true":
            self.dashboard_toggled(True)
            self.view_dashboard_action.setChecked(True)
        try:
            camera_params = json.loads(settings.value("camera_params"))
            self.game_view.set_camera_params(camera_params)
        except Exception:
            pass


def split_command(command: str) -> Tuple[str, List[str]]:
    """
    Split the full command string to separate the name of the command
    and its arguments.

    The command is in the following format:
    ```
    "command name <arg1> <arg2> ..."
    ```

    Arguments:
        command: The command string to split

    Return:
        A tuple of the command name and a list of arguments
    """
    result: List[str] = list()
    arg_match = re.findall(r"(<[\d\w]+>)", command)
    for arg in arg_match:
        result.append(arg[1:-1])
        command = command.replace(arg, "")
    command = command.strip()
    return (command, result)
