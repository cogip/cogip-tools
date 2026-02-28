"""
Firmware Adapter for PID Calibration

Unified facade for all firmware interactions via SocketIO:
- PID parameter load/save operations
- Motion control via pose_order/pose_reached
"""

from __future__ import annotations
import asyncio

import socketio

from cogip.models.models import Pose, SpeedOrder
from cogip.tools.copilot.controller import ControllerEnum
from cogip.tools.firmware_parameter_manager.firmware_parameter_manager import FirmwareParameterManager
from cogip.utils.console_ui import ConsoleUI
from . import logger
from .types import PidGains, PidType


class FirmwareAdapter:
    """Unified adapter for firmware operations via SocketIO.

    Handles PID parameter load/save and motion control via pose_order/pose_reached
    events.
    """

    PARAM_TIMEOUT: float = 5.0

    def __init__(
        self,
        sio: socketio.AsyncClient,
        param_manager: FirmwareParameterManager,
        pose_reached_event: asyncio.Event,
        console: ConsoleUI | None = None,
    ):
        """
        Initialize the firmware adapter.

        Args:
            sio: SocketIO client for communication
            param_manager: Firmware parameter manager for read/write operations
            pose_reached_event: Event signaled when robot reaches target position
            console: Optional ConsoleUI for progress display
        """
        self.sio = sio
        self._param_manager = param_manager
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
        kp_name, ki_name, kd_name = pid_type.param_names
        logger.info(f"Loading {pid_type.name} PID gains from firmware...")

        kp, ki, kd = await asyncio.gather(
            self._param_manager.get_parameter_value(kp_name, timeout=self.PARAM_TIMEOUT),
            self._param_manager.get_parameter_value(ki_name, timeout=self.PARAM_TIMEOUT),
            self._param_manager.get_parameter_value(kd_name, timeout=self.PARAM_TIMEOUT),
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
        kp_name, ki_name, kd_name = pid_type.param_names
        logger.info(f"Saving {pid_type.name} PID gains: {gains}")

        await asyncio.gather(
            self._param_manager.set_parameter_value(kp_name, gains.kp, timeout=self.PARAM_TIMEOUT),
            self._param_manager.set_parameter_value(ki_name, gains.ki, timeout=self.PARAM_TIMEOUT),
            self._param_manager.set_parameter_value(kd_name, gains.kd, timeout=self.PARAM_TIMEOUT),
        )

        logger.info(f"{pid_type.name} PID gains saved successfully")

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
            True if motion completed, False if timeout
        """
        await self._send_pose_order(x, y, orientation)
        return await self._wait_pose_reached(timeout)

    async def send_speed_order(self, linear_speed_mm_s: int, angular_speed_deg_s: int, duration_ms: int) -> None:
        """
        Send a speed order to the robot.

        Args:
            linear_speed_mm_s: Linear speed in mm/s (positive = forward, negative = backward)
            angular_speed_deg_s: Angular speed in deg/s (positive = counter-clockwise)
            duration_ms: Duration of the speed command in milliseconds
        """
        speed_order = SpeedOrder(
            linear_speed_mm_s=linear_speed_mm_s,
            angular_speed_deg_s=angular_speed_deg_s,
            duration_ms=duration_ms,
        )

        logger.debug(f"Sending speed order: {speed_order}")

        await self.sio.emit("speed_order", speed_order.model_dump(), namespace="/calibration")

    # === Controller ===

    async def set_controller(self, controller: ControllerEnum) -> None:
        """
        Set the robot controller.

        Args:
            controller: Controller type to set
        """
        logger.debug(f"Setting controller: {controller.name}")

        await self.sio.emit("set_controller", controller.value, namespace="/calibration")
