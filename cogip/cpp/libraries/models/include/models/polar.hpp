// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       polar_t class declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include <ostream>

namespace cogip {

namespace models {

/// Represents polar coordinates.
typedef struct {
    double distance;          ///< distance
    double angle;             ///< angle
} polar_t;

/// Overloads the stream insertion operator for `polar_t`.
/// Prints the polar in a human-readable format.
/// @param os The output stream.
/// @param polar The polar to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const polar_t& polar) {
    os << "polar_t(distance=" << polar.distance << ", angle=" << polar.angle << ")";
    return os;
}

} // namespace models

} // namespace cogip

/// @}
