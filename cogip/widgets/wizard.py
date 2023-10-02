from typing import Any

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot

from .. import logger


class BooleanWizard(QtCore.QObject):
    """
    BooleanWizard class.

    Build a widget to input a boolean.
    """
    response: qtSignal = qtSignal(bool)

    def __init__(self, wizard: dict[str, Any], parent: QtWidgets.QWidget):
        """
        Class constructor.

        Arguments:
            wizard: wizard request
            parent: the parent widget
        """
        super().__init__()
        self.wizard = wizard

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignHCenter)
        parent.setLayout(layout)

        self.input = QtWidgets.QCheckBox()
        self.input.setChecked(self.wizard.get("value", False))
        layout.addWidget(self.input)

        send_button = QtWidgets.QPushButton("Send")
        layout.addWidget(send_button)
        send_button.clicked.connect(self.send)

    @qtSlot()
    def send(self, clicked: bool):
        """
        Send chosen value to parent dialog on Send button click.
        """
        self.response.emit(self.input.isChecked())


class InputWizard(QtCore.QObject):
    """
    InputWizard class.

    Build a widget to input an integer, float or string.
    """
    response: qtSignal = qtSignal(str)

    def __init__(self, wizard: dict[str, Any], parent: QtWidgets.QWidget):
        """
        Class constructor.

        Arguments:
            wizard: wizard request
            parent: the parent widget
        """
        super().__init__()
        self.wizard = wizard

        layout = QtWidgets.QVBoxLayout()
        parent.setLayout(layout)

        match self.wizard["type"]:
            case "integer":
                self.input = QtWidgets.QSpinBox()
                self.input.setValue(int(self.wizard.get("value", 0)))
            case "floating":
                self.input = QtWidgets.QDoubleSpinBox()
                self.input.setValue(float(self.wizard.get("value", 0.0)))
            case "str":
                self.input = QtWidgets.QLineEdit()
                self.input.setText(self.wizard.get("value", ""))
        layout.addWidget(self.input)
        send_button = QtWidgets.QPushButton("Send")
        layout.addWidget(send_button)
        send_button.clicked.connect(self.send)

    @qtSlot()
    def send(self, clicked: bool):
        """
        Send chosen value to parent dialog on Send button click.
        """
        self.response.emit(self.input.text())


class MessageWizard(QtCore.QObject):
    """
    MessageWizard class.

    Build a widget to display a message.
    """
    response: qtSignal = qtSignal(str)

    def __init__(self, wizard: dict[str, Any], parent: QtWidgets.QWidget):
        """
        Class constructor.

        Arguments:
            wizard: wizard request
            parent: the parent widget
        """
        super().__init__()
        self.wizard = wizard

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignHCenter)
        parent.setLayout(layout)

        self.input = QtWidgets.QLabel()
        self.input.setText(self.wizard.get("value", False))
        layout.addWidget(self.input)

        send_button = QtWidgets.QPushButton("Ok")
        layout.addWidget(send_button)
        send_button.clicked.connect(self.send)

    @qtSlot()
    def send(self, clicked: bool):
        """
        Send chosen value to parent dialog on Send button click.
        """
        self.response.emit("")


class ChoiceWizard(QtCore.QObject):
    """
    ChoiceWizard class.

    Build a widget to choose a integer, float or string from a list.
    """
    response: qtSignal = qtSignal(str)

    def __init__(self, wizard: dict[str, Any], parent: QtWidgets.QWidget):
        """
        Class constructor.

        Arguments:
            wizard: wizard request
            parent: the parent widget
        """
        super().__init__()
        self.wizard = wizard

        layout = QtWidgets.QVBoxLayout()
        parent.setLayout(layout)

        self.buttons = QtWidgets.QButtonGroup(layout)
        for v in wizard["choices"]:
            button = QtWidgets.QRadioButton(str(v))
            self.buttons.addButton(button)
            button.setChecked(v == wizard["value"])
            layout.addWidget(button)
        send_button = QtWidgets.QPushButton("Send")
        layout.addWidget(send_button)
        send_button.clicked.connect(self.send)

    @qtSlot()
    def send(self, clicked: bool):
        """
        Send chosen value to parent dialog on Send button click.
        """
        self.response.emit(self.buttons.checkedButton().text())


class SelectWizard(QtCore.QObject):
    """
    SelectWizard class.

    Build a widget to select one or more integer, float or string from a list.
    """
    response: qtSignal = qtSignal(list)

    def __init__(self, wizard: dict[str, Any], parent: QtWidgets.QWidget):
        """
        Class constructor.

        Arguments:
            wizard: wizard request
            parent: the parent widget
        """
        super().__init__()
        self.wizard = wizard

        layout = QtWidgets.QVBoxLayout()
        parent.setLayout(layout)

        self.buttons = []
        for v in wizard["choices"]:
            button = QtWidgets.QCheckBox(str(v))
            self.buttons.append(button)
            button.setChecked(v in wizard["value"])
            layout.addWidget(button)
        send_button = QtWidgets.QPushButton("Send")
        layout.addWidget(send_button)
        send_button.clicked.connect(self.send)

    @qtSlot()
    def send(self, clicked: bool):
        """
        Send chosen value to parent dialog on Send button click.
        """
        print([button.text() for button in self.buttons if button.isChecked()])
        self.response.emit([button.text() for button in self.buttons if button.isChecked()])


class CampWizard(QtCore.QObject):
    """
    CampWizard class.

    Build a widget to select a string.
    """
    response: qtSignal = qtSignal(str)

    def __init__(self, wizard: dict[str, Any], parent: QtWidgets.QWidget):
        """
        Class constructor.

        Arguments:
            wizard: wizard request
            parent: the parent widget
        """
        super().__init__()
        self.wizard = wizard

        layout = QtWidgets.QVBoxLayout()
        parent.setLayout(layout)

        button_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(button_layout)

        self.buttons = QtWidgets.QButtonGroup()

        self.button_blue = QtWidgets.QRadioButton()
        self.button_blue.setObjectName("blueCamp")
        self.button_blue.setCheckable(True)
        self.button_blue.setStyleSheet(
            """
            QRadioButton#blueCamp {
                border-color: #005CE6;
                background-color: #005CE6;
                border-width: 2px;
                border-radius: 10px;
                border-style: inset;
                min-width: 6em;
                padding: 6px;
            }
            QRadioButton#blueCamp:checked {
                border-color: beige;
                border-style: outset;
            }
            QRadioButton#blueCamp::indicator {
                border-width: 0;
            }
            """)
        self.buttons.addButton(self.button_blue)
        button_layout.addWidget(self.button_blue)

        self.button_green = QtWidgets.QRadioButton()
        self.button_green.setObjectName("greenCamp")
        self.button_blue.setCheckable(True)
        self.button_green.setStyleSheet(
            """
            QRadioButton#greenCamp {
                border-color: #00AA12;
                background-color: #00AA12;
                border-width: 2px;
                border-radius: 10px;
                border-style: inset;
                min-width: 6em;
                padding: 6px;
            }
            QRadioButton#greenCamp:checked {
                border-color: beige;
                border-style: outset;
            }
            QRadioButton#greenCamp::indicator {
                border-width: 0;
            }
            """)
        self.buttons.addButton(self.button_green)
        button_layout.addWidget(self.button_green)

        if wizard["value"] == "blue":
            self.button_blue.setChecked(True)
        else:
            self.button_green.setChecked(True)
        send_button = QtWidgets.QPushButton("Send")
        layout.addWidget(send_button)
        send_button.clicked.connect(self.send)

    @qtSlot()
    def send(self, clicked: bool):
        color = "blue" if self.button_blue.isChecked() else "green"
        self.response.emit(color)


class WizardDialog(QtWidgets.QDialog):
    """
    WizardDialog class

    Build a modal for wizard request.

    Attributes:
        property_updated: Qt signal emitted when a property is updated
        closed: Qt signal emitted when the window is hidden
    """
    response: qtSignal = qtSignal(dict)

    def __init__(self, message: dict[str, Any], parent: QtWidgets.QWidget = None):
        """
        Class constructor.

        Arguments:
            config: JSON Schema of properties with current values and namespace
            parent: The parent widget
        """
        super().__init__(parent)
        self.message = message
        self.setWindowTitle(self.message["name"])
        self.setModal(False)
        self.setMinimumWidth(300)

        match wizard_type := self.message["type"]:
            case "boolean":
                self.wizard = BooleanWizard(self.message, self)
            case "integer" | "floating" | "str":
                self.wizard = InputWizard(self.message, self)
            case "message":
                self.wizard = MessageWizard(self.message, self)
            case "choice_integer" | "choice_floating" | "choice_str":
                self.wizard = ChoiceWizard(self.message, self)
            case "select_integer" | "select_floating" | "select_str":
                self.wizard = SelectWizard(self.message, self)
            case "camp":
                self.wizard = CampWizard(self.message, self)
            case _:
                logger.warning(f"Wizard message '{wizard_type} unsupported'")
                return

        self.wizard.response.connect(self.respond)
        self.rejected.connect(self.force_close)

    def respond(self, response: str | list[str]):
        self.message["value"] = response
        self.response.emit(self.message)
        self.accept()

    def force_close(self):
        self.message["value"] = None
        self.response.emit(self.message)
        self.accept()
