from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Signal as qtSignal

from cogip import logger
from cogip.models.actuators import (
    ActuatorCommand,
    ActuatorsKindEnum,
    ActuatorState,
    BoolSensor,
    BoolSensorEnum,
    PositionalActuator,
    PositionalActuatorCommand,
    PositionalActuatorEnum,
    actuator_limits,
)


class PositionalActuatorControl(QtCore.QObject):
    """
    PositionalControl class.

    Build a widget to control a positional actuator.
    """

    command_updated: qtSignal = qtSignal(object)

    def __init__(self, id: PositionalActuatorEnum, layout: QtWidgets.QGridLayout):
        """
        Class constructor.

        Arguments:
            id: ID of positional actuator to control
            layout: The parent layout
        """
        super().__init__()
        self.enabled = False
        command_schema = PositionalActuator.model_json_schema()["properties"]["command"]
        self.id = id

        row = layout.rowCount()
        minimum, maximum = actuator_limits.get(id, (command_schema.get("minimum"), command_schema.get("maximum")))

        self.label = QtWidgets.QLabel(self.id.name)
        layout.addWidget(self.label, row, 0)

        self.kind = QtWidgets.QLabel("Positional")
        layout.addWidget(self.kind, row, 1)

        self.command = QtWidgets.QSpinBox()
        self.command.setToolTip("Position command")
        self.command.setMinimum(minimum)
        self.command.setMaximum(maximum)
        self.command.setSingleStep(1)
        self.command.valueChanged.connect(self.command_changed)
        layout.addWidget(self.command, row, 2)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setToolTip("Position command")
        self.slider.setMinimum(minimum)
        self.slider.setMaximum(maximum)
        self.slider.setSingleStep(1)
        self.slider.valueChanged.connect(self.command.setValue)
        layout.addWidget(self.slider, row, 3)

        self.position = QtWidgets.QLabel()
        self.position.setToolTip("Current command")
        layout.addWidget(self.position, row, 4)

        self.label.setEnabled(False)
        self.kind.setEnabled(False)
        self.command.setEnabled(False)
        self.slider.setEnabled(False)
        self.position.setEnabled(False)

    def command_changed(self, value):
        self.slider.setValue(value)
        command = PositionalActuatorCommand(id=self.id, command=value)
        self.command_updated.emit(command)

    def update_value(self, actuator: PositionalActuator):
        if not self.enabled:
            self.enabled = True
            self.label.setEnabled(True)
            self.kind.setEnabled(True)
            self.command.setEnabled(True)
            self.slider.setEnabled(True)
            self.position.setEnabled(True)

        self.command.blockSignals(True)
        self.command.setValue(actuator.command)
        self.command.blockSignals(False)
        self.slider.blockSignals(True)
        self.slider.setValue(actuator.command)
        self.slider.blockSignals(False)
        self.position.setText(str(actuator.command))


class BoolSensorControl(QtCore.QObject):
    """
    BoolSensorControl class.

    Build a widget to show the state of a bool  sensor.
    """

    def __init__(self, id: BoolSensorEnum, layout: QtWidgets.QGridLayout):
        """
        Class constructor.

        Arguments:
            id: ID of bool sensor to display
            layout: The parent layout
        """
        super().__init__()
        self.enabled = False
        self.id = id

        row = layout.rowCount()

        self.label = QtWidgets.QLabel(self.id.name)
        layout.addWidget(self.label, row, 0)

        self.kind = QtWidgets.QLabel("Bool Sensor")
        layout.addWidget(self.kind, row, 1)

        self.state = QtWidgets.QCheckBox()
        self.state.setToolTip("State")
        self.state.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.state.setFocusPolicy(QtCore.Qt.NoFocus)
        self.state.setChecked(False)
        layout.addWidget(self.state, row, 2)

        self.label.setEnabled(False)
        self.kind.setEnabled(False)
        self.state.setEnabled(False)

    def update_value(self, actuator: BoolSensor):
        if not self.enabled:
            self.enabled = True
            self.label.setEnabled(True)
            self.kind.setEnabled(True)
            self.state.setEnabled(True)

        self.state.setChecked(actuator.state)


class ActuatorsDialog(QtWidgets.QDialog):
    """
    ActuatorsDialog class

    Build a modal for actuators remote control and monitoring.

    Attributes:
        new_actuator_command: Qt signal emitted when a actuator command is updated
        closed: Qt signal emitted when the window is hidden
    """

    closed: qtSignal = qtSignal()
    new_actuator_command: qtSignal = qtSignal(object)

    def __init__(self, parent: QtWidgets.QWidget = None):
        """
        Class constructor.

        Arguments:
            parent: The parent widget
        """
        super().__init__(parent)
        self.positional_actuators: dict[PositionalActuatorEnum, PositionalActuatorControl] = {}
        self.bool_sensors: dict[BoolSensorEnum, BoolSensorControl] = {}
        self.setWindowTitle("Actuators Control")
        self.setModal(False)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        for id in PositionalActuatorEnum:
            self.positional_actuators[id] = PositionalActuatorControl(id, layout)
            self.positional_actuators[id].command_updated.connect(self.command_updated)

        for id in BoolSensorEnum:
            self.bool_sensors[id] = BoolSensorControl(id, layout)

        self.readSettings()

    def update_actuator(self, actuator_state: ActuatorState):
        """
        Update an actuator with new values.

        Arguments:
            actuator_state: current state of an actuator
        """

        match actuator_state.kind:
            case ActuatorsKindEnum.servo:
                actuator = self.servos.get(actuator_state.id)
                if actuator is None:
                    logger.warning(f"Unknown servo ID: {actuator_state.id}")
                    return
                actuator.update_value(actuator_state)
            case ActuatorsKindEnum.positional_actuator:
                actuator = self.positional_actuators.get(actuator_state.id)
                if actuator is None:
                    logger.warning(f"Unknown positional actuator ID: {actuator_state.id}")
                    return
                actuator.update_value(actuator_state)
            case ActuatorsKindEnum.bool_sensor:
                actuator = self.bool_sensors.get(actuator_state.id)
                if actuator is None:
                    logger.warning(f"Unknown bool sensor ID: {actuator_state.id}")
                    return
                actuator.update_value(actuator_state)

    def command_updated(self, command: ActuatorCommand):
        """
        Emit updated values with namespace, name and value.
        """
        self.new_actuator_command.emit(command)

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        Hide the window.

        Arguments:
            event: The close event (unused)
        """
        settings = QtCore.QSettings("COGIP", "monitor")
        settings.setValue("properties/actuators", self.saveGeometry())

        self.closed.emit()
        event.accept()
        super().closeEvent(event)

    def readSettings(self):
        settings = QtCore.QSettings("COGIP", "monitor")
        self.restoreGeometry(settings.value("properties/actuators"))
