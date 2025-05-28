from typing import Any

import socketio

from .. import logger, server
from ..context import Context


class PlannerNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to planner.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/planner")
        self.cogip_server = cogip_server
        self.context = Context()
        self.connected = False
        self.context.planner_sid = None

    async def on_connect(self, sid, environ):
        if self.context.planner_sid:
            logger.error("Planner connection refused: a planner is already connected")
            raise ConnectionRefusedError("A planner is already connected")
        self.context.planner_sid = sid

    async def on_connected(self, sid, virtual: bool):
        logger.info(f"Planner connected (virtual={virtual}).")
        self.context.virtual_planner = virtual
        if self.context.copilot_sid:
            await self.emit("copilot_connected", namespace="/planner")

    def on_disconnect(self, sid):
        self.context.planner_sid = None
        logger.info("Planner disconnected.")

    async def on_register_menu(self, sid, data: dict[str, Any]):
        """
        Callback on register_menu.
        """
        await self.cogip_server.register_menu("planner", data)

    async def on_pose_start(self, sid, pose: dict[str, Any]):
        """
        Callback on pose start.
        Forward to pose to copilot.
        """
        logger.info(f"[planner => copilot] Pose start: {pose}")
        await self.emit("pose_start", pose, namespace="/copilot")

    async def on_pose_order(self, sid, pose: dict[str, Any]):
        """
        Callback on pose order.
        Forward to pose to copilot and dashboards.
        """
        logger.info(f"[planner => copilot] Pose order: {pose}")
        await self.emit("pose_order", pose, namespace="/copilot")
        await self.emit("pose_order", (self.context.robot_id, pose), namespace="/dashboard")

    async def on_wizard(self, sid, message: list[dict[str, Any]]):
        """
        Callback on wizard message.
        Forward to dashboard.
        """
        message["namespace"] = "/planner"
        await self.emit("wizard", message, namespace="/dashboard")

    async def on_set_controller(self, sid, controller: int):
        """
        Callback on set_controller message.
        Forward to copilot.
        """
        await self.emit("set_controller", controller, namespace="/copilot")

    async def on_path(self, sid, path: list[dict[str, float]]):
        """
        Callback on robot path.
        Forward the path to dashboard.
        """
        await self.emit("path", (self.context.robot_id, path), namespace="/dashboard")

    async def on_config(self, sid, config: dict[str, Any]):
        """
        Callback on config message.
        """
        await self.emit("config", config, namespace="/dashboard")

    async def on_cmd_reset(self, sid):
        """
        Callback on cmd_reset message.
        """
        await self.emit("cmd_reset", namespace="/monitor")

    async def on_starter_changed(self, sid, pushed: bool):
        """
        Callback on starter_pushed message.
        """
        await self.emit("starter_changed", (self.context.robot_id, pushed), namespace="/dashboard")

    async def on_close_wizard(self, sid):
        """
        Callback on close_wizard message.
        """
        await self.emit("close_wizard", namespace="/dashboard")

    async def on_game_start(self, sid):
        """
        Callback on game_start message.
        """
        logger.info("[planner => copilot] Game started.")
        await self.emit("game_start", namespace="/copilot")

    async def on_game_end(self, sid):
        """
        Callback on game_end message.
        """
        logger.info("[planner => copilot] Game ended.")
        await self.emit("game_end", namespace="/copilot")

    async def on_robot_end(self, sid):
        """
        Callback on robot_end message.
        """
        logger.info("[planner => copilot] Robot ended.")
        await self.emit("game_end", namespace="/copilot")

    async def on_game_reset(self, sid):
        """
        Callback on game_reset message.
        """
        logger.info("[planner => copilot] Game reset.")
        await self.emit("game_reset", namespace="/copilot")

    async def on_score(self, sid, score: int):
        """
        Callback on score message.
        """
        await self.emit("score", score, namespace="/dashboard")

    async def on_start_countdown(self, sid, robot_id: int, countdown: int, timestamp: str, color: str | None):
        """
        Callback on start_countdown message.
        """
        logger.info(f"[planner => beacon] Start countdown: {countdown}.")
        await self.emit("start_countdown", (robot_id, countdown, timestamp, color), namespace="/beacon")

    async def on_actuator_command(self, sid, data):
        """
        Callback on actuator_command message.
        """
        logger.info(f"[planner => copilot] Actuator command: {data}")
        await self.emit("actuator_command", data, namespace="/copilot")

    async def on_actuator_init(self, sid):
        """
        Callback on actuator_init message.
        """
        logger.info("[planner => copilot] Actuator init.")
        await self.emit("actuator_init", namespace="/copilot")

    async def on_start_video_record(self, sid):
        """
        Callback on start_video_record message.
        """
        await self.emit("start_video_record", namespace="/robotcam")

    async def on_stop_video_record(self, sid):
        """
        Callback on stop_video_record message.
        """
        await self.emit("stop_video_record", namespace="/robotcam")

    async def on_brake(self, sid):
        """
        Callback on brake message.
        """
        logger.info("[planner => copilot] Brake.")
        await self.emit("brake", namespace="/copilot")

    async def on_pami_reset(self, sid):
        """
        Callback on pami_reset message.
        """
        logger.info("[planner => beacon] PAMI reset.")
        await self.emit("pami_reset", namespace="/beacon")

    async def on_pami_camp(self, sid, data):
        """
        Callback on pami_camp message.
        """
        await self.emit("pami_camp", data, namespace="/beacon")

    async def on_pami_table(self, sid, data):
        """
        Callback on pami_table message.
        """
        await self.emit("pami_table", data, namespace="/beacon")

    async def on_pami_play(self, sid, timestamp: str):
        """
        Callback on pami_play message.
        """
        logger.info("[planner => beacon] PAMI play.")
        await self.emit("pami_play", timestamp, namespace="/beacon")
