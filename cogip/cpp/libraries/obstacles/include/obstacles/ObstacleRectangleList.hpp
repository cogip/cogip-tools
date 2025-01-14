// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_obstacles
/// @file        ObstacleRectangleList.hpp
/// @brief       Declaration of the ObstacleRectangleList class, representing a list of rectangle obstacles.
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "obstacles/ObstacleRectangle.hpp"
#include "obstacles/obstacle_polygon_list.hpp"
#include "models/List.hpp"

namespace cogip {

namespace obstacles {

class ObstacleRectangleList:
    public models::List<obstacle_polygon_t, ObstacleRectangle, obstacle_polygon_list_t, OBSTACLE_LIST_SIZE_MAX>
{
public:
    ObstacleRectangleList(obstacle_polygon_list_t* list) : List(list) {};

    void append(
        double x,                            ///< [in] X coordinate of the center.
        double y,                            ///< [in] Y coordinate of the center.
        double angle,                        ///< [in] Orientation angle in degrees.
        double length_x,                     ///< [in] Length along the X-axis.
        double length_y,                     ///< [in] Length along the Y-axis.
        double bounding_box_margin,          ///< [in] Bounding box margin.
        uint8_t bounding_box_points_number,  ///< [in] Number of points for the bounding box.
        uint32_t id = 0                      ///< [in] Optional identifier.
    ) {
        if (size() >= max_size()) {
            throw std::runtime_error("ObstaclePolygonList is full");
        }
        list_->count++;
        set(
            size() - 1,
            x,
            y,
            angle,
            length_x,
            length_y,
            bounding_box_margin,
            bounding_box_points_number,
            id
        );
    };

    void set(
        std::size_t index,
        double x,                            ///< [in] X coordinate of the center.
        double y,                            ///< [in] Y coordinate of the center.
        double angle,                        ///< [in] Orientation angle in degrees.
        double length_x,                     ///< [in] Length along the X-axis.
        double length_y,                     ///< [in] Length along the Y-axis.
        double bounding_box_margin,          ///< [in] Bounding box margin.
        uint8_t bounding_box_points_number,  ///< [in] Number of points for the bounding box.
        uint32_t id = 0                      ///< [in] Optional identifier.
    ) {
        if (index >= size()) {
            throw std::runtime_error("index out of range");
        }
        ObstacleRectangle(
            x,
            y,
            angle,
            length_x,
            length_y,
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
