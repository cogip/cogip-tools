// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_obstacles
/// @file        ObstacleCircleList.hpp
/// @brief       Declaration of the ObstacleCircleList class, representing a list of circular obstacles.
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "obstacles/ObstacleCircle.hpp"
#include "obstacles/obstacle_circle_list.hpp"
#include "models/List.hpp"

namespace cogip {

namespace obstacles {

class ObstacleCircleList:
    public models::List<obstacle_circle_t, ObstacleCircle, obstacle_circle_list_t, OBSTACLE_LIST_SIZE_MAX>
{
public:
    ObstacleCircleList(obstacle_circle_list_t* list) : List(list) {};

    void append(
        double x,
        double y,
        double angle,
        double radius,
        double bounding_box_margin,
        uint8_t bounding_box_points_number,
        uint32_t id = 0
    ) {
        if (size() >= max_size()) {
            throw std::runtime_error("ObstacleCircleList is full");
        }
        list_->count++;
        set(
            size() - 1,
            x,
            y,
            angle,
            radius,
            bounding_box_margin,
            bounding_box_points_number,
            id
        );
    };

    void set(
        std::size_t index,
        double x,
        double y,
        double angle,
        double radius,
        double bounding_box_margin,
        uint8_t bounding_box_points_number,
        uint32_t id = 0
    ) {
        if (index >= size()) {
            throw std::runtime_error("index out of range");
        }
        ObstacleCircle(
            x,
            y,
            angle,
            radius,
            bounding_box_margin,
            bounding_box_points_number,
            &list_->elems[index]
        );
        list_->elems[index].id = id;
    };
};

} // namespace obstacles

} // namespace cogip

/// @}
