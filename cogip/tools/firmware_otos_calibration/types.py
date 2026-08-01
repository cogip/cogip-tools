"""
OTOS Calibration Types

Enum and metadata for the two OTOS calibration phases.
"""

from enum import IntEnum, auto


class OtosCalibrationPhaseType(IntEnum):
    """Calibration phases for the OTOS sensor."""

    LINEAR_SCALAR = auto()
    ANGULAR_SCALAR = auto()

    @property
    def title(self) -> str:
        titles = {
            OtosCalibrationPhaseType.LINEAR_SCALAR: "LINEAR SCALAR CALIBRATION",
            OtosCalibrationPhaseType.ANGULAR_SCALAR: "ANGULAR SCALAR CALIBRATION",
        }
        return titles[self]

    @property
    def description(self) -> str:
        descriptions = {
            OtosCalibrationPhaseType.LINEAR_SCALAR: (
                "The robot will drive forward in a straight line. After it stops, measure the "
                "physically travelled distance with a tape and enter it. The OTOS linear_scalar "
                "is adjusted so that the commanded distance matches the physical distance."
            ),
            OtosCalibrationPhaseType.ANGULAR_SCALAR: (
                "The robot will rotate in place by a known number of full turns. After it "
                "stops, measure the physically rotated angle (e.g. using a marker and a "
                "reference line) and enter it in degrees. The OTOS angular_scalar is adjusted "
                "so that the commanded rotation matches the physical rotation."
            ),
        }
        return descriptions[self]

    @property
    def command_prompt(self) -> str:
        prompts = {
            OtosCalibrationPhaseType.LINEAR_SCALAR: "Commanded distance (mm)?",
            OtosCalibrationPhaseType.ANGULAR_SCALAR: "Number of full rotations?",
        }
        return prompts[self]

    @property
    def command_default(self) -> int:
        defaults = {
            OtosCalibrationPhaseType.LINEAR_SCALAR: 1000,
            OtosCalibrationPhaseType.ANGULAR_SCALAR: 5,
        }
        return defaults[self]

    @property
    def measurement_prompt(self) -> str:
        prompts = {
            OtosCalibrationPhaseType.LINEAR_SCALAR: "Measured physical distance (mm)?",
            OtosCalibrationPhaseType.ANGULAR_SCALAR: "Measured physical rotation (degrees)?",
        }
        return prompts[self]
