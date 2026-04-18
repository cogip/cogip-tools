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

/// Motion direction mode for path navigation.
enum class MotionDirection : std::uint8_t {
    bidirectional = 0,  ///< Robot can move forward or backward (choose optimal)
    forward_only = 1,   ///< Force forward motion only
    backward_only = 2   ///< Force backward motion only
};

/// Represents a pose in 2D space with an orientation.
typedef struct {
    double x;      ///< X-coordinate of the pose.
    double y;      ///< Y-coordinate of the pose.
    double angle;  ///< Orientation angle of the pose in degrees.
    std::uint8_t max_speed_linear; ///< Maximum linear speed for the pose (in percent of the robot max speed).
    std::uint8_t max_speed_angular; ///< Maximum linear speed for the pose (in percent of the robot max speed).
    MotionDirection motion_direction; ///< Motion direction mode (bidirectional, forward_only, or backward_only).
    bool bypass_anti_blocking; ///< True if the pose bypasses anti-blocking, false otherwise.
    bool bypass_final_orientation; ///< True if the pose bypasses final orientation, false otherwise.
    std::uint32_t timeout_ms; ///< Timeout in milliseconds for the pose to be reached.
    bool is_intermediate; ///< True if the pose is an intermediate pose, false if it is a final pose.
    double stop_before_distance; ///< Distance to stop before reaching the pose.
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
       << "max_speed_linear=" << static_cast<int>(data.max_speed_linear) << ", "
       << "max_speed_angular=" << static_cast<int>(data.max_speed_angular) << ", "
       << "motion_direction=" << static_cast<int>(data.motion_direction) << ", "
       << "bypass_anti_blocking=" << data.bypass_anti_blocking << ", "
       << "bypass_final_orientation=" << data.bypass_final_orientation << ", "
       << "timeout_ms=" << data.timeout_ms << ", "
       << "is_intermediate=" << data.is_intermediate << ", "
       << "stop_before_distance=" << data.stop_before_distance << ", "
       << ")";
    return os;
}

} // namespace models

} // namespace cogip

/// @}
