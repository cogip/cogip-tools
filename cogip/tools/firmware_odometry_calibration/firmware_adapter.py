"""
Firmware Adapter for Odometry Calibration

Unified facade for all firmware interactions via SocketIO:
- Parameter load/save operations
- Encoder telemetry
- Motion control via pose_order/pose_reached
- Calibration-specific movement sequences
"""

from __future__ import annotations
import asyncio
import math

import socketio
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from cogip.models import OdometryParameters
from cogip.models.models import Pose
from cogip.tools.firmware_parameter_manager.firmware_parameter_manager import FirmwareParameterManager
from cogip.tools.firmware_telemetry.firmware_telemetry_manager import FirmwareTelemetryManager
from cogip.utils.console_ui import ConsoleUI
from . import logger
from .types import SQUARE_PATH_CCW


class FirmwareAdapter:
    """Unified adapter for firmware operations via SocketIO.

    Handles odometry parameter load/save, encoder telemetry, motion control
    via pose_order/pose_reached events, and calibration movement sequences.
    """

    # Parameter name constants
    PARAM_WHEELS_DISTANCE = "encoder_wheels_distance_mm"
    PARAM_RIGHT_WHEEL_DIAMETER = "right_wheel_diameter_mm"
    PARAM_LEFT_WHEEL_DIAMETER = "left_wheel_diameter_mm"
    PARAM_LEFT_POLARITY = "qdec_left_polarity"
    PARAM_RIGHT_POLARITY = "qdec_right_polarity"
    PARAM_ENCODER_RESOLUTION = "encoder_wheels_resolution_pulses"

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

    async def load_parameters(self) -> OdometryParameters:
        """
        Load current odometry parameters from firmware.

        Returns:
            OdometryParameters populated with values from firmware

        Raises:
            TimeoutError: If firmware communication times out
        """
        logger.info("Loading parameters from firmware...")
        (
            wheels_distance,
            right_diameter,
            left_diameter,
            left_polarity,
            right_polarity,
            encoder_ticks,
        ) = await asyncio.gather(
            self._param_manager.get_parameter_value(self.PARAM_WHEELS_DISTANCE),
            self._param_manager.get_parameter_value(self.PARAM_RIGHT_WHEEL_DIAMETER),
            self._param_manager.get_parameter_value(self.PARAM_LEFT_WHEEL_DIAMETER),
            self._param_manager.get_parameter_value(self.PARAM_LEFT_POLARITY),
            self._param_manager.get_parameter_value(self.PARAM_RIGHT_POLARITY),
            self._param_manager.get_parameter_value(self.PARAM_ENCODER_RESOLUTION),
        )

        params = OdometryParameters(
            wheels_distance=wheels_distance,
            right_wheel_radius=right_diameter / 2.0,
            left_wheel_radius=left_diameter / 2.0,
            left_polarity=left_polarity,
            right_polarity=right_polarity,
            encoder_ticks=encoder_ticks,
        )

        logger.info(f"Loaded parameters: {params}")

        return params

    async def save_parameters(self, params: OdometryParameters) -> None:
        """
        Save odometry parameters to firmware.

        Only saves the calibrated values (wheels_distance, wheel radii).
        Polarity and encoder ticks are not modified.

        Args:
            params: OdometryParameters with values to save

        Raises:
            TimeoutError: If firmware communication times out
        """
        logger.info(f"Saving parameters to firmware: {params}")

        await asyncio.gather(
            self._param_manager.set_parameter_value(self.PARAM_WHEELS_DISTANCE, params.wheels_distance),
            self._param_manager.set_parameter_value(self.PARAM_RIGHT_WHEEL_DIAMETER, params.right_wheel_radius * 2.0),
            self._param_manager.set_parameter_value(self.PARAM_LEFT_WHEEL_DIAMETER, params.left_wheel_radius * 2.0),
        )

        logger.info("Parameters saved successfully")

    # === Telemetry ===

    async def get_encoder_ticks(self) -> tuple[int, int]:
        """
        Get current encoder tick counts from firmware telemetry.

        Waits briefly for telemetry to stabilize before reading values.

        Returns:
            Tuple of (left_ticks, right_ticks)
        """
        await asyncio.sleep(0.1)

        left = self._telemetry.get_value(self.TELEMETRY_LEFT_ENCODER)
        right = self._telemetry.get_value(self.TELEMETRY_RIGHT_ENCODER)

        return int(left), int(right)

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

    async def goto(self, x: float, y: float, orientation: float, timeout: float = 60.0) -> bool:
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

    # === Calibration Movement Sequences ===

    async def execute_rotations(self, num_rotations: int) -> bool:
        """
        Execute N full rotations in place (Phase 1: WHEEL_DISTANCE).

        Args:
            num_rotations: Number of full 360-degree rotations

        Returns:
            True if successful, False otherwise.
        """
        target_orientation = num_rotations * 360.0
        logger.info(f"Executing {num_rotations} rotations ({target_orientation}°)...")

        # Reset position to origin
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
                logger.debug(f"Rotation {rotation_num + 1}/{num_rotations}")
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

    async def execute_squares(self, num_squares: int) -> bool:
        """
        Execute N square paths clockwise (Phase 2: RIGHT_WHEEL_RADIUS).

        Uses the predefined 500mm square path from __init__.py.

        Args:
            num_squares: Number of complete squares to execute

        Returns:
            True if successful, False otherwise.
        """
        logger.info(f"Executing {num_squares} squares...")

        # Reset position to origin
        await self.set_start_position(0, 0, 0)
        await asyncio.sleep(0.2)

        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Square {task.fields[square]}/{task.fields[total_count]}[/]"),
            TimeElapsedColumn(),
            console=self._console,
        ) as progress:
            task = progress.add_task("", square=1, total_count=num_squares)

            for square_num in range(num_squares):
                progress.update(task, square=square_num + 1)
                for waypoint_idx, waypoint in enumerate(SQUARE_PATH_CCW):
                    orientation_degrees = math.degrees(waypoint.O)
                    logger.debug(
                        f"Square {square_num + 1}/{num_squares}, waypoint {waypoint_idx + 1}/4: "
                        f"({waypoint.x}, {waypoint.y}, {orientation_degrees}°)"
                    )

                    success = await self.goto(waypoint.x, waypoint.y, orientation_degrees, timeout=30.0)
                    if not success:
                        self._console.show_error(
                            f"Square path failed at waypoint {waypoint_idx + 1}/4 of square {square_num + 1}"
                        )
                        return False

            progress.update(task, square=num_squares)

        logger.info("Squares completed")
        return True

    async def execute_straight_line(self, distance_mm: int) -> bool:
        """
        Execute a straight line movement (Phase 3: LEFT_WHEEL_RADIUS).

        Moves forward from origin by the specified distance.

        Args:
            distance_mm: Distance to travel in mm

        Returns:
            True if successful, False otherwise.
        """
        logger.info(f"Executing straight line movement ({distance_mm}mm)...")

        # Reset position to origin facing forward (0°)
        await self.set_start_position(0, 0, 0)
        await asyncio.sleep(0.2)

        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Straight line ({task.fields[distance]} mm)[/]"),
            TimeElapsedColumn(),
            console=self._console,
        ) as progress:
            progress.add_task("", distance=distance_mm)

            success = await self.goto(distance_mm, 0, 0, timeout=30.0)
            if not success:
                self._console.show_error("Straight line movement failed (timeout)")
                return False

        logger.info("Straight line completed")
        return True
