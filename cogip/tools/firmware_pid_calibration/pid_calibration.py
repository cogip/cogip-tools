"""
PID Calibration Tool for differential drive robots.

Calibrates PID controller parameters through automated tuning procedures.
"""

from __future__ import annotations
import asyncio
import sys
from dataclasses import dataclass, field

import socketio

from cogip.models.firmware_parameter import FirmwareParametersGroup
from cogip.models.firmware_telemetry import TelemetryData
from cogip.tools.firmware_parameter_manager.firmware_parameter_manager import FirmwareParameterManager
from cogip.tools.firmware_telemetry.firmware_telemetry_manager import FirmwareTelemetryManager
from cogip.utils.console_ui import ConsoleUI
from . import logger
from .firmware_adapter import FirmwareAdapter
from .sio_events import SioEvents
from .types import CalibrationMode, PidGains, PidType


@dataclass
class TelemetryCollector:
    """Collects telemetry samples for oscillation analysis.

    Collects speed_order, speed_command, and current_speed to analyze tracking error.
    """

    speed_order_key: str
    speed_command_key: str
    current_speed_key: str
    speed_order_samples: list[float] = field(default_factory=list)
    speed_command_samples: list[float] = field(default_factory=list)
    current_speed_samples: list[float] = field(default_factory=list)
    collecting: bool = False
    _key_hashes: dict[int, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Compute key hashes after initialization."""
        from cogip.models.firmware_telemetry import fnv1a_hash

        self._key_hashes = {
            fnv1a_hash(self.speed_order_key): "speed_order",
            fnv1a_hash(self.speed_command_key): "speed_command",
            fnv1a_hash(self.current_speed_key): "current_speed",
        }

    def start(self) -> None:
        """Start collecting samples."""
        self.speed_order_samples.clear()
        self.speed_command_samples.clear()
        self.current_speed_samples.clear()
        self.collecting = True

    def stop(self) -> None:
        """Stop collecting samples."""
        self.collecting = False

    def on_telemetry(self, data: TelemetryData) -> None:
        """Callback for telemetry data."""
        if not self.collecting:
            return
        key_type = self._key_hashes.get(data.key_hash)
        if key_type == "speed_order":
            self.speed_order_samples.append(float(data.value))
        elif key_type == "speed_command":
            self.speed_command_samples.append(float(data.value))
        elif key_type == "current_speed":
            self.current_speed_samples.append(float(data.value))

    def detect_oscillation(self, sign_change_threshold: float = 0.01) -> bool:
        """
        Detect oscillation by analyzing the variation of tracking error.

        Algorithm:
        - tracking_error = speed_order - current_speed
        - delta_error = tracking_error[i] - tracking_error[i-1]
        - If delta_error changes sign frequently → error is oscillating

        Args:
            sign_change_threshold: Ratio of sign changes above which we consider oscillating

        Returns:
            True if oscillation detected, False otherwise
        """
        # Need matching samples
        n_samples = min(len(self.speed_order_samples), len(self.current_speed_samples))
        if n_samples < 10:
            logger.debug(f"Not enough samples: {n_samples}")
            return False

        # Compute tracking error
        tracking_error = [self.speed_order_samples[i] - self.current_speed_samples[i] for i in range(n_samples)]

        # Compute delta (variation) of tracking error
        delta_error = [tracking_error[i] - tracking_error[i - 1] for i in range(1, n_samples)]

        # Count sign changes in delta_error (error oscillating up/down)
        sign_changes = 0
        for i in range(1, len(delta_error)):
            if delta_error[i - 1] * delta_error[i] < 0:
                sign_changes += 1

        sign_change_ratio = sign_changes / (len(delta_error) - 1) if len(delta_error) > 1 else 0
        is_oscillating = sign_change_ratio > sign_change_threshold

        logger.debug(
            f"Oscillation detection: sign_changes={sign_changes}/{len(delta_error) - 1}, "
            f"ratio={sign_change_ratio:.2%}, threshold={sign_change_threshold:.2%}, "
            f"oscillating={is_oscillating}"
        )

        return is_oscillating


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
    LINEAR_DISTANCE_MM = 500  # 1 meter
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

        # Calibration mode (selected by user)
        self.calibration_mode: CalibrationMode = CalibrationMode.MANUAL

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

    async def _select_calibration_mode(self) -> None:
        """Display calibration mode selection menu and get user choice."""
        self.console.show_rule("Calibration Mode Selection")

        # Display options table
        table = self.console.create_table(
            title="Available Calibration Modes",
            columns=[
                ("#", {"style": "value", "justify": "right"}),
                ("Mode", {"style": "label"}),
                ("Description", {"style": "muted"}),
            ],
        )
        for row in CalibrationMode.table_rows():
            table.add_row(*row)
        self.console.print(table)
        self.console.print()

        # Get selection by number
        choice = await self.console.get_choice(
            "Select calibration mode",
            choices=CalibrationMode.choices(),
            default=str(CalibrationMode.MANUAL.index),
        )

        self.calibration_mode = CalibrationMode.from_index(int(choice))
        self.console.show_success(f"Selected: {self.calibration_mode.label}")

    def _format_gain(self, value: float) -> str:
        """Format a gain value, using scientific notation for very small values."""
        if value == 0.0:
            return "0.0"
        elif abs(value) < 0.0001:
            return f"{value:.2e}"
        else:
            return f"{value:.4f}"

    def _display_gains(self, gains: PidGains, title: str) -> None:
        """Display PID gains in a table."""
        self.console.show_key_value_table(
            [
                ("Kp", self._format_gain(gains.kp)),
                ("Ki", self._format_gain(gains.ki)),
                ("Kd", self._format_gain(gains.kd)),
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

    async def _run_pose_test_loop(self) -> None:
        """Run simple pose test loop (linear movement only, no tuning)."""
        self.console.show_rule("Pose Test")
        dist = self.LINEAR_DISTANCE_MM
        self.console.show_info(f"Movement: {dist}mm forward, then {dist}mm backward")
        self.console.show_info("This is a test mode - no coefficient tuning")

        iteration = 0
        while True:
            iteration += 1

            # Reset graph curves for new iteration
            self._start_iteration()

            # Set starting position at origin
            await self.firmware.set_start_position(0, 0, 0)

            self.console.show_rule(f"Test Iteration {iteration}")

            # Forward movement
            await self.console.wait_for_enter("Press Enter to start movement")
            self._start_recording()
            self.console.show_info(f"Moving forward {dist}mm...")
            if not await self.firmware.goto(dist, 0, 0):
                self.console.show_warning("Movement timeout")

            await asyncio.sleep(0.25)
            self.console.show_info(f"Moving backward {dist}mm...")
            if not await self.firmware.goto(0, 0, 0):
                self.console.show_warning("Movement timeout")
            self._stop_recording()

            # Ask to continue
            self.console.print()
            continue_test = await self.console.confirm("Run another iteration?", default=True)

            if not continue_test:
                self.console.show_success("Test complete!")
                break

    async def _run_empirical_autotune(self) -> None:
        """
        Run empirical autotuning based on step response analysis.

        Algorithm:
        1. Start with very low Kp (0.01), Ki=0, Kd=0
        2. Multiply Kp by 1.5 each iteration until oscillation is detected
        3. Use binary search (dichotomy) between last stable and oscillating Kp
        4. Same process for Ki
        """
        self.console.show_rule("Empirical Autotuning")
        self.console.show_info("Automatic tuning: finds optimal gains by detecting oscillations in telemetry data.")

        # Determine movement parameters and telemetry keys based on PID type
        if self.pid_type in (PidType.LINEAR_POSE, PidType.LINEAR_SPEED, PidType.LINEAR_POSE_TEST):
            distance = self.LINEAR_DISTANCE_MM
            is_linear = True
            speed_order_key = "linear_speed_order"
            speed_command_key = "linear_speed_command"
            current_speed_key = "linear_current_speed"
        else:
            distance = self.ANGULAR_DISTANCE_DEG
            is_linear = False
            speed_order_key = "angular_speed_order"
            speed_command_key = "angular_speed_command"
            current_speed_key = "angular_current_speed"

        # Create telemetry collector (collects speed_order, speed_command, current_speed)
        collector = TelemetryCollector(
            speed_order_key=speed_order_key, speed_command_key=speed_command_key, current_speed_key=current_speed_key
        )

        # Register collector callback
        original_callback = self.telemetry_manager.sio_events._telemetry_callback

        def combined_callback(data: TelemetryData) -> None:
            collector.on_telemetry(data)
            if original_callback:
                original_callback(data)

        self.telemetry_manager.sio_events.set_telemetry_callback(combined_callback)

        async def perform_step_response() -> bool:
            """Perform step response and return True if oscillation detected."""
            self._start_iteration()
            await self.firmware.set_start_position(0, 0, 0)
            await asyncio.sleep(0.1)  # Let the engine process the new position

            collector.start()
            self._start_recording()

            if is_linear:
                await self.firmware.goto(distance, 0, 0, timeout=5.0)
                await asyncio.sleep(0.3)
                await self.firmware.goto(0, 0, 0, timeout=5.0)
            else:
                await self.firmware.goto(0, 0, distance, timeout=5.0)
                await asyncio.sleep(0.3)
                await self.firmware.goto(0, 0, 0, timeout=5.0)

            self._stop_recording()
            collector.stop()

            await asyncio.sleep(0.2)

            n_samples = min(len(collector.speed_order_samples), len(collector.current_speed_samples))

            # Calculate sign change ratio for display
            sign_changes = 0
            if n_samples > 2:
                # Compute tracking error and its delta
                tracking_error = [
                    collector.speed_order_samples[i] - collector.current_speed_samples[i] for i in range(n_samples)
                ]
                delta_error = [tracking_error[i] - tracking_error[i - 1] for i in range(1, n_samples)]
                for i in range(1, len(delta_error)):
                    if delta_error[i - 1] * delta_error[i] < 0:
                        sign_changes += 1
                ratio = sign_changes / (len(delta_error) - 1) if len(delta_error) > 1 else 0
            else:
                ratio = 0

            return n_samples, sign_changes, ratio

        try:
            # Ask for oscillation threshold
            oscillation_threshold = await self.console.get_float("Oscillation threshold (%)", default=10.0)
            oscillation_threshold /= 100.0  # Convert to ratio

            async def test_gains_for_oscillation() -> bool:
                """Perform step response and check oscillation against threshold."""
                n_samples, sign_changes, ratio = await perform_step_response()
                oscillates = ratio > oscillation_threshold
                self.console.show_info(
                    f"Collected {n_samples} samples, sign_changes={sign_changes} ({ratio:.1%}) → "
                    f"{'[red]Oscillation detected[/red]' if oscillates else '[green]Stable[/green]'}"
                )
                return oscillates

            await self.console.wait_for_enter("Press Enter to start autotuning")

            # Phase 1: Find oscillation point by multiplying Kp
            self.console.show_rule("Phase 1: Finding Critical Kp")
            self.console.show_info("Increasing Kp until oscillation is detected...")

            kp_multiplier = 1.1
            current_kp = await self.console.get_float("Starting Kp", default=1.0)
            best_kp = current_kp

            iteration = 0
            while True:
                iteration += 1

                test_gains = PidGains(kp=current_kp, ki=0.0, kd=0.0)
                await self.firmware.save_pid_gains(self.pid_type, test_gains)
                self.gains = test_gains

                self.console.show_rule(f"Kp Iteration {iteration}")
                self.console.show_info(f"Testing Kp = {current_kp:.4f}")

                oscillates = await test_gains_for_oscillation()

                if oscillates:
                    # Ziegler-Nichols: Kp = Ku * 0.6
                    ku = current_kp
                    best_kp = ku * 0.6
                    self.console.show_success(f"Ku = {ku:.4f}, optimal Kp = Ku * 0.6 = {best_kp:.4f}")
                    break
                else:
                    current_kp *= kp_multiplier

            # Phase 2: Find optimal Ki
            self.console.show_rule("Phase 2: Finding Critical Ki")
            self.console.show_info("Increasing Ki until oscillation is detected...")

            ki_multiplier = 10.0
            current_ki = 1e-6
            last_stable_ki = 0.0
            oscillating_ki: float | None = None

            iteration = 0
            while oscillating_ki is None:
                iteration += 1

                test_gains = PidGains(kp=best_kp, ki=current_ki, kd=0.0)
                await self.firmware.save_pid_gains(self.pid_type, test_gains)
                self.gains = test_gains

                self.console.show_rule(f"Ki Iteration {iteration}")
                self.console.show_info(f"Testing Ki = {current_ki:.2e} (Kp = {best_kp:.4f})")

                oscillates = await test_gains_for_oscillation()

                if oscillates:
                    oscillating_ki = current_ki
                else:
                    last_stable_ki = current_ki
                    current_ki *= ki_multiplier

            # Binary search for Ki
            self.console.show_rule("Ki Binary Search")
            self.console.show_info(f"Range: [{last_stable_ki:.2e}, {oscillating_ki:.2e}]")

            low_ki = last_stable_ki
            high_ki = oscillating_ki
            best_ki = last_stable_ki
            max_binary_iterations = 5

            for i in range(max_binary_iterations):
                mid_ki = (low_ki + high_ki) / 2

                test_gains = PidGains(kp=best_kp, ki=mid_ki, kd=0.0)
                await self.firmware.save_pid_gains(self.pid_type, test_gains)
                self.gains = test_gains

                self.console.show_rule(f"Ki Binary {i + 1}/{max_binary_iterations}")
                self.console.show_info(f"Testing Ki = {mid_ki:.2e} [{low_ki:.2e}, {high_ki:.2e}]")

                oscillates = await test_gains_for_oscillation()

                if oscillates:
                    high_ki = mid_ki
                else:
                    low_ki = mid_ki
                    best_ki = mid_ki

            self.console.show_success(f"Optimal Ki found: {best_ki:.2e}")

            # Set final gains
            self.gains = PidGains(kp=best_kp, ki=best_ki, kd=0.0)
            await self.firmware.save_pid_gains(self.pid_type, self.gains)

            self.console.show_rule("Autotuning Complete")
            self._display_gains(self.gains, "Final Gains")

        finally:
            # Restore original callback
            self.telemetry_manager.sio_events.set_telemetry_callback(original_callback)

    def _display_final_summary(self) -> None:
        """Display final comparison between initial and current gains."""
        self.console.show_rule("Calibration Summary")
        self.console.show_comparison_table(
            [
                ("Kp", self._format_gain(self.initial_gains.kp), self._format_gain(self.gains.kp)),
                ("Ki", self._format_gain(self.initial_gains.ki), self._format_gain(self.gains.ki)),
                ("Kd", self._format_gain(self.initial_gains.kd), self._format_gain(self.gains.kd)),
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

        # LINEAR_POSE_TEST is just a test mode, no calibration
        if self.pid_type == PidType.LINEAR_POSE_TEST:
            await self._run_pose_test_loop()
            await self.console.wait_for_enter("Press Enter to return to menu")
            return

        # Select calibration mode for actual tuning
        await self._select_calibration_mode()

        # Load parameters from firmware
        self.console.show_info("Loading pid gains from firmware...")
        self.gains = await self.firmware.load_pid_gains(self.pid_type)
        self.initial_gains = self.gains.copy()
        self.console.show_success("Gains loaded successfully")

        # Run appropriate calibration based on mode
        if self.calibration_mode == CalibrationMode.EMPIRICAL_AUTOTUNE:
            await self._run_empirical_autotune()
        elif self.pid_type in (PidType.LINEAR_POSE, PidType.LINEAR_SPEED):
            await self._run_linear_calibration_loop()
        else:
            await self._run_angular_calibration_loop()

        # Display final summary
        self._display_final_summary()

        # Wait for user before returning to menu
        await self.console.wait_for_enter("Press Enter to return to menu")

    async def run(self) -> None:
        """Main entry point: connect, run calibration loop, disconnect."""
        try:
            await self._connect()

            # Main loop - return to menu after each calibration
            while True:
                try:
                    await self._run_calibration()
                except KeyboardInterrupt:
                    self.console.show_warning("\nCalibration interrupted")
                    # Ask if user wants to quit or continue
                    quit_now = await self.console.confirm("Quit calibration tool?", default=False)
                    if quit_now:
                        break
                    # Otherwise continue to menu

        except KeyboardInterrupt:
            self.console.show_warning("\nExiting...")
        except Exception as e:
            self.console.show_error(str(e))
            logger.error("Unexpected error during calibration")
            sys.exit(1)
        finally:
            await self._disconnect()
