// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#pragma once

#include "models/circle_list.hpp"
#include "models/coords_list.hpp"
#include "models/pose.hpp"
#include "models/pose_buffer.hpp"
#include "models/pose_order_list.hpp"
#include "obstacles/obstacle_circle_list.hpp"
#include "obstacles/obstacle_polygon_list.hpp"

#include <cstdint>
#include <map>
#include <ostream>

namespace cogip {

namespace shared_memory {

typedef struct shared_properties_t {
    std::uint8_t robot_id;  ///< Robot ID.
    std::uint16_t robot_width;  ///< Width of the robot (mm)
    std::uint16_t robot_length;  ///< Length of the robot (mm)
    std::uint16_t obstacle_radius;  ///< Radius of the obstacle (mm)
    double obstacle_bb_margin;  ///< Margin for the bounding box of the obstacle (mm)
    std::uint8_t obstacle_bb_vertices;  ///< Number of vertices for the bounding box of the obstacle
    double obstacle_updater_interval;  ///< Interval for updating obstacles (seconds)
    double path_refresh_interval;  ///< Interval for refreshing the path (seconds)
    bool bypass_detector;  ///< Whether to bypass the detector
    bool disable_fixed_obstacles;  ///< Whether to disable fixed obstacles
    std::uint8_t table;  ///< Table ID
    std::uint8_t strategy;  ///< Strategy ID
    std::uint8_t start_position;  ///< Start position ID
    std::uint8_t avoidance_strategy;  ///< Avoidance strategy ID
} shared_properties_t;

/// Overloads the stream insertion operator for `shared_properties_t`.
/// Prints the shared data in a human-readable format.
/// @param os The output stream.
/// @param data The shared data to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const shared_properties_t& data) {
    os << "shared_properties_t("
       << "robot_id=" << static_cast<int>(data.robot_id) << ", "
       << "robot_width=" << data.robot_width << ", "
       << "robot_length=" << data.robot_length << ", "
       << "obstacle_radius=" << data.obstacle_radius << ", "
       << "obstacle_bb_margin=" << data.obstacle_bb_margin << ", "
       << "obstacle_bb_vertices=" << static_cast<int>(data.obstacle_bb_vertices) << ", "
       << "obstacle_updater_interval=" << data.obstacle_updater_interval << ", "
       << "path_refresh_interval=" << data.path_refresh_interval << ", "
       << "bypass_detector=" << (data.bypass_detector ? "true" : "false") << ", "
       << "disable_fixed_obstacles=" << (data.disable_fixed_obstacles ? "true" : "false") << ", "
       << "table=" << static_cast<int>(data.table) << ", "
       << "strategy=" << static_cast<int>(data.strategy) << ", "
       << "start_position=" << static_cast<int>(data.start_position) << ", "
       << "avoidance_strategy=" << static_cast<int>(data.avoidance_strategy) << ", "
       << ")";
    return os;
}

} // namespace shared_memory

} // namespace cogip
