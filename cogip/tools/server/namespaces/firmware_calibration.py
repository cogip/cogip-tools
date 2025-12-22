from typing import Any

import socketio

from .. import logger, server
from ..context import Context


class FirmwareCalibrationNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to firmware calibration clients.
    Only one client connection is allowed at a time.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/calibration")
        self.cogip_server = cogip_server
        self.context = Context()

    async def on_connect(self, sid, environ):
        if self.context.calibration_sid:
            message = "A calibration client is already connected"
            logger.error(f"Calibration connection refused: {message}")
            raise ConnectionRefusedError(message)

    async def on_connected(self, sid):
        logger.info("Calibration client connected.")
        self.context.calibration_sid = sid

    async def on_disconnect(self, sid):
        self.context.calibration_sid = None
        logger.info("Calibration client disconnected.")

    async def on_pose_start(self, sid, pose: dict[str, Any]):
        """
        Callback on pose start (reset robot position).
        Forward to copilot.
        """
        logger.info(f"[calibration => copilot] Pose start: {pose}")
        await self.emit("pose_start", pose, namespace="/copilot")

    async def on_pose_order(self, sid, pose: dict[str, Any]):
        """
        Callback on pose order.
        Forward to pose to copilot and dashboards.
        """
        logger.info(f"[calibration => copilot] Pose order: {pose}")
        await self.emit("pose_order", pose, namespace="/copilot")
        await self.emit("pose_order", (self.context.robot_id, pose), namespace="/dashboard")
