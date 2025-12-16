"""
Odometry Calibration Calculator.

Pure mathematical functions for computing calibration parameters.

Calibrates three parameters for differential drive odometry:
wheel distance, left wheel radius, and right wheel radius.

Calibration process:
    Phase 1 (Turn in Place): Spin N rotations to compute wheel distance from encoder arcs
    Phase 2 (Square Path): Drive squares to isolate linear motion and find wheel radius ratio (beta)
    Phase 3 (Straight Line): Drive known distance to solve for actual wheel radius using beta
"""

import math

from cogip.models import CalibrationResult, CalibrationState


def compute_alpha_coefficients(
    turns: int,
    lticks_delta: int,
    rticks_delta: int,
    encoder_ticks: float,
) -> tuple[float, float]:
    """
    Compute alpha coefficients from turn-in-place data.

    Alpha represents wheel rotations per robot rotation.

    Args:
        turns: Number of full rotations performed
        lticks_delta: Change in left encoder ticks
        rticks_delta: Change in right encoder ticks
        encoder_ticks: Encoder ticks per wheel revolution

    Returns:
        Tuple of (alpha_l, alpha_r)
    """
    alpha_l = lticks_delta / (encoder_ticks * turns)
    alpha_r = rticks_delta / (encoder_ticks * turns)
    return alpha_l, alpha_r


def compute_wheel_distance(
    alpha_l: float,
    alpha_r: float,
    left_wheel_radius: float,
    right_wheel_radius: float,
) -> float:
    """
    Compute wheel distance from alpha coefficients and wheel radii.

    Formula: axletrack = |alpha_l| * radius_l + |alpha_r| * radius_r

    During rotation in place, wheels turn in opposite directions, so alpha
    coefficients have opposite signs. We use absolute values to sum their
    contributions.

    Args:
        alpha_l: Left wheel rotations per robot rotation (may be negative)
        alpha_r: Right wheel rotations per robot rotation (may be negative)
        left_wheel_radius: Current left wheel radius estimate
        right_wheel_radius: Current right wheel radius estimate

    Returns:
        Computed wheel distance in mm
    """
    return abs(alpha_l) * left_wheel_radius + abs(alpha_r) * right_wheel_radius


def compute_wheel_distance_result(
    turns: int,
    lticks_delta: int,
    rticks_delta: int,
    encoder_ticks: float,
    left_wheel_radius: float,
    right_wheel_radius: float,
    left_polarity: float = 1.0,
    right_polarity: float = 1.0,
) -> tuple[CalibrationResult, CalibrationState]:
    """
    Phase 1: Compute wheel distance from turn-in-place data.

    Args:
        turns: Number of full rotations performed
        lticks_delta: Change in left encoder ticks (raw)
        rticks_delta: Change in right encoder ticks (raw)
        encoder_ticks: Encoder ticks per wheel revolution
        left_wheel_radius: Current left wheel radius
        right_wheel_radius: Current right wheel radius
        left_polarity: Left encoder polarity correction (+1 or -1)
        right_polarity: Right encoder polarity correction (+1 or -1)

    Returns:
        Tuple of (CalibrationResult, updated CalibrationState)
    """
    # Apply polarity correction
    lticks_delta = int(lticks_delta * left_polarity)
    rticks_delta = int(rticks_delta * right_polarity)

    alpha_l, alpha_r = compute_alpha_coefficients(turns, lticks_delta, rticks_delta, encoder_ticks)
    new_wheels_distance = compute_wheel_distance(alpha_l, alpha_r, left_wheel_radius, right_wheel_radius)

    result = CalibrationResult(
        wheels_distance=new_wheels_distance,
        right_wheel_radius=right_wheel_radius,
        left_wheel_radius=left_wheel_radius,
    )

    state = CalibrationState(
        alpha_l=alpha_l,
        alpha_r=alpha_r,
        beta=0.0,
    )

    return result, state


def compute_beta_coefficient(
    lticks_linear: float,
    rticks_linear: float,
) -> float | None:
    """
    Compute beta coefficient (radius ratio) from linear encoder components.

    For straight-line motion, both wheels travel the same distance D:
        D = 2π * radius_l * (lticks / encoder_ticks)
        D = 2π * radius_r * (rticks / encoder_ticks)

    Therefore: radius_r / radius_l = lticks / rticks

    Beta = radius_r / radius_l = lticks_linear / rticks_linear

    Args:
        lticks_linear: Linear component of left encoder ticks
        rticks_linear: Linear component of right encoder ticks

    Returns:
        Beta coefficient (radius_r / radius_l), or None if rticks_linear is too small
    """
    if abs(rticks_linear) < 1:
        return None
    return lticks_linear / rticks_linear


def compute_right_wheel_radius_result(
    squares: int,
    lticks_delta: int,
    rticks_delta: int,
    state: CalibrationState,
    encoder_ticks: float,
    left_wheel_radius: float,
    left_polarity: float = 1.0,
    right_polarity: float = 1.0,
) -> tuple[CalibrationResult, CalibrationState] | None:
    """
    Phase 2: Compute right wheel radius from square trajectory data.

    Args:
        squares: Number of square paths performed
        lticks_delta: Change in left encoder ticks (raw)
        rticks_delta: Change in right encoder ticks (raw)
        state: Current calibration state with alpha coefficients
        encoder_ticks: Encoder ticks per wheel revolution
        left_wheel_radius: Current left wheel radius
        left_polarity: Left encoder polarity correction (+1 or -1)
        right_polarity: Right encoder polarity correction (+1 or -1)

    Returns:
        Tuple of (CalibrationResult, updated CalibrationState), or None if computation fails
    """
    # Apply polarity correction
    lticks_delta = int(lticks_delta * left_polarity)
    rticks_delta = int(rticks_delta * right_polarity)

    # Subtract rotation component to get linear component
    lticks_linear = lticks_delta - (state.alpha_l * encoder_ticks * squares)
    rticks_linear = rticks_delta - (state.alpha_r * encoder_ticks * squares)

    beta = compute_beta_coefficient(lticks_linear, rticks_linear)
    if beta is None:
        return None

    new_right_wheel_radius = beta * left_wheel_radius
    new_wheels_distance = compute_wheel_distance(
        state.alpha_l, state.alpha_r, left_wheel_radius, new_right_wheel_radius
    )

    result = CalibrationResult(
        wheels_distance=new_wheels_distance,
        right_wheel_radius=new_right_wheel_radius,
        left_wheel_radius=left_wheel_radius,
    )

    updated_state = CalibrationState(
        alpha_l=state.alpha_l,
        alpha_r=state.alpha_r,
        beta=beta,
    )

    return result, updated_state


def compute_left_wheel_radius_result(
    distance_mm: int,
    lticks_delta: int,
    rticks_delta: int,
    state: CalibrationState,
    encoder_ticks: float,
    left_polarity: float = 1.0,
    right_polarity: float = 1.0,
) -> tuple[CalibrationResult, CalibrationState] | None:
    """
    Phase 3: Compute left wheel radius from straight line data.

    For straight-line motion of distance D:
        D = 2π * radius_l * (lticks / encoder_ticks)
        D = 2π * radius_r * (rticks / encoder_ticks)

    With radius_r = beta * radius_l, summing both equations:
        2D = 2π * radius_l * (lticks + beta * rticks) / encoder_ticks

    Formula: radius_l = D * encoder_ticks / (π * (lticks + beta * rticks))

    Args:
        distance_mm: Distance traveled in mm
        lticks_delta: Change in left encoder ticks (raw)
        rticks_delta: Change in right encoder ticks (raw)
        state: Current calibration state with alpha and beta coefficients
        encoder_ticks: Encoder ticks per wheel revolution
        left_polarity: Left encoder polarity correction (+1 or -1)
        right_polarity: Right encoder polarity correction (+1 or -1)

    Returns:
        Tuple of (CalibrationResult, CalibrationState), or None if computation fails
    """
    # Apply polarity correction
    lticks_delta = int(lticks_delta * left_polarity)
    rticks_delta = int(rticks_delta * right_polarity)

    denominator = math.pi * (lticks_delta + state.beta * rticks_delta)

    if abs(denominator) < 1:
        return None

    new_left_wheel_radius = (distance_mm * encoder_ticks) / denominator
    new_right_wheel_radius = state.beta * new_left_wheel_radius
    new_wheels_distance = compute_wheel_distance(
        state.alpha_l, state.alpha_r, new_left_wheel_radius, new_right_wheel_radius
    )

    result = CalibrationResult(
        wheels_distance=new_wheels_distance,
        right_wheel_radius=new_right_wheel_radius,
        left_wheel_radius=new_left_wheel_radius,
    )

    # State unchanged in phase 3
    return result, state
