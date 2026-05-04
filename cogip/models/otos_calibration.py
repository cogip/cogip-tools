"""
OTOS Calibration Models

Pydantic models for the SparkFun OTOS sensor calibration scalars.
"""

from pydantic import BaseModel

# Range accepted by the OTOS chip for both calibration scalars.
OTOS_SCALAR_MIN = 0.872
OTOS_SCALAR_MAX = 1.127


class OTOSParameters(BaseModel):
    """Current OTOS calibration scalars pulled from firmware."""

    linear_scalar: float
    angular_scalar: float


class OTOSCalibrationResult(BaseModel):
    """Computed scalars after a single calibration phase."""

    linear_scalar: float
    angular_scalar: float
