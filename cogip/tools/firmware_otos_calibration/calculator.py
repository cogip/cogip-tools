"""
OTOS Calibration Calculator.

Pure math functions that derive a new OTOS calibration scalar from the
commanded motion and the physically measured result.

Both scalars correct a systematic bias between the OTOS-reported distance /
rotation and the actual one. The control loop stops when OTOS reports it has
reached the commanded value, so:

    physical = OTOS_reported / current_scalar
    new_scalar = current_scalar * (measured / commanded)

Each function returns the clamped scalar together with a boolean telling the
caller whether clamping actually kicked in (a sign that the sensor is more
off than OTOS can compensate and the mechanical setup needs a look).
"""

from cogip.models.otos_calibration import OTOS_SCALAR_MAX, OTOS_SCALAR_MIN


def _clamp(value: float) -> tuple[float, bool]:
    clamped = max(OTOS_SCALAR_MIN, min(OTOS_SCALAR_MAX, value))
    return clamped, clamped != value


def compute_linear_scalar(
    current_scalar: float,
    commanded_mm: float,
    measured_mm: float,
) -> tuple[float, bool]:
    """
    Compute a new linear_scalar so that next time OTOS reports commanded_mm
    the robot actually travels commanded_mm.

    Args:
        current_scalar: linear_scalar currently programmed in the OTOS chip.
        commanded_mm: distance sent to the motion control (mm).
        measured_mm: distance the operator measured after the motion (mm).

    Returns:
        (new_scalar, was_clamped). The second value is True if the result
        had to be clamped to the OTOS allowed range [0.872, 1.127].
    """
    if commanded_mm == 0.0:
        raise ValueError("commanded_mm must be non-zero")
    raw = current_scalar * (measured_mm / commanded_mm)
    return _clamp(raw)


def compute_angular_scalar(
    current_scalar: float,
    commanded_deg: float,
    measured_deg: float,
) -> tuple[float, bool]:
    """
    Compute a new angular_scalar so that next time OTOS reports commanded_deg
    the robot actually rotates commanded_deg.

    Args:
        current_scalar: angular_scalar currently programmed in the OTOS chip.
        commanded_deg: rotation sent to the motion control (degrees).
        measured_deg: rotation the operator measured after the motion (degrees).

    Returns:
        (new_scalar, was_clamped). The second value is True if the result
        had to be clamped to the OTOS allowed range [0.872, 1.127].
    """
    if commanded_deg == 0.0:
        raise ValueError("commanded_deg must be non-zero")
    raw = current_scalar * (measured_deg / commanded_deg)
    return _clamp(raw)
