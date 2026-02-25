"""
PID Calibration Models

Data types, enums, and dataclasses for the PID calibration tool.
"""

from dataclasses import dataclass
from enum import Enum

from cogip.tools.copilot.controller import ControllerEnum


class PidType(Enum):
    """Types of PID controllers."""

    LINEAR_POSE = (1, "Linear Pose", "Position control (distance)")
    ANGULAR_POSE = (2, "Angular Pose", "Position control (rotation)")
    LINEAR_SPEED = (3, "Linear Speed", "Velocity control (linear)")
    ANGULAR_SPEED = (4, "Angular Speed", "Velocity control (angular)")
    LINEAR_POSE_TEST = (5, "Linear Pose Test", "Linear movement with angular heading correction")

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
    def controller(self) -> ControllerEnum:
        """Return the controller to use for this PID type."""
        controller_map = {
            PidType.LINEAR_POSE: ControllerEnum.LINEAR_POSE_TUNING,
            PidType.ANGULAR_POSE: ControllerEnum.ANGULAR_POSE_TUNING,
            PidType.LINEAR_SPEED: ControllerEnum.LINEAR_SPEED_TUNING,
            PidType.ANGULAR_SPEED: ControllerEnum.ANGULAR_SPEED_TUNING,
            PidType.LINEAR_POSE_TEST: ControllerEnum.LINEAR_POSE_TEST,
        }
        return controller_map[self]


@dataclass
class PidGains:
    """PID gains (Kp, Ki, Kd) for a single controller."""

    kp: float = 0.0
    ki: float = 0.0
    kd: float = 0.0

    def copy(self) -> "PidGains":
        """Create a copy of the gains."""
        return PidGains(kp=self.kp, ki=self.ki, kd=self.kd)
