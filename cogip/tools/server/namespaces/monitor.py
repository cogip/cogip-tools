from typing import List
import socketio

from .. import logger
from ..context import Context


class MonitorNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to monitor.
    """
    def __init__(self):
        super().__init__("/monitor")
        self._connected = False
        self._context = Context()

    async def on_connect(self, sid, environ):
        if self._connected:
            logger.error("Monitor connection refused: a monitor is already connected")
            raise ConnectionRefusedError("A monitor is already connected")
        self._connected = True
        for robot_id, mode in self._context.detector_modes.items():
            if mode == "emulation":
                await self.emit("start_lidar_emulation", robot_id, namespace="/monitor")

        logger.info("Monitor connected.")

    def on_disconnect(self, sid):
        self._connected = False
        logger.info("Monitor disconnected.")

    async def on_lidar_data(self, sid, robot_id: int, lidar_data: List[int]):
        """
        Callback on lidar data.

        In emulation mode, receive Lidar data from the Monitor,
        and forward to the Detector in charge of computing dynamic obstacles.
        """
        detector_sid = self._context.detector_sids.inverse.get(robot_id)
        if detector_sid:
            await self.emit("lidar_data", lidar_data, to=detector_sid, namespace="/detector")
