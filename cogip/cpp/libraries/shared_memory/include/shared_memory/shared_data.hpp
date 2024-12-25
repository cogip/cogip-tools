// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#pragma once

#include "models/coords_list.hpp"
#include "models/pose.hpp"
#include "obstacles/obstacle_circle_list.hpp"
#include "obstacles/obstacle_polygon_list.hpp"

#include <cstdint>
#include <map>
#include <ostream>

namespace cogip {

namespace shared_memory {

constexpr std::size_t NUM_ANGLES = 360;

/// Represents shared data in shared memory.
typedef struct {
    models::pose_t pose_current;  ///< The current pose.
    models::pose_t pose_order;    ///< The target pose.
    uint16_t lidar_data[NUM_ANGLES][2];  ///< The Lidar data.
    models::coords_list_t detector_obstacles;  ///< The obstacles from detector.
    models::coords_list_t monitor_obstacles;   ///< The obstacles from monitor.
    obstacles::obstacle_circle_list_t circle_obstacles;  ///< The circle obstacles from planner.
    obstacles::obstacle_polygon_list_t rectangle_obstacles;  ///< The rectangle obstacles from planner.
} shared_data_t;

/// Overloads the stream insertion operator for `shared_data_t`.
/// Prints the shared data in a human-readable format.
/// @param os The output stream.
/// @param data The shared data to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const shared_data_t& data) {
    os << "shared_data_t(size=" << sizeof(shared_data_t) << ")";
    return os;
}

/// Enum representing different locks for shared memory.
enum class LockName {
    PoseCurrent,  ///< Lock for the pose_current.
    PoseOrder,    ///< Lock for the pose_order.
    LidarData,    ///< Lock for the lidar_data.
    DetectorObstacles, ///< Lock for the obstacles from detector.
    MonitorObstacles,  ///< Lock for the obstacles from the monitor.
    Obstacles,    ///< Lock for the circle obstacles from planner.
};

/// Maps `LockName` enum values to their corresponding string representations.
static std::map<LockName, std::string> lock2str = {
    { LockName::PoseCurrent, "PoseCurrent" },
    { LockName::PoseOrder, "PoseOrder" },
    { LockName::LidarData, "LidarData" },
    { LockName::DetectorObstacles, "DetectorObstacles" },
    { LockName::MonitorObstacles, "MonitorObstacles" },
    { LockName::Obstacles, "Obstacles" },
};

} // namespace shared_memory

} // namespace cogip
