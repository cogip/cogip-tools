"""
Firmware Adapter for PID Calibration

Unified facade for all firmware interactions via SocketIO:
- Parameter load/save operations
- Encoder telemetry
- Motion control via pose_order/pose_reached
- Calibration-specific movement sequences
"""

from __future__ import annotations
import asyncio

import socketio

from cogip.models.models import Pose
from cogip.tools.copilot.controller import ControllerEnum
from cogip.tools.firmware_parameter_manager.firmware_parameter_manager import FirmwareParameterManager
from cogip.tools.firmware_telemetry.firmware_telemetry_manager import FirmwareTelemetryManager
from cogip.utils.console_ui import ConsoleUI
from . import logger
from .types import PidGains, PidType


class FirmwareAdapter:
    """Unified adapter for firmware operations via SocketIO.

    Handles PID parameter load/save, encoder telemetry, motion control
    via pose_order/pose_reached events, and calibration movement sequences.
    """

    # PID parameter names mapping: PidType -> (kp_name, ki_name, kd_name)
    PID_PARAM_NAMES: dict[PidType, tuple[str, str, str]] = {
        PidType.LINEAR_POSE: ("linear_pose_pid_kp", "linear_pose_pid_ki", "linear_pose_pid_kd"),
        PidType.ANGULAR_POSE: ("angular_pose_pid_kp", "angular_pose_pid_ki", "angular_pose_pid_kd"),
        PidType.LINEAR_SPEED: ("linear_speed_pid_kp", "linear_speed_pid_ki", "linear_speed_pid_kd"),
        PidType.ANGULAR_SPEED: ("angular_speed_pid_kp", "angular_speed_pid_ki", "angular_speed_pid_kd"),
    }

    # Telemetry keys for encoder values
    TELEMETRY_LEFT_ENCODER = "encoder_left"
    TELEMETRY_RIGHT_ENCODER = "encoder_right"

    def __init__(
        self,
        sio: socketio.AsyncClient,
        param_manager: FirmwareParameterManager,
        telemetry_manager: FirmwareTelemetryManager,
        pose_reached_event: asyncio.Event,
        console: ConsoleUI | None = None,
    ):
        """
        Initialize the firmware adapter.

        Args:
            sio: SocketIO client for communication
            param_manager: Firmware parameter manager for read/write operations
            telemetry_manager: Firmware telemetry manager for encoder tick counts
            pose_reached_event: Event signaled when robot reaches target position
            console: Optional ConsoleUI for progress display
        """
        self.sio = sio
        self._param_manager = param_manager
        self._telemetry = telemetry_manager
        self.pose_reached_event = pose_reached_event
        self._console = console or ConsoleUI()

    # === Parameters ===

    async def load_pid_gains(self, pid_type: PidType) -> PidGains:
        """
        Load PID gains for a specific controller type.

        Args:
            pid_type: Type of PID controller to load

        Returns:
            PidGains with values from firmware

        Raises:
            TimeoutError: If firmware communication times out
        """
        kp_name, ki_name, kd_name = self.PID_PARAM_NAMES[pid_type]
        logger.info(f"Loading {pid_type.name} PID gains from firmware...")

        kp, ki, kd = await asyncio.gather(
            self._param_manager.get_parameter_value(kp_name, timeout=5),
            self._param_manager.get_parameter_value(ki_name, timeout=5),
            self._param_manager.get_parameter_value(kd_name, timeout=5),
        )

        gains = PidGains(kp=kp, ki=ki, kd=kd)
        logger.info(f"Loaded {pid_type.name}: {gains}")

        return gains

    async def save_pid_gains(self, pid_type: PidType, gains: PidGains) -> None:
        """
        Save PID gains for a specific controller type.

        Args:
            pid_type: Type of PID controller to save
            gains: PidGains with values to save

        Raises:
            TimeoutError: If firmware communication times out
        """
        kp_name, ki_name, kd_name = self.PID_PARAM_NAMES[pid_type]
        logger.info(f"Saving {pid_type.name} PID gains: {gains}")

        await asyncio.gather(
            self._param_manager.set_parameter_value(kp_name, gains.kp, timeout=5),
            self._param_manager.set_parameter_value(ki_name, gains.ki, timeout=5),
            self._param_manager.set_parameter_value(kd_name, gains.kd, timeout=5),
        )

        logger.info(f"{pid_type.name} PID gains saved successfully")

    # === Telemetry ===
    # TODO:

    # === Motion Control ===

    async def set_start_position(self, x: float, y: float, orientation: float) -> None:
        """
        Set the robot's starting reference position.

        Args:
            x: X coordinate in mm
            y: Y coordinate in mm
            orientation: Orientation in degrees
        """
        pose = Pose(x=x, y=y, O=orientation)

        logger.debug(f"Setting start position: {pose}")

        await self.sio.emit("pose_start", pose.model_dump(), namespace="/calibration")

    async def _send_pose_order(self, x: float, y: float, orientation: float) -> None:
        """
        Send a pose order to the robot.

        Args:
            x: Target X coordinate in mm
            y: Target Y coordinate in mm
            orientation: Target orientation in degrees
        """
        pose = Pose(x=x, y=y, O=orientation)
        self.pose_reached_event.clear()

        logger.debug(f"Sending pose order: {pose}")

        await self.sio.emit("pose_order", pose.model_dump(), namespace="/calibration")

    async def _wait_pose_reached(self, timeout: float = 60.0) -> bool:
        """
        Wait for the robot to reach its target position.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if pose was reached, False if timeout
        """
        try:
            await asyncio.wait_for(self.pose_reached_event.wait(), timeout=timeout)
            return True
        except TimeoutError:
            logger.warning(f"Timeout waiting for pose reached (>{timeout}s)")
            return False

    async def goto(self, x: float, y: float, orientation: float, timeout: float = 5.0) -> bool:
        """
        Move robot to target position and wait for completion.

        Args:
            x: Target X coordinate in mm
            y: Target Y coordinate in mm
            orientation: Target orientation in degrees
            timeout: Maximum time to wait in seconds

        Returns:
            True if movement completed, False if timeout
        """
        await self._send_pose_order(x, y, orientation)
        return await self._wait_pose_reached(timeout)

    # === Controller ===

    async def set_controller(self, controller: ControllerEnum, timeout: float = 5.0) -> bool:
        """
        Set the robot controller and wait for acknowledgment.

        Args:
            controller: Controller type to set
            timeout: Maximum time to wait for acknowledgment in seconds

        Returns:
            True if controller was set, False if timeout
        """
        logger.debug(f"Setting controller: {controller.name}")

        await self.sio.emit("set_controller", controller.value, namespace="/calibration")
