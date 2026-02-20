import asyncio
import time
import traceback

import socketio
from google.protobuf.json_format import MessageToDict

from cogip import models
from cogip.cpp.libraries.models import MotionDirection
from cogip.cpp.libraries.models import PoseBuffer as SharedPoseBuffer
from cogip.cpp.libraries.models import PoseOrderList as SharedPoseOrderList
from cogip.cpp.libraries.shared_memory import LockName, SharedMemory, WritePriorityLock
from cogip.models.actuators import ActuatorsKindEnum
from cogip.protobuf import (
    PB_ActuatorState,
    PB_EmergencyStopStatus,
    PB_ParameterGetResponse,
    PB_ParameterSetResponse,
    PB_PathPose,
    # PB_Pid,
    # PB_PidEnum,
    PB_Pose,
    PB_PowerRailsStatus,
    PB_PowerSourceStatus,
    PB_State,
    PB_TelemetryData,
)
from . import logger
from .pbcom import PBCom, pb_exception_handler

# from .pid import Pid
from .sio_events import SioEvents

# Motion Control: 0x1000 - 0x1FFF
state_uuid: int = 0x1001
pose_order_uuid: int = 0x1002
pose_reached_uuid: int = 0x1003
pose_start_uuid: int = 0x1004
pid_request_uuid: int = 0x1005
# pid_uuid: int = 0x1006
brake_uuid: int = 0x1007
controller_uuid: int = 0x1008
blocked_uuid: int = 0x1009
intermediate_pose_reached_uuid: int = 0x100A
# Actuators: 0x2000 - 0x2FFF
actuators_thread_start_uuid: int = 0x2001
actuators_thread_stop_uuid: int = 0x2002
actuator_state_uuid: int = 0x2003
actuator_command_uuid: int = 0x2004
actuator_init_uuid: int = 0x2005
# Service: 0x3000 - 0x3FFF
reset_uuid: int = 0x3001
copilot_connected_uuid: int = 0x3002
copilot_disconnected_uuid: int = 0x3003
parameter_set_uuid: int = 0x3004
parameter_set_response_uuid: int = 0x3005
parameter_get_uuid: int = 0x3006
parameter_get_response_uuid: int = 0x3007
telemetry_enable_uuid: int = 0x3008
telemetry_disable_uuid: int = 0x3009
telemetry_data_uuid: int = 0x300A
# Game: 0x4000 - 0x4FFF
game_start_uuid: int = 0x4001
game_end_uuid: int = 0x4002
game_reset_uuid: int = 0x4003
# Power Supply: 0x5000 - 0x5FFF
emergency_stop_status_uuid: int = 0x5001
power_source_status_uuid: int = 0x5002
power_rails_status_uuid: int = 0x5003
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
        # self.pb_pids: dict[PB_PidEnum, PB_Pid] = {}

        self.shared_memory: SharedMemory | None = None
        self.shared_pose_current_buffer: SharedPoseBuffer | None = None
        self.shared_pose_current_lock: WritePriorityLock | None = None
        self.shared_avoidance_path: SharedPoseOrderList | None = None
        self.shared_avoidance_path_lock: WritePriorityLock | None = None
        self.new_path_event_task: asyncio.Task | None = None

        self.sio = socketio.AsyncClient(logger=False)
        self.sio_events = SioEvents(self)
        self.sio.register_namespace(self.sio_events)

        pb_message_handlers = {
            reset_uuid: self.handle_reset,
            pose_order_uuid: self.handle_message_pose,
            state_uuid: self.handle_message_state,
            pose_reached_uuid: self.handle_pose_reached,
            intermediate_pose_reached_uuid: self.handle_intermediate_pose_reached,
            actuator_state_uuid: self.handle_actuator_state,
            # pid_uuid: self.handle_pid,
            blocked_uuid: self.handle_blocked,
            parameter_get_response_uuid: self.handle_parameter_get_response,
            parameter_set_response_uuid: self.handle_parameter_set_response,
            telemetry_data_uuid: self.handle_telemetry_data,
            emergency_stop_status_uuid: self.handle_emergency_stop_status,
            power_source_status_uuid: self.handle_power_source_status,
            power_rails_status_uuid: self.handle_power_rails_status,
        }

        self.pbcom = PBCom(can_channel, can_bitrate, canfd_data_bitrate, pb_message_handlers)

    def create_shared_memory(self):
        self.shared_memory = SharedMemory(f"cogip_{self.id}")
        self.shared_pose_current_buffer = self.shared_memory.get_pose_current_buffer()
        self.shared_pose_current_lock = self.shared_memory.get_lock(LockName.PoseCurrent)
        self.shared_avoidance_path = self.shared_memory.get_avoidance_path()
        self.shared_avoidance_path_lock = self.shared_memory.get_lock(LockName.AvoidancePath)
        self.shared_avoidance_path_lock.register_consumer()
        self.new_path_event_task = asyncio.create_task(
            self.new_path_event_loop(),
            name="Robot: Task New Path Event Watcher Loop",
        )

    async def delete_shared_memory(self):
        if self.new_path_event_task:
            self.new_path_event_task.cancel()
            try:
                await self.new_path_event_task
            except asyncio.CancelledError:
                logger.info("Copilot: Task New Path Event Watcher Loop stopped")
            except Exception as exc:
                logger.warning(f"Copilot: Unexpected exception {exc}")
                traceback.print_exc()
        self.new_path_event_task = None

        self.shared_avoidance_path_lock = None
        self.shared_avoidance_path = None
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
            always_print_fields_with_no_presence=True,
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
            always_print_fields_with_no_presence=True,
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
            always_print_fields_with_no_presence=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True,
        )
        actuator_state["kind"] = ActuatorsKindEnum[kind]
        if self.sio_events.connected:
            await self.sio_events.emit("actuator_state", actuator_state)

    # @pb_exception_handler
    # async def handle_pid(self, message: bytes | None = None) -> None:
    #     """
    #     Send pids state received from the robot to connected dashboards.
    #     """
    #     pb_pid = PB_Pid()
    #     if message:
    #         await self.loop.run_in_executor(None, pb_pid.ParseFromString, message)

    #     self.pb_pids[pb_pid.id] = pb_pid
    #     pid = Pid(
    #         id=pb_pid.id,
    #         kp=pb_pid.kp,
    #         ki=pb_pid.ki,
    #         kd=pb_pid.kd,
    #         integral_term_limit=pb_pid.integral_term_limit,
    #     )

    #     # Get JSON Schema
    #     pid_schema = pid.model_json_schema()
    #     # Add namespace in JSON Schema
    #     pid_schema["namespace"] = "/copilot"
    #     pid_schema["sio_event"] = "config_updated"
    #     # Add current values in JSON Schema
    #     pid_schema["title"] = pid.id.name
    #     for prop, value in pid.model_dump().items():
    #         if prop == "id":
    #             continue
    #         pid_schema["properties"][prop]["value"] = value
    #         pid_schema["properties"][f"{pid.id}-{prop}"] = pid_schema["properties"][prop]
    #         del pid_schema["properties"][prop]
    #     # Send config
    #     await self.sio_events.emit("config", pid_schema)

    async def handle_pose_reached(self) -> None:
        """
        Handle pose reached message.

        Forward info to the planner.
        """
        logger.info("[CAN] Received pose reached")
        if self.sio_events.connected:
            await self.sio_events.emit("pose_reached")

    async def handle_intermediate_pose_reached(self) -> None:
        """
        Handle intermediate pose reached message.

        Forward info to the planner.
        """
        logger.info("[CAN] Received intermediate pose reached")
        if self.sio_events.connected:
            await self.sio_events.emit("intermediate_pose_reached")

    async def handle_blocked(self) -> None:
        """
        Handle blocked message.

        Forward info to the planner.
        """
        logger.info("[CAN] Received blocked")
        if self.sio_events.connected:
            await self.sio_events.emit("blocked")

    @pb_exception_handler
    async def handle_parameter_get_response(self, message: bytes | None = None):
        """
        Handle parameter get response from firmware.

        Forward response to the firmware_parameter_manager.
        """
        pb_response = PB_ParameterGetResponse()

        if message:
            await self.loop.run_in_executor(None, pb_response.ParseFromString, message)

        response = MessageToDict(
            pb_response,
            always_print_fields_with_no_presence=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True,
        )
        logger.info(f"[CAN] get_response: {response}")

        if self.sio_events.connected:
            await self.sio_events.emit("get_parameter_response", response)

    @pb_exception_handler
    async def handle_parameter_set_response(self, message: bytes | None = None):
        """
        Handle parameter set response from firmware.

        Forward response to the firmware_parameter_manager.
        """
        pb_response = PB_ParameterSetResponse()

        if message:
            await self.loop.run_in_executor(None, pb_response.ParseFromString, message)

        response = MessageToDict(
            pb_response,
            always_print_fields_with_no_presence=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True,
        )
        logger.info(f"[CAN] set_response: {response}")

        if self.sio_events.connected:
            await self.sio_events.emit("set_parameter_response", response)

    @pb_exception_handler
    async def handle_telemetry_data(self, message: bytes | None = None):
        """
        Handle parameter telemetry data from firmware.

        Forward response to the TODO:
        """
        pb_telemetry = PB_TelemetryData()

        if message:
            await self.loop.run_in_executor(None, pb_telemetry.ParseFromString, message)

        telemetry = MessageToDict(
            pb_telemetry,
            always_print_fields_with_no_presence=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True,
        )
        logger.debug(f"[CAN] telemetry data: {telemetry}")

        if self.sio_events.connected:
            await self.sio_events.emit("telemetry_data", telemetry)

    @pb_exception_handler
    async def handle_emergency_stop_status(self, message: bytes | None = None):
        """
        Handle emergency stop status from power supply board.

        Forward status to connected clients.
        """
        pb_status = PB_EmergencyStopStatus()

        if message:
            await self.loop.run_in_executor(None, pb_status.ParseFromString, message)

        status = MessageToDict(
            pb_status,
            always_print_fields_with_no_presence=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True,
        )
        logger.debug(f"[CAN] emergency stop status: {status}")

        if self.sio_events.connected:
            await self.sio_events.emit("emergency_stop_status", status)

    @pb_exception_handler
    async def handle_power_source_status(self, message: bytes | None = None):
        """
        Handle power source status from power supply board.

        Forward status to connected clients.
        """
        pb_status = PB_PowerSourceStatus()

        if message:
            await self.loop.run_in_executor(None, pb_status.ParseFromString, message)

        status = MessageToDict(
            pb_status,
            always_print_fields_with_no_presence=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True,
        )
        logger.debug(f"[CAN] power source status: {status}")

        if self.sio_events.connected:
            await self.sio_events.emit("power_source_status", status)

    @pb_exception_handler
    async def handle_power_rails_status(self, message: bytes | None = None):
        """
        Handle power rails status from power supply board.

        Forward status to connected clients.
        """
        pb_status = PB_PowerRailsStatus()

        if message:
            await self.loop.run_in_executor(None, pb_status.ParseFromString, message)

        status = MessageToDict(
            pb_status,
            always_print_fields_with_no_presence=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True,
        )
        logger.debug(f"[CAN] power rails status: {status}")

        if self.sio_events.connected:
            await self.sio_events.emit("power_rails_status", status)

    async def new_path_event_loop(self):
        """
        Async worker watching for new path orders in shared memory.
        When a new path is available, its first pose is sent to the firmware.
        """
        logger.info("Copilot: Task New Path Event Watcher Loop started")
        try:
            while True:
                await asyncio.to_thread(self.shared_avoidance_path_lock.wait_update)
                if len(self.shared_avoidance_path) == 0:
                    continue
                pose_order = models.PathPose.from_shared(self.shared_avoidance_path[0])
                if self.id > 1:
                    pose_order.motion_direction = MotionDirection.FORWARD_ONLY
                pb_pose_order = PB_PathPose()
                pose_order.copy_pb(pb_pose_order)
                await self.pbcom.send_can_message(pose_order_uuid, pb_pose_order)

        except asyncio.CancelledError:
            logger.info("Copilot: Task New Path Event Watcher Loop cancelled")
            raise
        except Exception as exc:  # noqa
            logger.warning(f"Copilot: Task New Path Event Watcher Loop: Unknown exception {exc}")
            traceback.print_exc()
            raise
