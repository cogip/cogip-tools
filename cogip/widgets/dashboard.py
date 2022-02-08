from functools import partial

from PySide6 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets
from PySide6.QtCore import Signal as qtSignal


class Dashboard(QtWidgets.QDialog):
    """Dashboard class

    Build dashboard modal.
    This modal embbeds a web browser to display the content from the Copilot web server
    as it would display on the robot screen.
    Multiple screen sizes and resolutions are available to test rendering on different screens.

    Attributes:
        saved_geometry: Saved window position
        closed: Qt signal emitted when the window is hidden
        screen_sizes: available screens sizes in inches and corresponding resolutions
    """
    saved_geometry: QtCore.QRect = None
    closed: qtSignal = qtSignal()
    screen_sizes = {
        5: (800, 480),
        7: (1024, 600)
    }

    def __init__(self, url: str, parent: QtWidgets.QWidget = None):
        """
        Class constructor.

        Arguments:
            url: URL of the copilot web server
            parent: The parent widget
        """
        super().__init__(parent)

        self.screen_radios = {}

        self.setWindowTitle("Dashboard")
        self.setModal(False)

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        resolution_group = QtWidgets.QGroupBox("Screen Size:")
        resolution_layout = QtWidgets.QHBoxLayout()
        resolution_layout.addStretch(1)
        for inches, resolution in self.screen_sizes.items():
            radio = QtWidgets.QRadioButton(f"{inches} inches ({resolution[0]}x{resolution[1]})")
            radio.toggled.connect(partial(self.set_resolution, resolution[0], resolution[1]))
            resolution_layout.addWidget(radio)
            self.screen_radios[inches] = radio
        resolution_layout.addStretch(1)
        resolution_group.setLayout(resolution_layout)
        self.layout.addWidget(resolution_group)

        self.browser = QtWebEngineWidgets.QWebEngineView()
        self.browser.load(QtCore.QUrl(url))
        self.layout.addWidget(self.browser)

        self.screen_radios[7].setChecked(True)

    def restore_saved_geometry(self):
        """
        Reuse the position of the last displayed window for the current window.
        """
        if self.saved_geometry:
            self.setGeometry(self.saved_geometry)

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        Hide the window.

        Arguments:
            event: The close event (unused)
        """
        self.saved_geometry = self.geometry()
        self.closed.emit()
        event.accept()

    def set_resolution(self, width: int, height: int, checked: bool) -> None:
        """
        Change the resolution of the web view.
        This function is called when a radio button selecting the screen size is toggled (on and off).

        Arguments:
            width: new width in pixels
            height: new height in pixels
            checked: if the radio button was checked or unckecked
        """
        if checked:
            self.browser.setMaximumSize(QtCore.QSize(width, height))
            self.browser.setMinimumSize(QtCore.QSize(width, height))
            self.adjustSize()
            self.browser.reload()