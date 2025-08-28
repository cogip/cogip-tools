from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Signal as qtSignal

help_text = """
| Keyboard | Mouse | Action |
| --- | --- | --- |
| Left or Q | Left button + Mouse left | Move the scene left |
| Right or D | Left button + Mouse right | Move the scene right |
| Down or S | Left button + Mouse down | Move the scene down |
| Up or Z | Left button + Mouse up | Move the scene up |
| Space | | Display top view |
| Return | | Restore default view |
| Shift + (Left or Q) | Right button + Mouse left | Rotate on Y-axis |
| Shift + (Right or D) | Right button + Mouse right | Rotate on Y-axis |
| Shift + (Down or S) | Right button + Mouse down | Rotate on X-axis |
| Shift + (Up or Z) | Right button + Mouse right | Rotate on X-axis |
| Ctrl + (Left or Q) | Middle button + Mouse left | Rotate on Z-axis |
| Ctrl + (Right or D) | Middle button + Mouse right | Rotate on Z-axis |
| Ctrl + (Down or S) | Wheel | Zoom out |
| Ctrl + (Up or Z) | Wheel | Zoom in |
"""


class HelpCameraControlDialog(QtWidgets.QDialog):
    """HelpCameraControlDialog class

    Build a help modal for camera control.

    Attributes:
        saved_geometry: Saved window position
        closed: Qt signal emitted when the window is hidden
    """

    closed: qtSignal = qtSignal()

    def __init__(self, parent: QtWidgets.QWidget = None):
        """
        Class constructor.

        Arguments:
            parent: The parent widget
        """
        super().__init__(parent)

        self.setWindowTitle("Camera Control")
        self.setModal(False)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        browser = QtWidgets.QTextBrowser()
        layout.addWidget(browser)

        browser.document().setMarkdown(help_text)

        self.resize(580, 395)

        self.readSettings()

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        Hide the window.

        Arguments:
            event: The close event (unused)
        """
        settings = QtCore.QSettings("COGIP", "monitor")
        settings.setValue("help/geometry", self.saveGeometry())

        self.closed.emit()
        event.accept()
        super().closeEvent(event)

    def readSettings(self):
        settings = QtCore.QSettings("COGIP", "monitor")
        self.restoreGeometry(settings.value("help/geometry"))
