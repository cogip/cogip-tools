"""
PID Calibration Models

Data types, enums, and dataclasses for the PID calibration tool.
"""

from dataclasses import dataclass
from enum import Enum

from cogip.tools.copilot.controller import ControllerEnum


class MovementKind(Enum):
    """Determines which movement strategy a PID type uses."""

    LINEAR = "linear"
    ANGULAR = "angular"


class PidType(Enum):
    """Types of PID controllers.

    Each member is the single source of truth for:
    - index: selection menu index
    - label: human-readable name
    - description: longer explanation
    - param_names: (kp_name, ki_name, kd_name) for firmware parameters
    - controller: ControllerEnum to activate
    - movement_kind: which MovementKind to use for calibration
    - default_distance: default test distance (mm or degrees depending on kind)
    - graph_plot: title of the telemetry plot to display (None to skip)
    """

    LINEAR_POSE = (
        1,
        "Linear Pose",
        "Position control (distance)",
        ("linear_pose_pid_kp", "linear_pose_pid_ki", "linear_pose_pid_kd"),
        ControllerEnum.LINEAR_POSE_TUNING,
        MovementKind.LINEAR,
        500,
        "Linear Speed",
    )
    ANGULAR_POSE = (
        2,
        "Angular Pose",
        "Position control (rotation)",
        ("angular_pose_pid_kp", "angular_pose_pid_ki", "angular_pose_pid_kd"),
        ControllerEnum.ANGULAR_POSE_TUNING,
        MovementKind.ANGULAR,
        180,
        "Angular Speed",
    )
    LINEAR_SPEED = (
        3,
        "Linear Speed",
        "Velocity control (linear)",
        ("linear_speed_pid_kp", "linear_speed_pid_ki", "linear_speed_pid_kd"),
        ControllerEnum.LINEAR_SPEED_TUNING,
        MovementKind.LINEAR,
        500,
        "Linear Speed",
    )
    ANGULAR_SPEED = (
        4,
        "Angular Speed",
        "Velocity control (angular)",
        ("angular_speed_pid_kp", "angular_speed_pid_ki", "angular_speed_pid_kd"),
        ControllerEnum.ANGULAR_SPEED_TUNING,
        MovementKind.ANGULAR,
        180,
        "Angular Speed",
    )

    def __init__(
        self,
        index: int,
        label: str,
        description: str,
        param_names: tuple[str, str, str],
        controller: ControllerEnum,
        movement_kind: MovementKind,
        default_distance: float,
        graph_plot: str | None,
    ):
        self.index = index
        self.label = label
        self.description = description
        self.param_names = param_names
        self._controller = controller
        self.movement_kind = movement_kind
        self.default_distance = default_distance
        self.graph_plot = graph_plot

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


@dataclass
class PidGains:
    """PID gains (Kp, Ki, Kd) for a single controller."""

    kp: float = 0.0
    ki: float = 0.0
    kd: float = 0.0

    def copy(self) -> "PidGains":
        """Create a copy of the gains."""
        return PidGains(kp=self.kp, ki=self.ki, kd=self.kd)
