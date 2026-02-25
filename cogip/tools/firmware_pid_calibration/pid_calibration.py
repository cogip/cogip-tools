"""
PID Calibration Tool for differential drive robots.

Calibrates PID controller parameters through manual tuning.

Phases:
    1. Select PID type (linear/angular pose/speed)
    2. Set appropriate controller
    3. Iterative manual tuning loop with live movement tests

Usage:
    - Select which PID to calibrate
    - Observe robot behavior during test movements
    - Adjust Kp, Ki, Kd until satisfactory
    - Save or restore initial gains
"""

from __future__ import annotations

import asyncio
import sys

import socketio

from cogip.models import FirmwareParametersGroup
from cogip.tools.firmware_parameter_manager.firmware_parameter_manager import FirmwareParameterManager
from cogip.tools.firmware_telemetry.firmware_telemetry_manager import FirmwareTelemetryManager
from cogip.tools.firmware_telemetry.graph.bridge import TelemetryGraphBridge
from cogip.utils.console_ui import ConsoleUI
from . import logger
from .firmware_adapter import FirmwareAdapter
from .sio_events import SioEvents
from .types import PidGains, PidType


class PidCalibration:
    """
    PID Calibration controller.

    Orchestrates the calibration process by coordinating:
    - SocketIO connection to cogip-server
    - FirmwareAdapter for all firmware operations
    - User interaction via ConsoleUI
    """

    # Calibration movement constants
    LINEAR_DISTANCE_MM = 500
    ANGULAR_DISTANCE_DEG = 180

    def __init__(
        self,
        server_url: str,
        parameters_group: FirmwareParametersGroup,
        graph_bridge: TelemetryGraphBridge | None = None,
    ):
        """
        Initialize the calibration controller.

        Args:
            server_url: URL of the cogip-server
            parameters_group: Firmware parameters configuration
            graph_bridge: Optional bridge for telemetry graph visualization
        """
        self.server_url = server_url
        self.console = ConsoleUI()
        self.graph_bridge = graph_bridge

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
            self.sio, self.param_manager, self.pose_reached_event, self.console
        )

        # Calibration state
        self.pid_type: PidType = PidType.LINEAR_POSE
        self.gains: PidGains | None = None
        self.initial_gains: PidGains | None = None

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

        # Wire telemetry data to graph bridge
        if self.graph_bridge:
            self.telemetry_manager.sio_events.set_telemetry_callback(self.graph_bridge.emit_telemetry)

    async def _disconnect(self) -> None:
        """Disconnect from server."""
        # Clear telemetry callback
        if self.graph_bridge:
            self.telemetry_manager.sio_events.set_telemetry_callback(None)

        # Disable telemetry (only if namespace is connected)
        if self.telemetry_manager.is_connected:
            await self.telemetry_manager.disable()
            await asyncio.sleep(0.2)

        if self.sio and self.sio.connected:
            await self.sio.disconnect()

    def _display_intro(self) -> None:
        """Display introduction panel."""
        self.console.show_panel(
            "This tool calibrates the robot's PID gains through manual tuning:\n"
            "1. [header]Select PID type[/] - Choose which controller to tune\n"
            "2. [header]Observe behavior[/] - Watch robot response to test movements\n"
            "3. [header]Adjust gains[/] - Modify Kp, Ki, Kd until satisfactory",
            title="PID Calibration Tool",
        )

    def _display_gains(self, gains: PidGains, title: str) -> None:
        """Display PID gains in a table."""
        self.console.show_key_value_table(
            [
                ("Kp", f"{gains.kp:.4f}"),
                ("Ki", f"{gains.ki:.4f}"),
                ("Kd", f"{gains.kd:.4f}"),
            ],
            title=title,
        )

    def _display_final_summary(self) -> None:
        """Display final comparison between initial and current gains."""
        self.console.show_comparison_table(
            [
                ("Kp", f"{self.initial_gains.kp:.4f}", f"{self.gains.kp:.4f}"),
                ("Ki", f"{self.initial_gains.ki:.4f}", f"{self.gains.ki:.4f}"),
                ("Kd", f"{self.initial_gains.kd:.4f}", f"{self.gains.kd:.4f}"),
            ],
            title=f"{self.pid_type.label} - Final Gains",
            before_header="Initial",
            after_header="Final",
        )

    async def _select_pid_type(self) -> None:
        """Display PID type selection menu and get user choice."""
        self.console.show_rule("PID Type Selection")

        table = self.console.create_table(
            title="Available PID Types",
            columns=[
                ("#", {"style": "value", "justify": "right"}),
                ("Type", {"style": "label"}),
                ("Description", {"style": "muted"}),
            ],
        )
        for row in PidType.table_rows():
            table.add_row(*row)
        self.console.print(table)
        self.console.print()

        choice = await self.console.get_choice(
            "Select PID type",
            choices=PidType.choices(),
            default=str(PidType.LINEAR_POSE.index),
        )

        self.pid_type = PidType.from_index(int(choice))
        self.console.show_success(f"Selected: {self.pid_type.label}")

    async def _ask_new_gains(self) -> PidGains:
        """Ask user for new PID gains."""
        self.console.show_rule("Enter New Gains")
        kp = await self.console.get_float("Kp", default=self.gains.kp)
        ki = await self.console.get_float("Ki", default=self.gains.ki)
        kd = await self.console.get_float("Kd", default=self.gains.kd)
        return PidGains(kp=kp, ki=ki, kd=kd)

    def _graph_clear_and_start(self) -> None:
        """Clear the graph and start recording."""
        if self.graph_bridge:
            self.graph_bridge.emit_clear()
            self.graph_bridge.emit_start_recording()

    def _graph_stop(self) -> None:
        """Stop recording on the graph."""
        if self.graph_bridge:
            self.graph_bridge.emit_stop_recording()

    def _load_graph_for_pid_type(self) -> None:
        """Load only the relevant graph plot for the selected PID type."""
        if not self.graph_bridge:
            return

        plot_map = {
            PidType.LINEAR_POSE: "Linear Speed",
            PidType.LINEAR_SPEED: "Linear Speed",
            PidType.ANGULAR_POSE: "Angular Speed",
            PidType.ANGULAR_SPEED: "Angular Speed",
        }
        title = plot_map.get(self.pid_type)
        if title:
            self.graph_bridge.emit_load_plot(title)

    async def _run_linear_calibration_loop(self) -> None:
        """Run the linear PID calibration loop."""
        self.console.show_rule("Linear Calibration")
        dist = self.LINEAR_DISTANCE_MM
        self.console.show_info(f"Movement: {dist} mm forward, then {dist} mm backward")

        iteration = 0
        while True:
            iteration += 1

            await self.firmware.set_start_position(0, 0, 0)
            self._graph_clear_and_start()

            self.console.show_rule(f"Iteration {iteration}")
            self._display_gains(self.gains, "Current Gains")

            # Forward movement
            await self.console.wait_for_enter("Press Enter to start forward movement")
            self.console.show_info(f"Moving forward {dist} mm...")
            if not await self.firmware.goto(dist, 0, 0):
                self.console.show_warning("Movement timeout - robot may not have reached target")

            await asyncio.sleep(0.25)
            self.console.show_info(f"Moving backward {dist} mm...")
            if not await self.firmware.goto(0, 0, 0):
                self.console.show_warning("Movement timeout - robot may not have reached target")

            self._graph_stop()

            # Ask if satisfied
            self.console.print()
            satisfied = await self.console.confirm("Is the behavior satisfactory?", default=False)

            if satisfied:
                self.console.show_success("Calibration complete!")
                break

            # Get new gains
            new_gains = await self._ask_new_gains()

            # Save new gains to firmware
            self.console.show_info("Saving new gains to firmware...")
            await self.firmware.save_pid_gains(self.pid_type, new_gains)
            self.gains = new_gains
            self.console.show_success("Gains saved")

    async def _run_angular_calibration_loop(self) -> None:
        """Run the angular PID calibration loop."""
        self.console.show_rule("Angular Calibration")
        angle = self.ANGULAR_DISTANCE_DEG
        self.console.show_info(f"Movement: +{angle} deg rotation, then -{angle} deg rotation")

        iteration = 0
        while True:
            iteration += 1

            await self.firmware.set_start_position(0, 0, 0)
            self._graph_clear_and_start()

            self.console.show_rule(f"Iteration {iteration}")
            self._display_gains(self.gains, "Current Gains")

            # Positive rotation
            await self.console.wait_for_enter("Press Enter to start positive rotation")
            self.console.show_info(f"Rotating +{angle} deg...")
            if not await self.firmware.goto(0, 0, angle):
                self.console.show_warning("Movement timeout - robot may not have reached target")

            await asyncio.sleep(0.25)
            self.console.show_info(f"Rotating -{angle} deg...")
            if not await self.firmware.goto(0, 0, 0):
                self.console.show_warning("Movement timeout - robot may not have reached target")

            self._graph_stop()

            # Ask if satisfied
            self.console.print()
            satisfied = await self.console.confirm("Is the behavior satisfactory?", default=False)

            if satisfied:
                self.console.show_success("Calibration complete!")
                break

            # Get new gains
            new_gains = await self._ask_new_gains()

            # Save new gains to firmware
            self.console.show_info("Saving new gains to firmware...")
            await self.firmware.save_pid_gains(self.pid_type, new_gains)
            self.gains = new_gains
            self.console.show_success("Gains saved")

    async def _run_pose_test_loop(self) -> None:
        """Run simple pose test loop (linear movement only, no tuning)."""
        self.console.show_rule("Pose Test")
        dist = self.LINEAR_DISTANCE_MM
        self.console.show_info(f"Movement: {dist}mm forward, then {dist}mm backward")
        self.console.show_info("This is a test mode - no coefficient tuning")

        iteration = 0
        while True:
            iteration += 1

            await self.firmware.set_start_position(0, 0, 0)
            self._graph_clear_and_start()

            self.console.show_rule(f"Test Iteration {iteration}")

            # Forward movement
            await self.console.wait_for_enter("Press Enter to start movement")
            self.console.show_info(f"Moving forward {dist}mm...")
            if not await self.firmware.goto(dist, 0, 0):
                self.console.show_warning("Movement timeout")

            await asyncio.sleep(0.25)
            self.console.show_info(f"Moving backward {dist}mm...")
            if not await self.firmware.goto(0, 0, 0):
                self.console.show_warning("Movement timeout")

            self._graph_stop()

            # Ask to continue
            self.console.print()
            continue_test = await self.console.confirm("Run another iteration?", default=True)

            if not continue_test:
                self.console.show_success("Test complete!")
                break

    async def _run_calibration(self) -> None:
        """Run the PID calibration procedure."""
        self._display_intro()
        await self._select_pid_type()
        self._load_graph_for_pid_type()

        # Set the appropriate controller for the selected PID type
        controller = self.pid_type.controller
        self.console.show_info(f"Setting controller to {controller.name}...")
        await self.firmware.set_controller(controller)
        self.console.show_success(f"Controller set to {controller.name}")

        # LINEAR_POSE_TEST is just a test mode, no calibration
        if self.pid_type == PidType.LINEAR_POSE_TEST:
            await self._run_pose_test_loop()
            return

        # Load gains from firmware
        self.console.show_info("Loading PID gains from firmware...")
        self.gains = await self.firmware.load_pid_gains(self.pid_type)
        self.initial_gains = self.gains.copy()
        self.console.show_success("Gains loaded successfully")

        # Run calibration loop based on PID type
        if self.pid_type in (PidType.LINEAR_POSE, PidType.LINEAR_SPEED):
            await self._run_linear_calibration_loop()
        else:
            await self._run_angular_calibration_loop()

        # Final summary
        self.console.print()
        self._display_final_summary()

        # Save or restore
        save_gains = await self.console.confirm("Save calibrated gains to firmware?")
        self.console.show_info(f"Save: {save_gains}")
        if save_gains:
            self.console.show_info("Saving gains to firmware...")
            await self.firmware.save_pid_gains(self.pid_type, self.gains)
            self.console.show_success("Gains saved successfully!")
        else:
            self.console.show_warning("Restoring initial gains...")
            await self.firmware.save_pid_gains(self.pid_type, self.initial_gains)
            self.console.show_warning("Initial gains restored.")

    async def run(self) -> None:
        """Main entry point: connect, run calibration, disconnect."""
        try:
            await self._connect()
            await self._run_calibration()
        except KeyboardInterrupt:
            self.console.show_warning("\nCalibration interrupted by user")
            if self.initial_gains and self.firmware:
                self.console.show_warning("Restoring initial gains...")
                await self.firmware.save_pid_gains(self.pid_type, self.initial_gains)
            sys.exit(0)
        except Exception as e:
            self.console.show_error(str(e))
            logger.error("Unexpected error during calibration")
            if self.initial_gains and self.firmware:
                try:
                    await self.firmware.save_pid_gains(self.pid_type, self.initial_gains)
                except Exception:
                    pass
            sys.exit(1)
        finally:
            await self._disconnect()
