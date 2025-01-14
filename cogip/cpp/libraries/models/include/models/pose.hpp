// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       pose_t class declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include <ostream>

namespace cogip {

namespace models {

/// Represents a pose in 2D space with an orientation.
typedef struct {
    double x;      ///< X-coordinate of the pose.
    double y;      ///< Y-coordinate of the pose.
    double angle;  ///< Orientation angle of the pose in degrees.
} pose_t;

/// Overloads the stream insertion operator for `pose_t`.
/// Prints the pose in a human-readable format.
/// @param os The output stream.
/// @param pose The pose to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const pose_t& pose) {
    os << "pose_t(x=" << pose.x << ", y=" << pose.y << ", angle=" << pose.angle << ")";
    return os;
}

} // namespace cogip_defs

} // namespace cogip

/// @}
