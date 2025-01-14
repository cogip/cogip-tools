// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_obstacles
/// @file        obstacle_circle_list.hpp
/// @brief       Declaration of the obstacle_circle_list struct, representing a list of circular obstacles.
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "obstacles/Obstacle.hpp"
#include "obstacles/obstacle_circle.hpp"

namespace cogip {

namespace obstacles {

typedef struct {
    std::size_t count;
    obstacle_circle_t elems[OBSTACLE_LIST_SIZE_MAX];
} obstacle_circle_list_t;


} // namespace obstacles

} // namespace cogip

/// @}
