// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_obstacles
/// @file        obstacle_polygon_list.hpp
/// @brief       Declaration of the obstacle_polygon_list struct, representing a list of polygon obstacles.
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "obstacles/Obstacle.hpp"
#include "obstacles/obstacle_polygon.hpp"

namespace cogip {

namespace obstacles {

typedef struct {
    std::size_t count;
    obstacle_polygon_t elems[OBSTACLE_LIST_SIZE_MAX];
} obstacle_polygon_list_t;

} // namespace obstacles

} // namespace cogip

/// @}
