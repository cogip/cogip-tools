from typing import Any

import polling2
import socketio

from . import detector, logger
from .menu import menu


class SioEvents(socketio.ClientNamespace):
    """
    Handle all SocketIO events received by Detector.
    """

    def __init__(self, detector: "detector.Detector"):
        super().__init__("/detector")
        self.detector = detector

    def on_connect(self):
        """
        On connection to cogip-server, start detector threads.
        """
        polling2.poll(lambda: self.client.connected is True, step=0.2, poll_forever=True)
        logger.info("Connected to cogip-server")
        self.emit("connected", self.detector.lidar_port is None)
        self.emit("register_menu", {"name": "detector", "menu": menu.model_dump()})
        self.detector.start()

    def on_disconnect(self) -> None:
        """
        On disconnection from cogip-server, stop detector threads.
        """
        logger.info("Disconnected from cogip-server")
        self.detector.stop()
        self.detector.delete_shared_memory()

    def on_connect_error(self, data: dict[str, Any]) -> None:
        """
        On connection error, check if a Detector is already connected and exit,
        or retry connection.
        """
        logger.error(f"Connect to cogip-server error: {data = }")
        if (
            data
            and isinstance(data, dict)
            and (message := data.get("message"))
            and message == "A detector is already connected"
        ):
            logger.error(message)
            self.detector.retry_connection = False
            return

    def on_command(self, cmd: str) -> None:
        """
        Callback on command message from dashboard.
        """
        if cmd == "config":
            # Get JSON Schema
            schema = self.detector.properties.model_json_schema()
            # Add namespace in JSON Schema
            schema["namespace"] = "/detector"
            schema["sio_event"] = "config_updated"
            # Add current values in JSON Schema
            for prop, value in self.detector.properties.model_dump().items():
                schema["properties"][prop]["value"] = value
            # Send config
            self.emit("config", schema)
        else:
            logger.warning(f"Unknown command: {cmd}")

    def on_config_updated(self, config: dict[str, Any]) -> None:
        value = config["value"]
        self.detector.properties.__setattr__(name := config["name"], value)
        match name:
            case "refresh_interval":
                self.detector.obstacles_updater_loop.interval = value
            case "min_distance":
                if self.detector.lidar:
                    self.detector.lidar.set_min_distance(value)
            case "max_distance":
                if self.detector.lidar:
                    self.detector.lidar.set_max_distance(value)
            case "min_intensity":
                if self.detector.lidar:
                    self.detector.lidar.set_min_intensity(value)
            case "sensor_delay":
                self.detector.lidar_data_converter.set_pose_current_index(value)
