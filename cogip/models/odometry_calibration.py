"""
Odometry Calibration Models

Pydantic models for odometry calibration data.
"""

from pydantic import BaseModel


class CalibrationResult(BaseModel):
    """Result of a calibration computation."""

    wheels_distance: float
    right_wheel_radius: float
    left_wheel_radius: float


class CalibrationState(BaseModel):
    """
    State container for calibration intermediate values.

    Tracks alpha and beta coefficients computed during calibration phases.
    """

    alpha_l: float = 0.0
    alpha_r: float = 0.0
    beta: float = 0.0


class EncoderDeltas(BaseModel):
    """Encoder tick deltas captured during a motion sequence."""

    left: int
    right: int


class OdometryParameters(BaseModel):
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
