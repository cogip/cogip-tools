"""
PID Calibration Models

Data types, enums, and dataclasses for the PID calibration tool.
"""

from dataclasses import dataclass
from enum import Enum

from cogip.tools.copilot.controller import ControllerEnum


class CalibrationMode(Enum):
    """Calibration modes."""

    MANUAL = (1, "Manual Tuning", "Adjust gains manually based on observation")
    EMPIRICAL_AUTOTUNE = (2, "Empirical Autotune", "Automatic gain estimation via step response")

    def __init__(self, index: int, label: str, description: str):
        self.index = index
        self.label = label
        self.description = description

    @classmethod
    def from_index(cls, index: int) -> "CalibrationMode":
        """Get CalibrationMode by its index number."""
        for mode in cls:
            if mode.index == index:
                return mode
        raise ValueError(f"Invalid calibration mode index: {index}")

    @classmethod
    def choices(cls) -> list[str]:
        """Return list of valid index choices as strings."""
        return [str(mode.index) for mode in cls]

    @classmethod
    def table_rows(cls) -> list[tuple[str, str, str]]:
        """Return table rows: (index, label, description)."""
        return [(str(m.index), m.label, m.description) for m in cls]


class PidType(Enum):
    """Types of PID controllers."""

    LINEAR_POSE = (1, "Linear Pose", "Position control (distance)")
    ANGULAR_POSE = (2, "Angular Pose", "Position control (rotation)")
    LINEAR_SPEED = (3, "Linear Speed", "Velocity control (linear)")
    ANGULAR_SPEED = (4, "Angular Speed", "Velocity control (angular)")
    LINEAR_POSE_TEST = (5, "Linear Pose Test", "Linear movement with angular heading correction")
    # Lift PID types (for lift actuator calibration)
    LIFT_POSE = (6, "Lift Pose", "Lift position tracking error correction")
    LIFT_SPEED = (7, "Lift Speed", "Lift velocity control")

    def __init__(self, index: int, label: str, description: str):
        self.index = index
        self.label = label
        self.description = description

    @classmethod
    def from_index(cls, index: int) -> "PidType":
        """Get PidType by its index number."""
        for pid_type in cls:
            if pid_type.index == index:
                return pid_type
        raise ValueError(f"Invalid PID type index: {index}")

    @classmethod
    def choices(cls) -> list[str]:
        """Return list of valid index choices as strings."""
        return [str(pid_type.index) for pid_type in cls]

    @classmethod
    def table_rows(cls) -> list[tuple[str, str, str]]:
        """Return table rows: (index, label, description)."""
        return [(str(pt.index), pt.label, pt.description) for pt in cls]

    @property
    def controller(self) -> ControllerEnum | None:
        """Return the controller to use for this PID type.

        Returns None for lift PIDs since they don't require a controller switch
        (lift motors are controlled by the actuator system, not motion control).
        """
        controller_map: dict[PidType, ControllerEnum | None] = {
            PidType.LINEAR_POSE: ControllerEnum.LINEAR_POSE_TUNING,
            PidType.ANGULAR_POSE: ControllerEnum.ANGULAR_POSE_TUNING,
            PidType.LINEAR_SPEED: ControllerEnum.LINEAR_SPEED_TUNING,
            PidType.ANGULAR_SPEED: ControllerEnum.ANGULAR_SPEED_TUNING,
            PidType.LINEAR_POSE_TEST: ControllerEnum.LINEAR_POSE_TEST,
            # Lift PIDs don't use motion control controller switching
            PidType.LIFT_POSE: None,
            PidType.LIFT_SPEED: None,
        }
        return controller_map[self]

    @property
    def is_lift_pid(self) -> bool:
        """Return True if this is a lift PID type."""
        return self in (PidType.LIFT_POSE, PidType.LIFT_SPEED)


class TelemetryType(Enum):
    """
    Telemetry types for PID visualization.

    Each type has: (telemetry_key, label)
    """

    # Linear telemetry
    LINEAR_SPEED_ORDER = ("linear_speed_order", "Order")
    LINEAR_CURRENT_SPEED = ("linear_current_speed", "Current Speed")
    LINEAR_TRACKER_VELOCITY = ("linear_tracker_velocity", "Tracker")
    LINEAR_SPEED_COMMAND = ("linear_speed_command", "Command")

    # Angular telemetry
    ANGULAR_SPEED_ORDER = ("angular_speed_order", "Order")
    ANGULAR_CURRENT_SPEED = ("angular_current_speed", "Current Speed")
    ANGULAR_TRACKER_VELOCITY = ("angular_tracker_velocity", "Tracker")
    ANGULAR_SPEED_COMMAND = ("angular_speed_command", "Command")

    # Lift telemetry
    LIFT_SPEED_ORDER = ("speed_order", "Order")
    LIFT_CURRENT_SPEED = ("current_speed", "Current Speed")
    LIFT_TRACKER_VELOCITY = ("tracker_velocity", "Tracker")
    LIFT_SPEED_COMMAND = ("speed_command", "Command")

    def __init__(self, telemetry_key: str, label: str):
        self.telemetry_key = telemetry_key
        self.label = label

    @classmethod
    def for_pid_type(cls, pid_type: PidType) -> list["TelemetryType"]:
        """Return relevant telemetry types for a given PID type."""
        if pid_type in (PidType.LINEAR_POSE, PidType.LINEAR_SPEED, PidType.LINEAR_POSE_TEST):
            return [
                cls.LINEAR_SPEED_ORDER,
                cls.LINEAR_CURRENT_SPEED,
                cls.LINEAR_TRACKER_VELOCITY,
                cls.LINEAR_SPEED_COMMAND,
            ]
        elif pid_type in (PidType.ANGULAR_POSE, PidType.ANGULAR_SPEED):
            return [
                cls.ANGULAR_SPEED_ORDER,
                cls.ANGULAR_CURRENT_SPEED,
                cls.ANGULAR_TRACKER_VELOCITY,
                cls.ANGULAR_SPEED_COMMAND,
            ]
        else:
            # Lift PID types
            return [
                cls.LIFT_SPEED_ORDER,
                cls.LIFT_CURRENT_SPEED,
                cls.LIFT_TRACKER_VELOCITY,
                cls.LIFT_SPEED_COMMAND,
            ]


@dataclass
class PidGains:
    """PID gains (Kp, Ki, Kd) for a single controller."""

    kp: float = 0.0
    ki: float = 0.0
    kd: float = 0.0

    def copy(self) -> "PidGains":
        """Create a copy of the gains."""
        return PidGains(kp=self.kp, ki=self.ki, kd=self.kd)
