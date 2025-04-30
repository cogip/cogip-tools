import asyncio
from typing import Any

import polling2
import socketio
from pydantic import TypeAdapter

from cogip import models
from cogip.models.actuators import ActuatorCommand, PositionalActuatorCommand, ServoCommand
from cogip.protobuf import PB_ActuatorCommand, PB_Command, PB_Controller, PB_PathPose, PB_Pid_Id, PB_PidEnum
from . import copilot, logger
from .menu import menu


class SioEvents(socketio.AsyncClientNamespace):
    """
    Handle all SocketIO events received by Planner.
    """

    def __init__(self, copilot: "copilot.Copilot"):
        super().__init__("/copilot")
        self.copilot = copilot
        self.connected = False

    async def on_connect(self):
        """
        On connection to cogip-server.
        """
        await asyncio.to_thread(
            polling2.poll,
            lambda: self.client.connected is True,
            step=1,
            poll_forever=True,
        )
        logger.info("Connected to cogip-server")
        await self.emit("connected")

        self.copilot.create_shared_memory()
        self.connected = True

        if self.copilot.shell_menu:
            await self.emit("menu", self.copilot.shell_menu.model_dump(exclude_defaults=True, exclude_unset=True))
        await self.emit("register_menu", {"name": "copilot", "menu": menu.model_dump()})

    def on_disconnect(self) -> None:
        """
        On disconnection from cogip-server.
        """
        logger.info("Disconnected from cogip-server")
        self.connected = False
        self.copilot.delete_shared_memory()

    async def on_connect_error(self, data: dict[str, Any]) -> None:
        """
        On connection error, check if a Planner is already connected and exit,
        or retry connection.
        """
        if isinstance(data, dict) and "message" in data:
            message = data["message"]
        else:
            message = data
        logger.error(f"Connection to cogip-server failed: {message}")

    async def on_command(self, data):
        """
        Callback on tool command message.
        """
        cmd, _, _ = data.partition(" ")
        pid_id = PB_Pid_Id()
        match cmd:
            case "angular_speed_pid_config":
                # Request angular speed pid state
                pid_id.id = PB_PidEnum.ANGULAR_SPEED_PID
                await self.copilot.pbcom.send_can_message(copilot.pid_request_uuid, pid_id)
            case "linear_speed_pid_config":
                # Request linear_speed pid state
                pid_id.id = PB_PidEnum.LINEAR_SPEED_PID
                await self.copilot.pbcom.send_can_message(copilot.pid_request_uuid, pid_id)
            case "angular_position_pid_config":
                # Request angular position pid state
                pid_id.id = PB_PidEnum.ANGULAR_POSE_PID
                await self.copilot.pbcom.send_can_message(copilot.pid_request_uuid, pid_id)
            case "linear_position_pid_config":
                # Request linear position pid state
                pid_id.id = PB_PidEnum.LINEAR_POSE_PID
                await self.copilot.pbcom.send_can_message(copilot.pid_request_uuid, pid_id)
            case _:
                logger.warning(f"Unknown command: {cmd}")

    async def on_shell_command(self, data):
        """
        Callback on shell command message.

        Build the Protobuf command message:

        * split received string at first space if any.
        * first is the command and goes to `cmd` attribute.
        * second part is arguments, if any, and goes to `desc` attribute.
        """
        response = PB_Command()
        response.cmd, _, response.desc = data.partition(" ")
        await self.copilot.pbcom.send_can_message(copilot.command_uuid, response)

    async def on_pose_start(self, data: dict[str, Any]):
        """
        Callback on pose start (from planner).
        Forward to mcu-firmware.
        """
        start_pose = models.PathPose.model_validate(data)
        pb_start_pose = PB_PathPose()
        start_pose.copy_pb(pb_start_pose)
        await self.copilot.pbcom.send_can_message(copilot.pose_start_uuid, pb_start_pose)

    async def on_pose_order(self, data: dict[str, Any]):
        """
        Callback on pose order (from planner).
        Forward to mcu-firmware.
        """
        pose_order = models.PathPose.model_validate(data)
        if self.copilot.id > 1:
            pose_order.allow_reverse = False
        pb_pose_order = PB_PathPose()
        pose_order.copy_pb(pb_pose_order)
        await self.copilot.pbcom.send_can_message(copilot.pose_order_uuid, pb_pose_order)

    async def on_actuators_start(self):
        """
        Callback on actuators_start (from dashboard).
        Forward to mcu-firmware.
        """
        await self.copilot.pbcom.send_can_message(copilot.actuators_thread_start_uuid, None)

    async def on_actuators_stop(self):
        """
        Callback on actuators_stop (from dashboard).
        Forward to mcu-firmware.
        """
        await self.copilot.pbcom.send_can_message(copilot.actuators_thread_stop_uuid, None)

    async def on_actuator_command(self, data: dict[str, Any]):
        """
        Callback on actuator_command (from dashboard).
        Forward to mcu-firmware.
        """
        command = TypeAdapter(ActuatorCommand).validate_python(data)

        pb_command = PB_ActuatorCommand()
        if isinstance(command, ServoCommand):
            command.pb_copy(pb_command.servo)
        elif isinstance(command, PositionalActuatorCommand):
            command.pb_copy(pb_command.positional_actuator)
        await self.copilot.pbcom.send_can_message(copilot.actuator_command_uuid, pb_command)

    async def on_config_updated(self, config: dict[str, Any]) -> None:
        """
        Callback on config_updated from dashboard.
        Update pid PB message and send it back to firmware.
        """
        pid_id, _, name = config["name"].partition("-")
        if pid_id and name:
            setattr(self.copilot.pb_pids[int(pid_id)], name, config["value"])
            await self.copilot.pbcom.send_can_message(copilot.pid_uuid, self.copilot.pb_pids[int(pid_id)])

    async def on_set_controller(self, controller: int):
        """
        Callback on set_controller message.
        Forward to firmware.
        """
        pb_controller = PB_Controller()
        pb_controller.id = controller
        await self.copilot.pbcom.send_can_message(copilot.controller_uuid, pb_controller)

    async def on_game_start(self):
        """
        Callback on game_start message.
        Forward to firmware.
        """
        await self.copilot.pbcom.send_can_message(copilot.game_start_uuid, None)

    async def on_game_end(self):
        """
        Callback on game_end message.
        Forward to firmware.
        """
        await self.copilot.pbcom.send_can_message(copilot.game_end_uuid, None)

    async def on_game_reset(self):
        """
        Callback on game_reset message.
        Forward to firmware.
        """
        await self.copilot.pbcom.send_can_message(copilot.game_reset_uuid, None)

    async def on_brake(self):
        """
        Callback on brake message.
        Forward to firmware.
        """
        await self.copilot.pbcom.send_can_message(copilot.brake_uuid, None)
