import os
import sys
from pathlib import Path
from typing import Any

import PySide6
import typer
from PySide6 import QtCore
from PySide6.QtCore import QCoreApplication, QObject, QUrl
from PySide6.QtGui import QFont, QGuiApplication, QPalette, QWindow
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtQuickControls2 import QQuickStyle

from cogip.models import models
from . import logger
from .obstacle import ObstacleStorage
from .sio_client import SocketioClient
from .table import Table
from .view3D import View3DBackend


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
    if os.getenv("QT_QPA_PLATFORM") is None:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    QCoreApplication.setOrganizationName("cogip")
    QCoreApplication.setOrganizationDomain("cogip.tools")
    QCoreApplication.setApplicationName("COGIP Monitor")

    sio_client = SocketioClient(url)

    app = QGuiApplication(sys.argv)
    app.setFont(QFont("Ubuntu", 11))

    QQuickStyle.setStyle("Fusion")

    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, "#2a2a2a")
    palette.setColor(QPalette.ColorRole.WindowText, "#ffffff")
    palette.setColor(QPalette.ColorRole.Base, "#2a2a2a")
    palette.setColor(QPalette.ColorRole.AlternateBase, "#272727")
    palette.setColor(QPalette.ColorRole.ToolTipBase, "#ffffdc")
    palette.setColor(QPalette.ColorRole.ToolTipText, "#000000")
    palette.setColor(QPalette.ColorRole.Text, "#ffffff")
    palette.setColor(QPalette.ColorRole.Button, "#2a2a2a")
    palette.setColor(QPalette.ColorRole.ButtonText, "#ffffff")
    palette.setColor(QPalette.ColorRole.BrightText, "#ffffff")
    palette.setColor(QPalette.ColorRole.Highlight, "#e95420")
    palette.setColor(QPalette.ColorRole.HighlightedText, "#ffffff")
    palette.setColor(QPalette.ColorRole.Light, "#343434")
    palette.setColor(QPalette.ColorRole.Midlight, "#2f2f2f")
    palette.setColor(QPalette.ColorRole.Dark, "#252525")
    palette.setColor(QPalette.ColorRole.Mid, "#2f2f2f")
    palette.setColor(QPalette.ColorRole.Shadow, "#020202")
    palette.setColor(QPalette.ColorRole.Link, "#308cc6")
    palette.setColor(QPalette.ColorRole.LinkVisited, "#ff00ff")
    palette.setColor(QPalette.ColorRole.NoRole, "#000000")
    palette.setColor(QPalette.ColorRole.PlaceholderText, "#9b9b9b")
    palette.setColor(QPalette.ColorRole.Accent, "#308cc6")
    app.setPalette(palette)

    qmlRegisterType(View3DBackend, "View3DBackend", 1, 0, "View3DBackend")

    engine = QQmlApplicationEngine()

    # Add PySide6's QML import path
    engine.addImportPath(PySide6.__path__[0])

    qml_file = Path(__file__).parent / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        logger.error("No root objects loaded, exiting.")
        sys.exit(-1)

    root: QWindow = engine.rootObjects()[0]
    view3d_qml = root.findChild(QObject, "view")
    view3d_backend = View3DBackend(view3d_qml)
    view3d_qml.setProperty("view3DBackend", view3d_backend)
    root.setProperty("isConnected", False)
    root.setProperty("starterChecked", False)
    root.setProperty("socketClient", sio_client)
    root.setProperty("toolMenu", {"name": "", "entries": []})
    obstacle_storage = ObstacleStorage()
    root.setProperty("obstacleStorage", obstacle_storage)

    table = Table(view3d_qml.findChild(QObject, "table"))
    root.setProperty("table", table)

    def request_quit() -> None:
        QtCore.QTimer.singleShot(0, app.quit)

    def handle_connected(connected: bool) -> None:
        def update_state() -> None:
            root.setProperty("isConnected", connected)
            if not connected:
                root.setProperty("toolMenu", {"name": "", "entries": []})
                root.setProperty("starterChecked", False)
                QtCore.QMetaObject.invokeMethod(
                    root,
                    "closeAllConfigWindows",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                )
                QtCore.QMetaObject.invokeMethod(
                    root,
                    "closeWizardWindow",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                )

        QtCore.QTimer.singleShot(0, update_state)

    def handle_tool_menu(menu: models.ShellMenu) -> None:
        filtered_entries: list[dict[str, str]] = []
        for entry in menu.entries:
            if entry.cmd.startswith("_"):
                continue
            entry_dict = {"cmd": entry.cmd, "desc": entry.desc}
            if entry.cmd == "exit":
                filtered_entries.insert(0, entry_dict)
            else:
                filtered_entries.append(entry_dict)
        payload = {
            "name": menu.name,
            "entries": filtered_entries,
        }

        QtCore.QTimer.singleShot(0, lambda: root.setProperty("toolMenu", payload))

    def handle_wizard_request(data: dict[str, Any]) -> None:
        QtCore.QMetaObject.invokeMethod(
            root,
            "openWizardWindow",
            QtCore.Qt.ConnectionType.QueuedConnection,
            QtCore.Q_ARG("QVariant", data),
        )

    def handle_close_wizard() -> None:
        QtCore.QMetaObject.invokeMethod(
            root,
            "closeWizardWindow",
            QtCore.Qt.ConnectionType.QueuedConnection,
        )

    def handle_starter_changed(pushed: bool) -> None:
        QtCore.QTimer.singleShot(0, lambda: root.setProperty("starterChecked", pushed))

    sio_client.signal_connected.connect(handle_connected)
    sio_client.signal_exit.connect(request_quit)
    sio_client.signal_add_robot.connect(view3d_backend.handle_add_robot)
    sio_client.signal_del_robot.connect(view3d_backend.handle_del_robot)
    sio_client.signal_robot_path.connect(view3d_backend.handle_robot_path)
    sio_client.signal_tool_menu.connect(handle_tool_menu)
    sio_client.signal_wizard_request.connect(handle_wizard_request)
    sio_client.signal_close_wizard.connect(handle_close_wizard)
    sio_client.signal_starter_changed.connect(handle_starter_changed)

    sio_client.start()

    ret = app.exec()

    sio_client.stop()

    sys.exit(ret)


def main():
    """
    Starts the copilot.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-monitor` script using this function as entrypoint.
    """
    typer.run(main_opt)
