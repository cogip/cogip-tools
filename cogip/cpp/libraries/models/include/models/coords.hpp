// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       coords_t declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include <ostream>

namespace cogip {

namespace models {

/// Represents absolute coordinates along X and Y axis.
typedef struct {
    double x;      ///< x-position.
    double y;      ///< Y-coordinate of the pose.
} coords_t;

/// Overloads the stream insertion operator for `coords_t`.
/// Prints the coords in a human-readable format.
/// @param os The output stream.
/// @param coords The coords to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const coords_t& coords) {
    os << "coords_t(x=" << coords.x << ", y=" << coords.y << ")";
    return os;
}

} // namespace models

} // namespace cogip

/// @}
