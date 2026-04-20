"""
Firmware Adapter for OTOS Calibration

Thin facade over the shared FirmwareParameterManager and the motion control
pose_order / pose_reached SocketIO pattern. Mirrors firmware_odometry_calibration's
adapter but deals with OTOS scalars and skips the encoder telemetry (OTOS
does not expose useful ticks; the ground truth is the operator's physical
measurement).
"""

from __future__ import annotations
import asyncio

import socketio
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from cogip.models import OTOSParameters
from cogip.models.models import Pose
from cogip.tools.firmware_parameter_manager.firmware_parameter_manager import FirmwareParameterManager
from cogip.utils.console_ui import ConsoleUI
from . import logger


class FirmwareAdapter:
    """Wraps parameter read/write and motion execution for OTOS calibration."""

    PARAM_LINEAR_SCALAR = "otos_linear_scalar"
    PARAM_ANGULAR_SCALAR = "otos_angular_scalar"

    def __init__(
        self,
        sio: socketio.AsyncClient,
        param_manager: FirmwareParameterManager,
        pose_reached_event: asyncio.Event,
        console: ConsoleUI | None = None,
    ) -> None:
        self.sio = sio
        self._param_manager = param_manager
        self.pose_reached_event = pose_reached_event
        self._console = console or ConsoleUI()

    # === Parameters ===

    async def load_parameters(self) -> OTOSParameters:
        """Read the current OTOS scalars from firmware."""
        logger.info("Loading OTOS parameters from firmware...")
        linear, angular = await asyncio.gather(
            self._param_manager.get_parameter_value(self.PARAM_LINEAR_SCALAR),
            self._param_manager.get_parameter_value(self.PARAM_ANGULAR_SCALAR),
        )
        params = OTOSParameters(linear_scalar=linear, angular_scalar=angular)
        logger.info(f"Loaded OTOS parameters: {params}")
        return params

    async def save_parameters(self, params: OTOSParameters) -> None:
        """Write both OTOS scalars back to the firmware."""
        logger.info(f"Saving OTOS parameters to firmware: {params}")
        await asyncio.gather(
            self._param_manager.set_parameter_value(self.PARAM_LINEAR_SCALAR, params.linear_scalar),
            self._param_manager.set_parameter_value(self.PARAM_ANGULAR_SCALAR, params.angular_scalar),
        )
        logger.info("OTOS parameters saved successfully")

    async def save_linear_scalar(self, scalar: float) -> None:
        await self._param_manager.set_parameter_value(self.PARAM_LINEAR_SCALAR, scalar)

    async def save_angular_scalar(self, scalar: float) -> None:
        await self._param_manager.set_parameter_value(self.PARAM_ANGULAR_SCALAR, scalar)

    # === Motion Control ===

    async def set_start_position(self, x: float, y: float, orientation: float) -> None:
        """Reset the OTOS-reported pose to the given reference."""
        pose = Pose(x=x, y=y, O=orientation)
        logger.debug(f"Setting start position: {pose}")
        await self.sio.emit("pose_start", pose.model_dump(), namespace="/calibration")

    async def _send_pose_order(self, x: float, y: float, orientation: float) -> None:
        pose = Pose(x=x, y=y, O=orientation)
        self.pose_reached_event.clear()
        logger.debug(f"Sending pose order: {pose}")
        await self.sio.emit("pose_order", pose.model_dump(), namespace="/calibration")

    async def _wait_pose_reached(self, timeout: float = 120.0) -> bool:
        try:
            await asyncio.wait_for(self.pose_reached_event.wait(), timeout=timeout)
            return True
        except TimeoutError:
            logger.warning(f"Timeout waiting for pose reached (>{timeout}s)")
            return False

    async def goto(self, x: float, y: float, orientation: float, timeout: float = 120.0) -> bool:
        await self._send_pose_order(x, y, orientation)
        return await self._wait_pose_reached(timeout)

    # === Calibration Movement Sequences ===

    async def execute_straight_line(self, distance_mm: int) -> bool:
        """Drive straight forward by distance_mm (linear scalar phase)."""
        logger.info(f"Executing straight line movement ({distance_mm} mm)...")

        await self.set_start_position(0, 0, 0)
        await asyncio.sleep(0.2)

        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Straight line ({task.fields[distance]} mm)[/]"),
            TimeElapsedColumn(),
            console=self._console,
        ) as progress:
            progress.add_task("", distance=distance_mm)

            success = await self.goto(distance_mm, 0, 0, timeout=10.0)
            if not success:
                self._console.show_error("Straight line movement failed (timeout)")
                return False

        logger.info("Straight line completed")
        return True

    async def execute_rotations(self, num_rotations: int) -> bool:
        """Rotate in place by num_rotations * 360° (angular scalar phase).

        Each full turn is split into four quarter-turn pose orders so the
        motion controller takes the short angular path instead of flipping
        through the ±180° wrap.
        """
        target_orientation = num_rotations * 360.0
        logger.info(f"Executing {num_rotations} rotations ({target_orientation}°)...")

        await self.set_start_position(0, 0, 0)
        await asyncio.sleep(0.2)

        quarter_turns = [90, 180, -90, 0]

        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Rotation {task.fields[rotation]}/{task.fields[total_count]}[/]"),
            TimeElapsedColumn(),
            console=self._console,
        ) as progress:
            task = progress.add_task("", rotation=1, total_count=num_rotations)

            for rotation_num in range(num_rotations):
                progress.update(task, rotation=rotation_num + 1)
                for target_angle in quarter_turns:
                    success = await self.goto(0, 0, target_angle, timeout=30.0)
                    if not success:
                        self._console.show_error(
                            f"Rotation {rotation_num + 1}/{num_rotations} failed at {target_angle}° (timeout)"
                        )
                        return False

            progress.update(task, rotation=num_rotations)

        logger.info("Rotations completed")
        return True
