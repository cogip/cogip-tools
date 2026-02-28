"""
PID Calibration Models

Data types, enums, and dataclasses for the PID calibration tool.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from cogip.tools.copilot.controller import ControllerEnum

# Default calibration test values
DEFAULT_LINEAR_DISTANCE_MM = 500
DEFAULT_ANGULAR_DISTANCE_DEG = 180
DEFAULT_LINEAR_SPEED_MM_S = 200
DEFAULT_ANGULAR_SPEED_DEG_S = 90
DEFAULT_SPEED_DURATION_MS = 2000


class MotionKind(Enum):
    """Determines which motion strategy a PID type uses."""

    LINEAR = "linear"
    ANGULAR = "angular"


class CommandKind(Enum):
    """Determines which command protocol a PID type uses."""

    POSE = "pose"
    SPEED = "speed"

    @property
    def layout_path(self) -> Path:
        """Path to the graph layout YAML file for this command kind."""
        return Path(__file__).parent / f"pid_graph_{self.value}_layout.yaml"


class PidType(Enum):
    """Types of PID controllers.

    Each member is the single source of truth for:
    - label: human-readable name (also used as telemetry graph plot title)
    - description: longer explanation
    - param_names: (kp_name, ki_name, kd_name) for firmware parameters
    - controller: ControllerEnum to activate
    - command_kind: whether to use pose or speed commands
    - motion_kind: which MotionKind to use for calibration
    - default_distance: default test distance in mm or deg (pose types only)
    - default_speed: default test speed in mm/s or deg/s (speed types only)
    - default_duration_ms: default speed command duration in ms (speed types only)

    The index is auto-computed from declaration order (1-based).
    """

    LINEAR_POSE = dict(
        label="Linear Pose",
        description="Position control (distance)",
        param_names=("linear_pose_pid_kp", "linear_pose_pid_ki", "linear_pose_pid_kd"),
        controller=ControllerEnum.LINEAR_POSE_TUNING,
        command_kind=CommandKind.POSE,
        motion_kind=MotionKind.LINEAR,
        default_distance=DEFAULT_LINEAR_DISTANCE_MM,
    )
    ANGULAR_POSE = dict(
        label="Angular Pose",
        description="Position control (rotation)",
        param_names=("angular_pose_pid_kp", "angular_pose_pid_ki", "angular_pose_pid_kd"),
        controller=ControllerEnum.ANGULAR_POSE_TUNING,
        command_kind=CommandKind.POSE,
        motion_kind=MotionKind.ANGULAR,
        default_distance=DEFAULT_ANGULAR_DISTANCE_DEG,
    )
    LINEAR_SPEED = dict(
        label="Linear Speed",
        description="Velocity control (linear)",
        param_names=("linear_speed_pid_kp", "linear_speed_pid_ki", "linear_speed_pid_kd"),
        controller=ControllerEnum.LINEAR_SPEED_TUNING,
        command_kind=CommandKind.SPEED,
        motion_kind=MotionKind.LINEAR,
        default_speed=DEFAULT_LINEAR_SPEED_MM_S,
        default_duration_ms=DEFAULT_SPEED_DURATION_MS,
    )
    ANGULAR_SPEED = dict(
        label="Angular Speed",
        description="Velocity control (angular)",
        param_names=("angular_speed_pid_kp", "angular_speed_pid_ki", "angular_speed_pid_kd"),
        controller=ControllerEnum.ANGULAR_SPEED_TUNING,
        command_kind=CommandKind.SPEED,
        motion_kind=MotionKind.ANGULAR,
        default_speed=DEFAULT_ANGULAR_SPEED_DEG_S,
        default_duration_ms=DEFAULT_SPEED_DURATION_MS,
    )

    def __init__(self, config: dict):
        self.index = len(self.__class__.__members__) + 1
        self.label = config["label"]
        self.description = config["description"]
        self.param_names = config["param_names"]
        self.controller = config["controller"]
        self.command_kind = config["command_kind"]
        self.motion_kind = config["motion_kind"]
        self.default_distance = config.get("default_distance", 0)
        self.default_speed = config.get("default_speed", 0)
        self.default_duration_ms = config.get("default_duration_ms", 0)

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
