// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       pose_order_t class declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include <cstdint>
#include <ostream>

namespace cogip {

namespace models {

/// Represents a pose in 2D space with an orientation.
typedef struct {
    double x;      ///< X-coordinate of the pose.
    double y;      ///< Y-coordinate of the pose.
    double angle;  ///< Orientation angle of the pose in degrees.
    std::uint8_t max_speed_linear; ///< Maximum linear speed for the pose (in percent of the robot max speed).
    std::uint8_t max_speed_angular; ///< Maximum linear speed for the pose (in percent of the robot max speed).
    bool allow_reverse; ///< True if the pose allows reverse movement, false otherwise.
    bool bypass_anti_blocking; ///< True if the pose bypasses anti-blocking, false otherwise.
    bool bypass_final_orientation; ///< True if the pose bypasses final orientation, false otherwise.
    std::uint32_t timeout_ms; ///< Timeout in milliseconds for the pose to be reached.
    bool is_intermediate; ///< True if the pose is an intermediate pose, false if it is a final pose.
} pose_order_t;

/// Overloads the stream insertion operator for `pose_order_t`.
/// Prints the pose in a human-readable format.
/// @param os The output stream.
/// @param data The data to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const pose_order_t& data) {
    os << "pose_order_t("
       << "x=" << data.x << ", "
       << "y=" << data.y << ", "
       << "angle=" << data.angle << ", "
       << "max_speed_linear=" << data.max_speed_linear << ", "
       << "max_speed_angular=" << data.max_speed_angular << ", "
       << "allow_reverse=" << data.allow_reverse << ", "
       << "bypass_anti_blocking=" << data.bypass_anti_blocking << ", "
       << "bypass_final_orientation=" << data.bypass_final_orientation << ", "
       << "timeout_ms=" << data.timeout_ms << ", "
       << "is_intermediate=" << data.is_intermediate << ", "
       << ")";
    return os;
}

} // namespace models

} // namespace cogip

/// @}
