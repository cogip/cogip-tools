// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       circle_t class declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include <ostream>

namespace cogip {

namespace models {

/// Represents a circle in 2D space.
typedef struct {
    double x;       ///< X-coordinate of the circle center.
    double y;       ///< Y-coordinate of the circle center.
    double radius;  ///< Radius of the circle.
} circle_t;

/// Overloads the stream insertion operator for `circle_t`.
/// Prints the circle in a human-readable format.
/// @param os The output stream.
/// @param circle The circle to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const circle_t& circle) {
    os << "circle_t(x=" << circle.x << ", y=" << circle.y << ", radius=" << circle.radius << ")";
    return os;
}

} // namespace cogip_defs

} // namespace cogip

/// @}
