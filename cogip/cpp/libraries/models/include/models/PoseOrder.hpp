// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       PoseOrder class declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

// System includes
#include <cmath>

// Project includes
#include "models/pose_order.hpp"
#include "models/Pose.hpp"

namespace cogip {

namespace models {

/// Pose order used by the avoidance process and the motion control.
class PoseOrder {
public:
    /// Constructor.
    PoseOrder(
        pose_order_t *data       ///< [in] Pointer to an existing data structure
                                 ///<      If nullptr, will allocate one internally
    );

    /// Constructor with initial values.
    PoseOrder(
        double x=0.0,                         ///< [in] X coordinate
        double y=0.0,                         ///< [in] Y coordinate
        double angle=0.0,                     ///< [in] orientation
        std::uint8_t max_speed_linear=66,     ///< [in] Maximum linear speed for the pose (in percent of the robot max speed).
        std::uint8_t max_speed_angular=66,    ///< [in] Maximum linear speed for the pose (in percent of the robot max speed).
        bool allow_reverse=true,              ///< [in] True if the pose allows reverse movement, false otherwise.
        bool bypass_anti_blocking=false,      ///< [in] True if the pose bypasses anti-blocking, false otherwise.
        bool bypass_final_orientation=false,  ///< [in] True if the pose bypasses final orientation, false otherwise.
        std::uint32_t timeout_ms=0,           ///< [in] Timeout in milliseconds for the pose to be reached.
        bool is_intermediate=false,           ///< [in] True if the pose is an intermediate pose, false if it is a final pose.
        pose_order_t *data=nullptr            ///< [in] Pointer to an existing data structure
                                              ///<      If nullptr, will allocate one internally
    );

    /// Copy constructor
    PoseOrder(
        const PoseOrder& other,       ///< [in] The PoseOrder to copy
        bool deep_copy=false          ///< [in] If true, will perform a deep copy of the data
    );

    /// Assignment operator
    PoseOrder& operator=(
        const PoseOrder& other        ///< [in] The PoseOrder to copy
    );


    /// Destructor.
    ~PoseOrder();

    double x() const { return data_->x; }
    void set_x(double x) { data_->x = x; }

    double y() const { return data_->y; }
    void set_y(double y) { data_->y = y; }

    /// Return orientation.
    double angle(void) const { return data_->angle; };

    /// Set orientation.
    void set_angle(
        double angle              ///< [in] new 0-orientation
    ) { data_->angle = angle; };

    /// Return maximum linear speed for the pose (in percent of the robot max speed).
    std::uint8_t max_speed_linear(void) const { return data_->max_speed_linear; }

    /// Set maximum linear speed for the pose (in percent of the robot max speed).
    void set_max_speed_linear(
        std::uint8_t max_speed_linear  ///< [in] new maximum linear speed for the pose (in percent of the robot max speed)
    ) { data_->max_speed_linear = max_speed_linear; }

    /// Return maximum angular speed for the pose (in percent of the robot max speed).
    std::uint8_t max_speed_angular(void) const { return data_->max_speed_angular; }

    /// Set maximum angular speed for the pose (in percent of the robot max speed).
    void set_max_speed_angular(
        std::uint8_t max_speed_angular  ///< [in] new maximum angular speed for the pose (in percent of the robot max speed)
    ) { data_->max_speed_angular = max_speed_angular; }

    /// Return true if the pose allows reverse movement, false otherwise.
    bool allow_reverse(void) const { return data_->allow_reverse; }

    /// Set whether the pose allows reverse movement.
    void set_allow_reverse(
        bool allow_reverse  ///< [in] true if the pose allows reverse movement, false otherwise
    ) { data_->allow_reverse = allow_reverse; }

    /// Return true if the pose bypasses anti-blocking, false otherwise.
    bool bypass_anti_blocking(void) const { return data_->bypass_anti_blocking; }

    /// Set whether the pose bypasses anti-blocking.
    void set_bypass_anti_blocking(
        bool bypass_anti_blocking  ///< [in] true if the pose bypasses anti-blocking, false otherwise
    ) { data_->bypass_anti_blocking = bypass_anti_blocking; }

    /// Return true if the pose bypasses final orientation, false otherwise.
    bool bypass_final_orientation(void) const { return data_->bypass_final_orientation; }

    /// Set whether the pose bypasses final orientation.
    void set_bypass_final_orientation(
        bool bypass_final_orientation  ///< [in] true if the pose bypasses final orientation, false otherwise
    ) { data_->bypass_final_orientation = bypass_final_orientation; }

    /// Return timeout in milliseconds for the pose to be reached.
    std::uint32_t timeout_ms(void) const { return data_->timeout_ms; }

    /// Set timeout in milliseconds for the pose to be reached.
    void set_timeout_ms(
        std::uint32_t timeout_ms  ///< [in] new timeout in milliseconds for the pose to be reached
    ) { data_->timeout_ms = timeout_ms; }

    /// Return true if the pose is an intermediate pose, false if it is a final pose.
    bool is_intermediate(void) const { return data_->is_intermediate; }

    /// Set whether the pose is an intermediate pose.
    void set_is_intermediate(
        bool is_intermediate  ///< [in] true if the pose is an intermediate pose, false if it is a final pose
    ) { data_->is_intermediate = is_intermediate; }

protected:
    void initMemory();

    pose_order_t* data_;    ///< pointer to internal data structure
    bool external_data_;    ///< Flag to indicate if memory is externally managed
};

/// Overloads the stream insertion operator for `PoseOrder`.
/// Prints the pose order in a human-readable format.
/// @param os The output stream.
/// @param data The pose order to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, PoseOrder data) {
    os << "PoseOrder("
       << "x=" << data.x() << ", "
       << "y=" << data.y() << ", "
       << "angle=" << data.angle() << ", "
       << "max_speed_linear=" << data.max_speed_linear() << ", "
       << "max_speed_angular=" << data.max_speed_angular() << ", "
       << "allow_reverse=" << data.allow_reverse() << ", "
       << "bypass_anti_blocking=" << data.bypass_anti_blocking() << ", "
       << "bypass_final_orientation=" << data.bypass_final_orientation() << ", "
       << "timeout_ms=" << data.timeout_ms() << ", "
       << "is_intermediate=" << data.is_intermediate()
       << ")";
    return os;
}

} // namespace models

} // namespace cogip

/// @}
