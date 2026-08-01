"""
OTOS Calibration Tool.

Calibrates the two OTOS scalars (linear_scalar, angular_scalar) through two
phases:

    1. Linear scalar - commanded straight line vs. physically measured distance
    2. Angular scalar - commanded number of rotations vs. physically measured angle

The tool drives the robot through cogip-server, then prompts the operator
for the physically measured outcome, derives the corrected scalar and
writes it back to firmware (which re-programs the OTOS chip immediately).
"""

from __future__ import annotations
import asyncio
import sys

import socketio

from cogip.models import FirmwareParametersGroup, OTOSParameters
from cogip.tools.firmware_parameter_manager.firmware_parameter_manager import FirmwareParameterManager
from cogip.utils.console_ui import ConsoleUI
from . import logger
from .calculator import compute_angular_scalar, compute_linear_scalar
from .firmware_adapter import FirmwareAdapter
from .sio_events import SioEvents
from .types import OtosCalibrationPhaseType


class OTOSCalibration:
    """OTOS calibration controller."""

    def __init__(self, server_url: str, parameters_group: FirmwareParametersGroup):
        self.server_url = server_url
        self.console = ConsoleUI()

        self.pose_reached_event = asyncio.Event()

        self.sio = socketio.AsyncClient(logger=False)
        self.sio_ns = SioEvents(self)
        self.sio.register_namespace(self.sio_ns)

        self.param_manager = FirmwareParameterManager(self.sio, parameters_group)

        self.firmware = FirmwareAdapter(self.sio, self.param_manager, self.pose_reached_event, self.console)

        self.params: OTOSParameters | None = None
        self.initial_params: OTOSParameters | None = None

    async def _connect(self) -> None:
        self.console.show_info(f"Connecting to {self.server_url}...")
        await self.sio.connect(
            self.server_url,
            namespaces=[
                self.sio_ns.namespace,
                self.param_manager.namespace,
            ],
        )
        self.console.show_info("Waiting for connections...")
        while not (self.sio_ns.connected and self.param_manager.is_connected):
            await asyncio.sleep(0.1)
        self.console.show_success("Connected to cogip-server")

    async def _disconnect(self) -> None:
        if self.sio and self.sio.connected:
            await self.sio.disconnect()

    def _display_intro(self) -> None:
        self.console.show_panel(
            "This tool calibrates the OTOS sensor through 2 phases:\n"
            "1. [header]Linear scalar[/] - drive in a straight line, measure the physical distance\n"
            "2. [header]Angular scalar[/] - rotate N turns, measure the physical rotation\n\n"
            "New scalars are written back to firmware immediately and re-programmed on the OTOS chip.",
            title="OTOS Calibration Tool",
        )

    def _display_parameters(self, params: OTOSParameters, title: str) -> None:
        self.console.show_key_value_table(
            [
                ("Linear scalar", f"{params.linear_scalar:.6f}"),
                ("Angular scalar", f"{params.angular_scalar:.6f}"),
            ],
            title=title,
        )

    def _display_scalar_change(self, label: str, before: float, after: float) -> None:
        table = self.console.create_table(
            title=f"{label} result",
            columns=[
                ("Parameter", {"style": "label"}),
                ("Before", {"style": "muted", "justify": "right"}),
                ("After", {"style": "value", "justify": "right"}),
                ("Change", {"style": "warning", "justify": "right"}),
            ],
        )
        table.add_row(label, f"{before:.6f}", f"{after:.6f}", f"{after - before:+.6f}")
        self.console.print(table)

    async def _run_linear_phase(self) -> bool:
        phase = OtosCalibrationPhaseType.LINEAR_SCALAR
        self.console.show_rule(phase.title)
        self.console.show_info(phase.description)

        commanded_mm = await self.console.get_integer(phase.command_prompt, default=phase.command_default)

        await self.console.wait_for_enter(
            "Place the robot at the start mark, aligned forward. Press Enter to start the motion."
        )

        if not await self.firmware.execute_straight_line(commanded_mm):
            return False

        measured_mm = await self.console.get_float(phase.measurement_prompt, default=float(commanded_mm))

        try:
            new_scalar, clamped = compute_linear_scalar(self.params.linear_scalar, float(commanded_mm), measured_mm)
        except ValueError as exc:
            self.console.show_error(str(exc))
            return False

        if clamped:
            self.console.show_warning("Result was clamped to the OTOS allowed range. Check mechanical setup.")

        self._display_scalar_change("linear_scalar", self.params.linear_scalar, new_scalar)

        if not await self.console.confirm("Accept this result?"):
            return False

        await self.firmware.save_linear_scalar(new_scalar)
        self.params.linear_scalar = new_scalar
        self.console.show_success("linear_scalar written to firmware")
        return True

    async def _run_angular_phase(self) -> bool:
        phase = OtosCalibrationPhaseType.ANGULAR_SCALAR
        self.console.show_rule(phase.title)
        self.console.show_info(phase.description)

        num_rotations = await self.console.get_integer(phase.command_prompt, default=phase.command_default)
        commanded_deg = float(num_rotations) * 360.0

        await self.console.wait_for_enter(
            "Place a rotation marker (e.g. tape on the chassis aligned with a floor mark). "
            "Press Enter to start the rotation."
        )

        if not await self.firmware.execute_rotations(num_rotations):
            return False

        self.console.show_info(f"Commanded rotation: {commanded_deg:.1f}°")
        measured_deg = await self.console.get_float(phase.measurement_prompt, default=commanded_deg)

        try:
            new_scalar, clamped = compute_angular_scalar(self.params.angular_scalar, commanded_deg, measured_deg)
        except ValueError as exc:
            self.console.show_error(str(exc))
            return False

        if clamped:
            self.console.show_warning("Result was clamped to the OTOS allowed range. Check mechanical setup.")

        self._display_scalar_change("angular_scalar", self.params.angular_scalar, new_scalar)

        if not await self.console.confirm("Accept this result?"):
            return False

        await self.firmware.save_angular_scalar(new_scalar)
        self.params.angular_scalar = new_scalar
        self.console.show_success("angular_scalar written to firmware")
        return True

    async def _run_calibration(self) -> None:
        self._display_intro()

        self.console.show_info("Loading OTOS parameters from firmware...")
        self.params = await self.firmware.load_parameters()
        self.initial_params = self.params.model_copy()
        self.console.show_success("Parameters loaded successfully")
        self._display_parameters(self.params, "Initial Parameters")

        while not await self._run_linear_phase():
            if not await self.console.confirm("Retry linear phase?", default=True):
                break

        while not await self._run_angular_phase():
            if not await self.console.confirm("Retry angular phase?", default=True):
                break

        self.console.print()
        self._display_parameters(self.params, "Final Calibrated Parameters")

        if not await self.console.confirm("Keep calibrated parameters in firmware?", default=True):
            self.console.show_warning("Restoring initial parameters...")
            await self.firmware.save_parameters(self.initial_params)
            self.console.show_warning("Initial parameters restored.")

    async def run(self) -> None:
        try:
            await self._connect()
            await self._run_calibration()
        except KeyboardInterrupt:
            self.console.show_warning("\nCalibration interrupted by user")
            if self.initial_params and self.firmware:
                self.console.show_warning("Restoring initial parameters...")
                await self.firmware.save_parameters(self.initial_params)
            sys.exit(0)
        except Exception as exc:
            self.console.show_error(str(exc))
            logger.error("Unexpected error during OTOS calibration")
            if self.initial_params and self.firmware:
                try:
                    await self.firmware.save_parameters(self.initial_params)
                except Exception:
                    pass
            sys.exit(1)
        finally:
            await self._disconnect()
