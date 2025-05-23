import asyncio
import time

import socketio
from google.protobuf.json_format import MessageToDict

from cogip import models
from cogip.cpp.libraries.models import PoseBuffer as SharedPoseBuffer
from cogip.cpp.libraries.shared_memory import LockName, SharedMemory, WritePriorityLock
from cogip.models.actuators import ActuatorsKindEnum
from cogip.protobuf import PB_ActuatorState, PB_Pid, PB_PidEnum, PB_Pose, PB_State
from . import logger
from .pbcom import PBCom, pb_exception_handler
from .pid import Pid
from .sio_events import SioEvents

# Motion Control: 0x1000 - 0x1FFF
state_uuid: int = 0x1001
pose_order_uuid: int = 0x1002
pose_reached_uuid: int = 0x1003
pose_start_uuid: int = 0x1004
pid_request_uuid: int = 0x1005
pid_uuid: int = 0x1006
brake_uuid: int = 0x1007
controller_uuid: int = 0x1008
blocked_uuid: int = 0x1009
# Actuators: 0x2000 - 0x2FFF
actuators_thread_start_uuid: int = 0x2001
actuators_thread_stop_uuid: int = 0x2002
actuator_state_uuid: int = 0x2003
actuator_command_uuid: int = 0x2004
# Service: 0x3000 - 0x3FFF
reset_uuid: int = 0x3001
copilot_connected_uuid: int = 0x3002
copilot_disconnected_uuid: int = 0x3003
# Game: 0x4000 - 0x4FFF
game_start_uuid: int = 0x4001
game_end_uuid: int = 0x4002
game_reset_uuid: int = 0x4003
# Board: 0xF000 - 0xFFFF


class Copilot:
    """
    Main copilot class.
    """

    loop: asyncio.AbstractEventLoop = None  # Event loop to use for all coroutines

    def __init__(self, server_url: str, id: int, can_channel: str, can_bitrate: int, canfd_data_bitrate: int):
        """
        Class constructor.

        Arguments:
            server_url: server URL
            id: robot id
            can_channel: CAN channel connected to STM32 device
            can_bitrate: CAN bitrate
            canfd_data_bitrate: CAN data bitrate
        """
        self.server_url = server_url
        self.id = id
        self.retry_connection = True
        self.shell_menu: models.ShellMenu | None = None
        self.pb_pids: dict[PB_PidEnum, PB_Pid] = {}

        self.shared_memory: SharedMemory | None = None
        self.shared_pose_current_buffer: SharedPoseBuffer | None = None
        self.shared_pose_current_lock: WritePriorityLock | None = None

        self.sio = socketio.AsyncClient(logger=False)
        self.sio_events = SioEvents(self)
        self.sio.register_namespace(self.sio_events)

        pb_message_handlers = {
            reset_uuid: self.handle_reset,
            pose_order_uuid: self.handle_message_pose,
            state_uuid: self.handle_message_state,
            pose_reached_uuid: self.handle_pose_reached,
            actuator_state_uuid: self.handle_actuator_state,
            pid_uuid: self.handle_pid,
            blocked_uuid: self.handle_blocked,
        }

        self.pbcom = PBCom(can_channel, can_bitrate, canfd_data_bitrate, pb_message_handlers)

    def create_shared_memory(self):
        self.shared_memory = SharedMemory(f"cogip_{self.id}")
        self.shared_pose_current_buffer = self.shared_memory.get_pose_current_buffer()
        self.shared_pose_current_lock = self.shared_memory.get_lock(LockName.PoseCurrent)

    def delete_shared_memory(self):
        self.shared_pose_current_buffer = None
        self.shared_pose_current_lock = None
        self.shared_memory = None

    async def run(self):
        """
        Start copilot.
        """
        self.loop = asyncio.get_running_loop()

        self.retry_connection = True
        await self.try_connect()

        await self.pbcom.send_can_message(copilot_connected_uuid, None)

        await self.pbcom.run()

    async def try_connect(self):
        """
        Poll to wait for the first connection.
        Disconnections/reconnections are handle directly by the client.
        """
        while self.retry_connection:
            try:
                await self.sio.connect(self.server_url, namespaces=["/copilot"])
            except socketio.exceptions.ConnectionError:
                time.sleep(2)
                continue
            break

    async def handle_reset(self) -> None:
        """
        Handle reset message. This means that the robot has just booted.

        Send a reset message to all connected clients.
        """
        logger.info("[CAN] Received reset")
        await self.pbcom.send_can_message(copilot_connected_uuid, None)
        await self.sio_events.emit("reset")

    @pb_exception_handler
    async def handle_message_pose(self, message: bytes | None = None) -> None:
        """
        Send robot pose received from the robot to connected monitors and detector.
        """
        pb_pose = PB_Pose()

        if message:
            await self.loop.run_in_executor(None, pb_pose.ParseFromString, message)

        pose = MessageToDict(
            pb_pose,
            including_default_value_fields=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True,
        )
        if self.sio_events.connected:
            self.shared_pose_current_lock.start_writing()
            self.shared_pose_current_buffer.push(pose["x"], pose["y"], pose["O"])
            self.shared_pose_current_lock.finish_writing()

    @pb_exception_handler
    async def handle_message_state(self, message: bytes | None = None) -> None:
        """
        Send robot state received from the robot to connected monitors.
        """
        pb_state = PB_State()

        if message:
            await self.loop.run_in_executor(None, pb_state.ParseFromString, message)

        state = MessageToDict(
            pb_state,
            including_default_value_fields=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True,
        )
        if self.sio_events.connected:
            await self.sio_events.emit("state", state)

    @pb_exception_handler
    async def handle_actuator_state(self, message: bytes | None = None) -> None:
        """
        Send actuator state received from the robot.
        """
        pb_actuator_state = PB_ActuatorState()

        if message:
            await self.loop.run_in_executor(None, pb_actuator_state.ParseFromString, message)

        kind = pb_actuator_state.WhichOneof("type")
        actuator_state = MessageToDict(
            getattr(pb_actuator_state, kind),
            including_default_value_fields=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True,
        )
        actuator_state["kind"] = ActuatorsKindEnum[kind]
        if self.sio_events.connected:
            await self.sio_events.emit("actuator_state", actuator_state)

    @pb_exception_handler
    async def handle_pid(self, message: bytes | None = None) -> None:
        """
        Send pids state received from the robot to connected dashboards.
        """
        pb_pid = PB_Pid()
        if message:
            await self.loop.run_in_executor(None, pb_pid.ParseFromString, message)

        self.pb_pids[pb_pid.id] = pb_pid
        pid = Pid(
            id=pb_pid.id,
            kp=pb_pid.kp,
            ki=pb_pid.ki,
            kd=pb_pid.kd,
            integral_term_limit=pb_pid.integral_term_limit,
        )

        # Get JSON Schema
        pid_schema = pid.model_json_schema()
        # Add namespace in JSON Schema
        pid_schema["namespace"] = "/copilot"
        pid_schema["sio_event"] = "config_updated"
        # Add current values in JSON Schema
        pid_schema["title"] = pid.id.name
        for prop, value in pid.model_dump().items():
            if prop == "id":
                continue
            pid_schema["properties"][prop]["value"] = value
            pid_schema["properties"][f"{pid.id}-{prop}"] = pid_schema["properties"][prop]
            del pid_schema["properties"][prop]
        # Send config
        await self.sio_events.emit("config", pid_schema)

    async def handle_pose_reached(self) -> None:
        """
        Handle pose reached message.

        Forward info to the planner.
        """
        logger.info("[CAN] Received pose reached")
        if self.sio_events.connected:
            await self.sio_events.emit("pose_reached")

    async def handle_blocked(self) -> None:
        """
        Handle blocked message.

        Forward info to the planner.
        """
        logger.info("[CAN] Received blocked")
        if self.sio_events.connected:
            await self.sio_events.emit("blocked")
