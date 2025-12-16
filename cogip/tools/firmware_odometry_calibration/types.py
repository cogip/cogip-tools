"""
Odometry Calibration Models

Data types, enums, and dataclasses for the calibration tool.
"""

import math
from dataclasses import dataclass
from enum import Enum, auto

from cogip.models import Pose


class CalibrationPhaseType(Enum):
    """Calibration phase types."""

    WHEEL_DISTANCE = auto()
    RIGHT_WHEEL_RADIUS = auto()
    LEFT_WHEEL_RADIUS = auto()

    @property
    def title(self) -> str:
        """Phase title for display."""
        titles = {
            CalibrationPhaseType.WHEEL_DISTANCE: "WHEEL DISTANCE CALIBRATION",
            CalibrationPhaseType.RIGHT_WHEEL_RADIUS: "RIGHT WHEEL RADIUS CALIBRATION",
            CalibrationPhaseType.LEFT_WHEEL_RADIUS: "LEFT WHEEL RADIUS CALIBRATION",
        }
        return titles[self]

    @property
    def description(self) -> str:
        """Phase description for display."""
        descriptions = {
            CalibrationPhaseType.WHEEL_DISTANCE: "The robot will rotate in place to calibrate the wheel distance",
            CalibrationPhaseType.RIGHT_WHEEL_RADIUS: (
                "The robot will perform square trajectories to calibrate the right wheel radius"
            ),
            CalibrationPhaseType.LEFT_WHEEL_RADIUS: (
                "The robot will travel a straight line to calibrate the left wheel radius"
            ),
        }
        return descriptions[self]

    @property
    def input_prompt(self) -> str:
        """Input prompt for this phase."""
        prompts = {
            CalibrationPhaseType.WHEEL_DISTANCE: "How many full rotations?",
            CalibrationPhaseType.RIGHT_WHEEL_RADIUS: "How many squares?",
            CalibrationPhaseType.LEFT_WHEEL_RADIUS: "What distance in mm?",
        }
        return prompts[self]

    @property
    def default_value(self) -> int:
        """Default value for this phase input."""
        defaults = {
            CalibrationPhaseType.WHEEL_DISTANCE: 10,
            CalibrationPhaseType.RIGHT_WHEEL_RADIUS: 5,
            CalibrationPhaseType.LEFT_WHEEL_RADIUS: 2000,
        }
        return defaults[self]

    @property
    def error_message(self) -> str | None:
        """Error message specific to this phase computation."""
        errors = {
            CalibrationPhaseType.WHEEL_DISTANCE: None,
            CalibrationPhaseType.RIGHT_WHEEL_RADIUS: (
                "Right encoder linear component too small. Check encoder connection."
            ),
            CalibrationPhaseType.LEFT_WHEEL_RADIUS: "Denominator too small. Check encoder counts.",
        }
        return errors[self]


@dataclass
class CalibrationResult:
    """Result of a calibration computation."""

    wheels_distance: float
    right_wheel_radius: float
    left_wheel_radius: float


@dataclass
class CalibrationState:
    """
    State container for calibration intermediate values.

    Tracks alpha and beta coefficients computed during calibration phases.
    """

    alpha_l: float = 0.0
    alpha_r: float = 0.0
    beta: float = 0.0


@dataclass
class EncoderDeltas:
    """Encoder tick deltas captured during a motion sequence."""

    left: int
    right: int


@dataclass
class OdometryParameters:
    """
    Container for odometry parameters.

    Holds all parameters needed for odometry calibration.
    """

    wheels_distance: float = 0.0
    right_wheel_radius: float = 0.0
    left_wheel_radius: float = 0.0
    left_polarity: float = 0.0
    right_polarity: float = 0.0
    encoder_ticks: float = 0.0

    def copy(self) -> "OdometryParameters":
        """Create a copy of the parameters."""
        return OdometryParameters(
            wheels_distance=self.wheels_distance,
            right_wheel_radius=self.right_wheel_radius,
            left_wheel_radius=self.left_wheel_radius,
            left_polarity=self.left_polarity,
            right_polarity=self.right_polarity,
            encoder_ticks=self.encoder_ticks,
        )


# Predefined square path for calibration phase 2 (500mm sides, counter-clockwise)
SQUARE_PATH_CCW: tuple[Pose, ...] = (
    Pose(x=500, y=0, O=math.pi / 2),
    Pose(x=500, y=500, O=math.pi),
    Pose(x=0, y=500, O=-math.pi / 2),
    Pose(x=0, y=0, O=0),
)
