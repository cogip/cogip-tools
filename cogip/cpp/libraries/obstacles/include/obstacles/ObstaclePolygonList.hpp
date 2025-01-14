// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_obstacles
/// @file        ObstaclePolygonList.hpp
/// @brief       Declaration of the ObstaclePolygonList class, representing a list of polygon obstacles.
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "obstacles/ObstaclePolygon.hpp"
#include "obstacles/obstacle_polygon_list.hpp"
#include "models/List.hpp"

namespace cogip {

namespace obstacles {

class ObstaclePolygonList:
    public models::List<obstacle_polygon_t, ObstaclePolygon, obstacle_polygon_list_t, OBSTACLE_LIST_SIZE_MAX>
{
public:
    ObstaclePolygonList(obstacle_polygon_list_t* list) : List(list) {};

    void append(
        const models::CoordsList& points,    ///< [in] List of points defining the polygon.
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
            points,
            bounding_box_margin,
            bounding_box_points_number,
            id
        );
    };

    void set(
        std::size_t index,
        const models::CoordsList& points,    ///< [in] List of points defining the polygon.
        double bounding_box_margin,          ///< [in] Bounding box margin.
        uint8_t bounding_box_points_number,  ///< [in] Number of points for the bounding box.
        uint32_t id = 0                      ///< [in] Optional identifier.
    ) {
        if (index >= size()) {
            throw std::runtime_error("index out of range");
        }
        ObstaclePolygon(
            points,
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
