"""
Empirical Autotuning for PID Calibration.

Contains the TelemetryCollector for oscillation analysis and the
empirical autotuning algorithm based on step response analysis.

Algorithm:
    1. Start with very low Kp, Ki=0, Kd=0
    2. Multiply Kp each iteration until oscillation is detected
    3. Use Ziegler-Nichols to compute optimal Kp
    4. Same process for Ki with binary search refinement
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from cogip.models import TelemetryData
from cogip.tools.firmware_telemetry.firmware_telemetry_manager import FirmwareTelemetryManager
from cogip.utils.console_ui import ConsoleUI
from . import logger
from .firmware_adapter import FirmwareAdapter
from .types import PidGains, PidType


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
        - If delta_error changes sign frequently -> error is oscillating

        Args:
            sign_change_threshold: Ratio of sign changes above which we consider oscillating

        Returns:
            True if oscillation detected, False otherwise
        """
        n_samples = min(len(self.speed_order_samples), len(self.current_speed_samples))
        if n_samples < 10:
            logger.debug(f"Not enough samples: {n_samples}")
            return False

        tracking_error = [
            self.speed_order_samples[i] - self.current_speed_samples[i]
            for i in range(n_samples)
        ]

        delta_error = [
            tracking_error[i] - tracking_error[i - 1]
            for i in range(1, n_samples)
        ]

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


async def run_empirical_autotune(
    pid_type: PidType,
    gains: PidGains,
    firmware: FirmwareAdapter,
    telemetry_manager: FirmwareTelemetryManager,
    console: ConsoleUI,
    linear_distance_mm: int,
    angular_distance_deg: int,
) -> PidGains:
    """
    Run empirical autotuning based on step response analysis.

    Algorithm:
    1. Start with very low Kp (0.01), Ki=0, Kd=0
    2. Multiply Kp by 1.1 each iteration until oscillation is detected
    3. Use Ziegler-Nichols (Ku * 0.6) for optimal Kp
    4. Same process for Ki with binary search refinement

    Args:
        pid_type: Type of PID controller being tuned
        gains: Current PID gains (will be updated)
        firmware: Firmware adapter for motion control
        telemetry_manager: Telemetry manager for data collection
        console: Console UI for user interaction
        linear_distance_mm: Distance for linear movements
        angular_distance_deg: Angle for angular movements

    Returns:
        Final tuned PidGains
    """
    console.show_rule("Empirical Autotuning")
    console.show_info(
        "Automatic tuning: finds optimal gains by detecting oscillations in telemetry data."
    )

    # Determine movement parameters and telemetry keys based on PID type
    if pid_type in (PidType.LINEAR_POSE, PidType.LINEAR_SPEED, PidType.LINEAR_POSE_TEST):
        distance = linear_distance_mm
        is_linear = True
        speed_order_key = "linear_speed_order"
        speed_command_key = "linear_speed_command"
        current_speed_key = "linear_current_speed"
    else:
        distance = angular_distance_deg
        is_linear = False
        speed_order_key = "angular_speed_order"
        speed_command_key = "angular_speed_command"
        current_speed_key = "angular_current_speed"

    collector = TelemetryCollector(
        speed_order_key=speed_order_key,
        speed_command_key=speed_command_key,
        current_speed_key=current_speed_key,
    )

    original_callback = telemetry_manager.sio_events._telemetry_callback

    def combined_callback(data: TelemetryData) -> None:
        collector.on_telemetry(data)
        if original_callback:
            original_callback(data)

    telemetry_manager.sio_events.set_telemetry_callback(combined_callback)

    async def perform_step_response() -> tuple[int, int, float]:
        """Perform step response and return (n_samples, sign_changes, ratio)."""
        await firmware.set_start_position(0, 0, 0)
        await asyncio.sleep(0.1)

        collector.start()

        if is_linear:
            await firmware.goto(distance, 0, 0, timeout=5.0)
            await asyncio.sleep(0.3)
            await firmware.goto(0, 0, 0, timeout=5.0)
        else:
            await firmware.goto(0, 0, distance, timeout=5.0)
            await asyncio.sleep(0.3)
            await firmware.goto(0, 0, 0, timeout=5.0)

        collector.stop()
        await asyncio.sleep(0.2)

        n_samples = min(len(collector.speed_order_samples), len(collector.current_speed_samples))

        sign_changes = 0
        if n_samples > 2:
            tracking_error = [
                collector.speed_order_samples[i] - collector.current_speed_samples[i]
                for i in range(n_samples)
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
        oscillation_threshold = await console.get_float(
            "Oscillation threshold (%)", default=10.0
        )
        oscillation_threshold /= 100.0

        async def test_gains_for_oscillation() -> bool:
            """Perform step response and check oscillation against threshold."""
            n_samples, sign_changes, ratio = await perform_step_response()
            oscillates = ratio > oscillation_threshold
            console.show_info(
                f"Collected {n_samples} samples, sign_changes={sign_changes} ({ratio:.1%}) -> "
                f"{'[red]Oscillation detected[/red]' if oscillates else '[green]Stable[/green]'}"
            )
            return oscillates

        await console.wait_for_enter("Press Enter to start autotuning")

        # Phase 1: Find oscillation point by multiplying Kp
        console.show_rule("Phase 1: Finding Critical Kp")
        console.show_info("Increasing Kp until oscillation is detected...")

        kp_multiplier = 1.1
        current_kp = await console.get_float("Starting Kp", default=1.0)
        best_kp = current_kp

        iteration = 0
        while True:
            iteration += 1

            test_gains = PidGains(kp=current_kp, ki=0.0, kd=0.0)
            await firmware.save_pid_gains(pid_type, test_gains)

            console.show_rule(f"Kp Iteration {iteration}")
            console.show_info(f"Testing Kp = {current_kp:.4f}")

            oscillates = await test_gains_for_oscillation()

            if oscillates:
                ku = current_kp
                best_kp = ku * 0.6
                console.show_success(f"Ku = {ku:.4f}, optimal Kp = Ku * 0.6 = {best_kp:.4f}")
                break
            else:
                current_kp *= kp_multiplier

        # Phase 2: Find optimal Ki
        console.show_rule("Phase 2: Finding Critical Ki")
        console.show_info("Increasing Ki until oscillation is detected...")

        ki_multiplier = 10.0
        current_ki = 1e-6
        last_stable_ki = 0.0
        oscillating_ki: float | None = None

        iteration = 0
        while oscillating_ki is None:
            iteration += 1

            test_gains = PidGains(kp=best_kp, ki=current_ki, kd=0.0)
            await firmware.save_pid_gains(pid_type, test_gains)

            console.show_rule(f"Ki Iteration {iteration}")
            console.show_info(f"Testing Ki = {current_ki:.2e} (Kp = {best_kp:.4f})")

            oscillates = await test_gains_for_oscillation()

            if oscillates:
                oscillating_ki = current_ki
            else:
                last_stable_ki = current_ki
                current_ki *= ki_multiplier

        # Binary search for Ki
        console.show_rule("Ki Binary Search")
        console.show_info(f"Range: [{last_stable_ki:.2e}, {oscillating_ki:.2e}]")

        low_ki = last_stable_ki
        high_ki = oscillating_ki
        best_ki = last_stable_ki
        max_binary_iterations = 5

        for i in range(max_binary_iterations):
            mid_ki = (low_ki + high_ki) / 2

            test_gains = PidGains(kp=best_kp, ki=mid_ki, kd=0.0)
            await firmware.save_pid_gains(pid_type, test_gains)

            console.show_rule(f"Ki Binary {i + 1}/{max_binary_iterations}")
            console.show_info(f"Testing Ki = {mid_ki:.2e} [{low_ki:.2e}, {high_ki:.2e}]")

            oscillates = await test_gains_for_oscillation()

            if oscillates:
                high_ki = mid_ki
            else:
                low_ki = mid_ki
                best_ki = mid_ki

        console.show_success(f"Optimal Ki found: {best_ki:.2e}")

        final_gains = PidGains(kp=best_kp, ki=best_ki, kd=0.0)
        await firmware.save_pid_gains(pid_type, final_gains)

        console.show_rule("Autotuning Complete")
        return final_gains

    finally:
        telemetry_manager.sio_events.set_telemetry_callback(original_callback)
