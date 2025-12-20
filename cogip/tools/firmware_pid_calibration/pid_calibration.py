"""
PID Calibration Tool for differential drive robots.

Calibrates PID controller parameters through automated tuning procedures.
"""

from __future__ import annotations
import asyncio
import sys

import socketio

from cogip.models.firmware_parameter import FirmwareParametersGroup
from cogip.tools.firmware_parameter_manager.firmware_parameter_manager import FirmwareParameterManager
from cogip.tools.firmware_telemetry.firmware_telemetry_manager import FirmwareTelemetryManager
from cogip.utils.console_ui import ConsoleUI
from . import logger
from .firmware_adapter import FirmwareAdapter
from .sio_events import SioEvents
from .types import PidGains, PidType

TYPE_CHECKING = False
if TYPE_CHECKING:
    from .telemetry_graph import TelemetryGraphBridge, TelemetryGraphWidget


class PidCalibration:
    """
    PID Calibration controller.

    Orchestrates the calibration process by coordinating:
    - SocketIO connection to cogip-server
    - FirmwareParameterManager for parameter access
    - FirmwareTelemetryManager for real-time data
    - User interaction via ConsoleUI
    """

    # Calibration movement constants
    LINEAR_DISTANCE_MM = 1000  # 1 meter
    ANGULAR_DISTANCE_DEG = 180  # 180 degrees

    def __init__(self, server_url: str, parameters_group: FirmwareParametersGroup, *, enable_graph: bool = False):
        """
        Initialize the calibration controller.

        Args:
            server_url: URL of the cogip-server
            parameters_group: Firmware parameters configuration
            enable_graph: If True, show real-time telemetry graph window
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

        # PID type to calibrate (selected by user)
        self.pid_type: PidType = PidType.LINEAR_POSE

        # Calibration state
        self.gains: PidGains | None = None
        self.initial_gains: PidGains | None = None

        # Graph state
        self._enable_graph = enable_graph
        self._graph_widget: TelemetryGraphWidget | None = None
        self._graph_bridge: TelemetryGraphBridge | None = None

        if enable_graph:
            self._setup_graph()

    def _setup_graph(self) -> None:
        """Initialize the graph widget and bridge."""
        from .telemetry_graph import TelemetryGraphBridge, TelemetryGraphWidget

        self._graph_widget = TelemetryGraphWidget()
        self._graph_bridge = TelemetryGraphBridge(self._graph_widget)
        self._graph_widget.show()

    def _start_iteration(self) -> None:
        """Called at the start of each calibration iteration to reset curves."""
        if self._graph_bridge:
            self._graph_bridge.emit_clear()

    def _start_recording(self) -> None:
        """Start recording telemetry data to graph."""
        if self._graph_bridge:
            self._graph_bridge.emit_start_recording()

    def _stop_recording(self) -> None:
        """Stop recording telemetry data to graph."""
        if self._graph_bridge:
            self._graph_bridge.emit_stop_recording()

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

        # Register telemetry callback for graph if enabled
        if self._graph_bridge:
            self.telemetry_manager.sio_events.set_telemetry_callback(self._graph_bridge.emit_telemetry)

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
            "This tool calibrates the robot's PIDs gains\n",
            title="PIDs Calibration Tool",
        )

    async def _select_pid_type(self) -> None:
        """Display PID type selection menu and get user choice."""
        self.console.show_rule("PID Type Selection")

        # Display options table
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

        # Get selection by number
        choice = await self.console.get_choice(
            "Select PID type",
            choices=PidType.choices(),
            default=str(PidType.LINEAR_POSE.index),
        )

        self.pid_type = PidType.from_index(int(choice))
        self.console.show_success(f"Selected: {self.pid_type.label}")

        # Configure graph to show relevant curves for this PID type
        if self._graph_bridge:
            self._graph_bridge.emit_set_pid_type(self.pid_type)

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

    async def _ask_new_gains(self) -> PidGains:
        """Ask user for new PID gains."""
        self.console.show_rule("Enter New Gains")
        kp = await self.console.get_float("Kp", default=self.gains.kp)
        ki = await self.console.get_float("Ki", default=self.gains.ki)
        kd = await self.console.get_float("Kd", default=self.gains.kd)
        return PidGains(kp=kp, ki=ki, kd=kd)

    async def _run_linear_calibration_loop(self) -> None:
        """Run the linear PID calibration loop."""
        self.console.show_rule("Linear Calibration")
        dist = self.LINEAR_DISTANCE_MM
        self.console.show_info(f"Movement: {dist}mm forward, then {dist}mm backward")

        iteration = 0
        while True:
            iteration += 1

            # Reset graph curves for new iteration
            self._start_iteration()

            # Set starting position at origin
            await self.firmware.set_start_position(0, 0, 0)

            self.console.show_rule(f"Iteration {iteration}")
            self._display_gains(self.gains, "Current Gains")

            # Forward movement
            await self.console.wait_for_enter("Press Enter to start forward movement")
            self._start_recording()
            self.console.show_info(f"Moving forward {self.LINEAR_DISTANCE_MM}mm...")
            if not await self.firmware.goto(self.LINEAR_DISTANCE_MM, 0, 0):
                self.console.show_warning("Movement timeout - robot may not have reached target")

            await asyncio.sleep(0.25)
            self.console.show_info(f"Moving backward {self.LINEAR_DISTANCE_MM}mm...")
            if not await self.firmware.goto(0, 0, 0):
                self.console.show_warning("Movement timeout - robot may not have reached target")
            self._stop_recording()

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
        self.console.show_info(f"Movement: +{angle}deg rotation, then -{angle}deg rotation")

        iteration = 0
        while True:
            iteration += 1

            # Reset graph curves for new iteration
            self._start_iteration()

            # Set starting position at origin
            await self.firmware.set_start_position(0, 0, 0)

            self.console.show_rule(f"Iteration {iteration}")
            self._display_gains(self.gains, "Current Gains")

            # Positive rotation
            await self.console.wait_for_enter("Press Enter to start positive rotation")
            self._start_recording()
            self.console.show_info(f"Rotating +{self.ANGULAR_DISTANCE_DEG}deg...")
            if not await self.firmware.goto(0, 0, self.ANGULAR_DISTANCE_DEG):
                self.console.show_warning("Movement timeout - robot may not have reached target")

            await asyncio.sleep(0.25)
            self.console.show_info(f"Rotating -{self.ANGULAR_DISTANCE_DEG}deg...")
            if not await self.firmware.goto(0, 0, 0):
                self.console.show_warning("Movement timeout - robot may not have reached target")
            self._stop_recording()

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

    def _display_final_summary(self) -> None:
        """Display final comparison between initial and current gains."""
        self.console.show_rule("Calibration Summary")
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

    async def _run_calibration(self) -> None:
        """Run the PID calibration procedure."""
        self._display_intro()
        await self._select_pid_type()

        # Set the appropriate controller for the selected PID type
        controller = self.pid_type.controller
        self.console.show_info(f"Setting controller to {controller.name}...")
        await self.firmware.set_controller(controller)
        self.console.show_success(f"Controller set to {controller.name}")

        # Load parameters from firmware
        self.console.show_info("Loading pid gains from firmware...")
        self.gains = await self.firmware.load_pid_gains(self.pid_type)
        self.initial_gains = self.gains.copy()
        self.console.show_success("Gains loaded successfully")

        # Run appropriate calibration loop
        if self.pid_type in (PidType.LINEAR_POSE, PidType.LINEAR_SPEED):
            await self._run_linear_calibration_loop()
        else:
            await self._run_angular_calibration_loop()

        # Display final summary
        self._display_final_summary()

    async def run(self) -> None:
        """Main entry point: connect, run calibration, disconnect."""
        try:
            await self._connect()
            await self._run_calibration()
        except KeyboardInterrupt:
            self.console.show_warning("\nCalibration interrupted by user")
            sys.exit(0)
        except Exception as e:
            self.console.show_error(str(e))
            logger.error("Unexpected error during calibration")
            sys.exit(1)
        finally:
            await self._disconnect()
