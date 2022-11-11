from typing import Any, Dict
import socketio

from .. import logger
from ..context import Context
from ..recorder import GameRecorder


class PlannerNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to planner.
    """
    def __init__(self):
        super().__init__("/planner")
        self._connected = False
        self._context = Context()
        self._recorder = GameRecorder()

    def on_connect(self, sid, environ):
        if self._connected:
            logger.error("Planner connection refused: a planner is already connected")
            raise ConnectionRefusedError("A planner is already connected")
        self._connected = True
        logger.info("Planner connected.")

    def on_disconnect(self, sid):
        self._connected = False
        logger.info("Planner disconnected.")

    async def on_menu(self, sid, menu):
        """
        Callback on menu.
        """
        self._context.planner_menu = menu
        await self.emit("planner_menu", menu, namespace="/dashboard")

    async def on_pose_start(self, sid, data: Dict[str, Any]):
        """
        Callback on pose start.
        Forward to pose to copilot.
        """
        await self.emit("pose_start", data, namespace="/copilot")

    async def on_pose_order(self, sid, data: Dict[str, Any]):
        """
        Callback on pose order.
        Forward to pose to copilot and dashboards.
        """
        await self.emit("pose_order", data, namespace="/copilot")
        await self.emit("pose_order", data, namespace="/dashboard")
        await self._recorder.async_record({"pose_order": data})