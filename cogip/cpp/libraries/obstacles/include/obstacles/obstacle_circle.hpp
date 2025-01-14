// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_obstacles
/// @file        obstacle_circle.hpp
/// @brief       Declaration of the obstacle_circle struct, representing a circular obstacle.
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "models/coords_list.hpp"
#include "models/pose.hpp"

#include <cstdint>

namespace cogip {

namespace obstacles {

typedef struct {
    uint32_t id;                         ///< Optional identifier.
    models::pose_t center;               ///< Obstacle center.
    double radius;                       ///< Obstacle circumscribed circle radius.
    double bounding_box_margin;          ///< Margin for the bounding box.
    uint8_t bounding_box_points_number;  ///< Number of points to define the bounding box.
    models::coords_list_t bounding_box;  ///< Precomputed bounding box for avoidance.
} obstacle_circle_t;

// Overload the stream insertion operator for obstacle_circle_t
inline std::ostream& operator<<(std::ostream& os, const obstacle_circle_t& obj) {
    os << "obstacle_circle_t(center=" << obj.center
       << ", radius=" << obj.radius
       << ", bounding_box_margin=" << obj.bounding_box_margin
       << ", bounding_box_points_number=" << static_cast<int>(obj.bounding_box_points_number)
       << ", bounding_box=" << obj.bounding_box
       << ")";
    return os;
}

} // namespace obstacles

} // namespace cogip

/// @}
