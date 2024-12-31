// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#pragma once

#include <cmath>

#ifndef M_PI
#define M_PI   3.14159265358979323846  /* pi */
#endif

#define square(__x) (__x * __x)

#define RAD2DEG(a) ((a * 180.0) / M_PI)
#define DEG2RAD(a) ((a * M_PI) / 180.0)

namespace cogip {

namespace utils {

inline double limit_angle_rad(double O)
{
    // TODO: avoid risk of blocking loop
    while (O > M_PI) {
        O -= 2.0 * M_PI;
    }

    while (O < -M_PI) {
        O += 2.0 * M_PI;
    }

    return O;
}

inline double limit_angle_deg(double O)
{
    while (O > 180) {
        O -= 360;
    }

    while (O < -180) {
        O += 360;
    }

    return O;
}

/// @brief Compare two floating-point numbers (double) with a specified tolerance.
///
/// This function checks if the absolute difference between two doubles is less than a given tolerance (epsilon),
/// which helps to address the imprecision of floating-point calculations.
///
/// @param[in]   a       The first floating-point number to compare.
/// @param[in]   b       The second floating-point number to compare.
/// @param[in]   epsilon The tolerance used for comparison (default value: 1e-3).
/// @return true         If the absolute difference between a and b is less than epsilon.
/// @return false        Otherwise.
inline bool are_doubles_equal(double a, double b, double epsilon = 1e-3) {
    return std::fabs(a - b) < epsilon;
};

/// @brief Calculate the Euclidean distance between two coordinates.
///
/// This function computes the straight-line distance between two points
/// in a 2D space, represented by the Coords class.
///
/// @param[in]   x1   The first point X-coordinate.
/// @param[in]   y1   The first point Y-coordinate.
/// @param[in]   x2   The second point X-coordinate.
/// @param[in]   y2   The second point Y-coordinate.
/// @return double   The Euclidean distance between the two points.
inline double calculate_distance(double x1, double y1, double x2, double y2) {
    // Compute the weight (Euclidean distance between two points)
    return std::hypot(
        x2 - x1,
        y2 - y1
    );
};

} // namespace utils

} // namespace cogip
