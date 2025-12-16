import asyncio
from typing import TYPE_CHECKING, Any

import polling2
import socketio

from . import logger

if TYPE_CHECKING:
    from .odometry_calibration import OdometryCalibration


class SioEvents(socketio.AsyncClientNamespace):
    """
    Handle all SocketIO events received by the odometry calibration tool.
    """

    def __init__(self, calibration: "OdometryCalibration"):
        super().__init__("/calibration")
        self.calibration = calibration
        self.connected = False

    async def on_connect(self):
        """
        On connection to cogip-server.
        """
        await asyncio.to_thread(
            polling2.poll,
            lambda: self.client.connected is True,
            step=0.2,
            poll_forever=True,
        )
        logger.info("Connected to cogip-server on /calibration")
        await self.emit("connected")
        self.connected = True

    async def on_disconnect(self) -> None:
        """
        On disconnection from cogip-server.
        """
        logger.info("Disconnected from cogip-server")
        self.connected = False

    async def on_connect_error(self, data: dict[str, Any]) -> None:
        """
        On connection error.
        """
        if isinstance(data, dict) and "message" in data:
            message = data["message"]
        else:
            message = data
        logger.error(f"Connection to cogip-server failed: {message}")

    async def on_pose_reached(self) -> None:
        """
        Handle pose_reached event from copilot (via server).
        Signal that the robot has reached its target position.
        """
        logger.debug("Pose reached")
        self.calibration.pose_reached_event.set()
