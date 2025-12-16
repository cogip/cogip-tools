"""
Odometry Calibration Types

Enums and constants for the calibration tool.
"""

import math
from enum import IntEnum, auto

from cogip.models import Pose


class CalibrationPhaseType(IntEnum):
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


# Predefined square path for calibration phase 2 (500mm sides, counter-clockwise)
SQUARE_PATH_CCW: tuple[Pose, ...] = (
    Pose(x=500, y=0, O=math.pi / 2),
    Pose(x=500, y=500, O=math.pi),
    Pose(x=0, y=500, O=-math.pi / 2),
    Pose(x=0, y=0, O=0),
)
