"""
Odometry Calibration Tool for differential drive robots.

Calibrates three parameters: wheel distance, left/right wheel radius.

Phases:
    1. Wheel Distance - Turn in place N rotations
    2. Right Wheel Radius - Execute square trajectories to find radius ratio
    3. Left Wheel Radius - Travel straight line to compute absolute radius

Usage:
    - Start with approximate parameter values in firmware
    - Execute phases in order (each depends on previous results)
    - Manually reposition robot to theoretical position after each motion
"""

from __future__ import annotations
import asyncio
import sys
from collections.abc import Awaitable, Callable

import socketio

from cogip.models import (
    CalibrationResult,
    CalibrationState,
    EncoderDeltas,
    FirmwareParametersGroup,
    OdometryParameters,
)
from cogip.tools.firmware_parameter_manager.firmware_parameter_manager import FirmwareParameterManager
from cogip.tools.firmware_telemetry.firmware_telemetry_manager import FirmwareTelemetryManager
from cogip.utils.console_ui import ConsoleUI
from . import logger
from .calculator import (
    compute_left_wheel_radius_result,
    compute_right_wheel_radius_result,
    compute_wheel_distance_result,
)
from .firmware_adapter import FirmwareAdapter
from .sio_events import SioEvents
from .types import CalibrationPhaseType


class OdometryCalibration:
    """
    Odometry Calibration controller.

    Orchestrates the calibration process by coordinating:
    - SocketIO connection to cogip-server
    - FirmwareAdapter for all firmware operations
    - User interaction via ConsoleUI
    """

    def __init__(self, server_url: str, parameters_group: FirmwareParametersGroup):
        """
        Initialize the calibration controller.

        Args:
            server_url: URL of the cogip-server
            parameters_group: Firmware parameters configuration
        """
        self.server_url = server_url
        self.console = ConsoleUI()

        # Event to signal pose reached
        self.pose_reached_event = asyncio.Event()

        # SocketIO client and namespaces
        self.sio = socketio.AsyncClient(logger=False)
        self.sio_ns = SioEvents(self)
        self.sio.register_namespace(self.sio_ns)

        # Managers (they register their own namespaces)
        self.param_manager = FirmwareParameterManager(self.sio, parameters_group)
        self.telemetry_manager = FirmwareTelemetryManager(self.sio)

        # Firmware adapter for motion control
        self.firmware = FirmwareAdapter(
            self.sio, self.param_manager, self.telemetry_manager, self.pose_reached_event, self.console
        )

        # Calibration state
        self.params: OdometryParameters | None = None
        self.initial_params: OdometryParameters | None = None
        self.state = CalibrationState()

    async def _connect(self) -> None:
        """Connect to cogip-server."""
        self.console.show_info(f"Connecting to {self.server_url}...")
        await self.sio.connect(
            self.server_url,
            namespaces=[
                self.sio_ns.namespace,
                self.param_manager.namespace,
                self.telemetry_manager.namespace,
            ],
        )

        # Wait for all namespaces to be connected
        self.console.show_info("Waiting for connections...")
        while not (self.sio_ns.connected and self.param_manager.is_connected and self.telemetry_manager.is_connected):
            await asyncio.sleep(0.1)

        self.console.show_success("Connected to cogip-server")

        # Enable telemetry
        await self.telemetry_manager.enable()
        await asyncio.sleep(0.2)

    async def _disconnect(self) -> None:
        """Disconnect from server."""
        # Disable telemetry
        await self.telemetry_manager.disable()
        await asyncio.sleep(0.2)
        
        if self.sio and self.sio.connected:
            await self.sio.disconnect()

    def _display_intro(self) -> None:
        """Display introduction panel."""
        self.console.show_panel(
            "This tool calibrates the robot's odometry parameters through 3 phases:\n"
            "1. [header]Wheel Distance[/] - Robot will rotates in place\n"
            "2. [header]Right Wheel Radius[/] - Robot will performs square paths\n"
            "3. [header]Left Wheel Radius[/] - Robot will travels along a straight line",
            title="Odometry Calibration Tool",
        )

    def _display_parameters(self, params: OdometryParameters, title: str) -> None:
        """Display parameters in a table."""
        self.console.show_key_value_table(
            [
                ("Wheels Distance", f"{params.wheels_distance:.3f} mm"),
                ("Left Wheel Radius", f"{params.left_wheel_radius:.3f} mm"),
                ("Right Wheel Radius", f"{params.right_wheel_radius:.3f} mm"),
                ("Left Polarity", f"{params.left_polarity:.0f}"),
                ("Right Polarity", f"{params.right_polarity:.0f}"),
                ("Encoder Ticks", f"{params.encoder_ticks:.0f} ticks/rev"),
            ],
            title=title,
        )

    def _display_result(self, result: CalibrationResult, current: OdometryParameters) -> None:
        """Display calibration result comparison."""
        change_wd = result.wheels_distance - current.wheels_distance
        change_lr = result.left_wheel_radius - current.left_wheel_radius
        change_rr = result.right_wheel_radius - current.right_wheel_radius

        table = self.console.create_table(
            title="Calibration Result",
            columns=[
                ("Parameter", {"style": "label"}),
                ("Before", {"style": "muted", "justify": "right"}),
                ("After", {"style": "value", "justify": "right"}),
                ("Change", {"style": "warning", "justify": "right"}),
            ],
        )
        table.add_row(
            "Wheels Distance (mm)",
            f"{current.wheels_distance:.3f}",
            f"{result.wheels_distance:.3f}",
            f"{change_wd:+.3f}",
        )
        table.add_row(
            "Left Wheel Radius (mm)",
            f"{current.left_wheel_radius:.3f}",
            f"{result.left_wheel_radius:.3f}",
            f"{change_lr:+.3f}",
        )
        table.add_row(
            "Right Wheel Radius (mm)",
            f"{current.right_wheel_radius:.3f}",
            f"{result.right_wheel_radius:.3f}",
            f"{change_rr:+.3f}",
        )
        self.console.print(table)

    async def _apply_result(self, result: CalibrationResult) -> None:
        """Apply calibration result to current parameters and save to firmware."""
        self.params.wheels_distance = result.wheels_distance
        self.params.right_wheel_radius = result.right_wheel_radius
        self.params.left_wheel_radius = result.left_wheel_radius

        self.console.show_info("Saving parameters to firmware...")
        await self.firmware.save_parameters(self.params)
        self.console.show_success("Parameters saved to firmware")

    async def _execute_motion_sequence(
        self,
        motion_fn: Callable[[int], Awaitable[bool]],
        motion_arg: int,
    ) -> EncoderDeltas | None:
        """
        Execute motion and collect encoder tick deltas.

        Args:
            motion_fn: Async function to execute the motion (e.g., execute_rotations).
            motion_arg: Argument to pass to the motion function (e.g., number of rotations).

        Returns:
            EncoderDeltas or None if motion failed.
        """
        await self.console.wait_for_enter("Position the robot at the starting position")
        left_before, right_before = await self.firmware.get_encoder_ticks()
        logger.info(f"Encoder ticks before: L={left_before}, R={right_before}")

        if not await motion_fn(motion_arg):
            return None

        await self.console.wait_for_enter("Reposition the robot to its theoretical position")
        left_after, right_after = await self.firmware.get_encoder_ticks()
        logger.info(f"Encoder ticks after: L={left_after}, R={right_after}")

        deltas = EncoderDeltas(left=left_after - left_before, right=right_after - right_before)
        logger.info(f"Encoder deltas: L={deltas.left}, R={deltas.right}")

        return deltas

    async def _handle_phase_result(
        self,
        result_tuple: tuple[CalibrationResult, CalibrationState] | None,
        phase: CalibrationPhaseType,
    ) -> bool:
        """
        Handle calibration result: display, confirm, and apply.

        Args:
            result_tuple: The computation result or None if computation failed.
            phase: The calibration phase type for error messages.

        Returns:
            True if result was accepted and applied, False otherwise.
        """
        if result_tuple is None:
            self.console.show_error(phase.error_message)
            return False

        result, new_state = result_tuple
        self._display_result(result, self.params)

        accepted = await self.console.confirm("Accept this result?")
        self.console.show_info(f"Accepted: {accepted}")

        if accepted:
            await self._apply_result(result)
            self.state = new_state
            return True

        return False

    async def _run_phase_1(self) -> bool:
        """Phase 1: Wheel Distance Calibration (Turn in Place)."""
        phase = CalibrationPhaseType.WHEEL_DISTANCE

        self.console.show_rule(phase.title)
        self.console.show_info(phase.description)

        num_rotations = await self.console.get_integer(phase.input_prompt, default=phase.default_value)

        deltas = await self._execute_motion_sequence(self.firmware.execute_rotations, num_rotations)
        if deltas is None:
            return False

        result_tuple = compute_wheel_distance_result(
            turns=num_rotations,
            lticks_delta=deltas.left,
            rticks_delta=deltas.right,
            encoder_ticks=self.params.encoder_ticks,
            left_wheel_radius=self.params.left_wheel_radius,
            right_wheel_radius=self.params.right_wheel_radius,
            left_polarity=self.params.left_polarity,
            right_polarity=self.params.right_polarity,
        )

        return await self._handle_phase_result(result_tuple, phase)

    async def _run_phase_2(self) -> bool:
        """Phase 2: Right Wheel Radius Calibration (Square Trajectories)."""
        phase = CalibrationPhaseType.RIGHT_WHEEL_RADIUS

        self.console.show_rule(phase.title)
        self.console.show_info(phase.description)

        num_squares = await self.console.get_integer(phase.input_prompt, default=phase.default_value)

        deltas = await self._execute_motion_sequence(self.firmware.execute_squares, num_squares)
        if deltas is None:
            return False

        result_tuple = compute_right_wheel_radius_result(
            squares=num_squares,
            lticks_delta=deltas.left,
            rticks_delta=deltas.right,
            state=self.state,
            encoder_ticks=self.params.encoder_ticks,
            left_wheel_radius=self.params.left_wheel_radius,
            left_polarity=self.params.left_polarity,
            right_polarity=self.params.right_polarity,
        )

        return await self._handle_phase_result(result_tuple, phase)

    async def _run_phase_3(self) -> bool:
        """Phase 3: Left Wheel Radius Calibration (Straight Line)."""
        phase = CalibrationPhaseType.LEFT_WHEEL_RADIUS

        self.console.show_rule(phase.title)
        self.console.show_info(phase.description)

        distance_mm = await self.console.get_integer(phase.input_prompt, default=phase.default_value)

        deltas = await self._execute_motion_sequence(self.firmware.execute_straight_line, distance_mm)
        if deltas is None:
            return False

        result_tuple = compute_left_wheel_radius_result(
            distance_mm=distance_mm,
            lticks_delta=deltas.left,
            rticks_delta=deltas.right,
            state=self.state,
            encoder_ticks=self.params.encoder_ticks,
            left_polarity=self.params.left_polarity,
            right_polarity=self.params.right_polarity,
        )

        return await self._handle_phase_result(result_tuple, phase)

    async def _run_calibration(self) -> None:
        """Run the calibration phases."""
        self._display_intro()

        # Load parameters from firmware
        self.console.show_info("Loading odometry parameters from firmware...")
        self.params = await self.firmware.load_parameters()
        self.initial_params = self.params.model_copy()
        self.console.show_success("Parameters loaded successfully")
        self._display_parameters(self.params, "Initial Parameters")

        # Phase 1: Wheel distance
        while not await self._run_phase_1():
            self.console.show_warning("Retrying Phase 1...")

        # Phase 2: Right wheel radius
        while not await self._run_phase_2():
            self.console.show_warning("Retrying Phase 2...")

        # Phase 3: Left wheel radius
        while not await self._run_phase_3():
            self.console.show_warning("Retrying Phase 3...")

        # Final summary
        self.console.print()
        self._display_parameters(self.params, "Final Calibrated Parameters")

        # Save or restore
        save_params = await self.console.confirm("Save calibrated parameters to firmware?")
        self.console.show_info(f"Save: {save_params}")
        if save_params:
            self.console.show_info("Saving parameters to firmware...")
            await self.firmware.save_parameters(self.params)
            self.console.show_success("Parameters saved successfully!")
        else:
            self.console.show_warning("Restoring initial parameters...")
            await self.firmware.save_parameters(self.initial_params)
            self.console.show_warning("Initial parameters restored.")

    async def run(self) -> None:
        """Main entry point: connect, run calibration, disconnect."""
        try:
            await self._connect()
            await self._run_calibration()
        except KeyboardInterrupt:
            self.console.show_warning("\nCalibration interrupted by user")
            if self.initial_params and self.firmware:
                self.console.show_warning("Restoring initial parameters...")
                await self.firmware.save_parameters(self.initial_params)
            sys.exit(0)
        except Exception as e:
            self.console.show_error(str(e))
            logger.error("Unexpected error during calibration")
            if self.initial_params and self.firmware:
                try:
                    await self.firmware.save_parameters(self.initial_params)
                except Exception:
                    pass
            sys.exit(1)
        finally:
            await self._disconnect()
