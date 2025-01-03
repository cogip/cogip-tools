// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_obstacles
/// @file        ObstacleRectangle.hpp
/// @brief       Declaration of the ObstacleRectangle class, representing a rectangular obstacle.
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "obstacles/ObstaclePolygon.hpp"
#include "models/Pose.hpp"

namespace cogip {

namespace obstacles {

/// @class ObstacleRectangle
/// @brief A rectangular obstacle that simplifies the representation of a polygon.
///
/// This class provides a simplified way to define rectangular obstacles by specifying
/// a center pose, orientation, and lengths along the X and Y axes.
class ObstacleRectangle : public ObstaclePolygon {
public:
    /// Constructor.
    ObstacleRectangle(
        obstacle_polygon_t* data  ///< [in] Pointer to an existing data structure
                                  ///<      If nullptr, will allocate one internally
    ): ObstaclePolygon(data) {};

    /// Copy constructor.
    /// @param other The obstacle to copy.
    /// @param deep_copy If true, will perform a deep copy of the data.
    ObstacleRectangle(const ObstaclePolygon& other, bool deep_copy=false): ObstaclePolygon(other, deep_copy) {};

    /// Constructor for ObstacleRectangle.
    ObstacleRectangle(
        double x,                            ///< [in] X coordinate of the center.
        double y,                            ///< [in] Y coordinate of the center.
        double angle,                        ///< [in] Orientation angle in degrees.
        double length_x,                     ///< [in] Length along the X-axis.
        double length_y,                     ///< [in] Length along the Y-axis.
        double bounding_box_margin,          ///< [in] Bounding box margin.
        uint8_t bounding_box_points_number,  ///< [in] Number of points for the bounding box.
        obstacle_polygon_t* data=nullptr     ///< [in] Pointer to an existing data structure
                                             ///<      If nullptr, will allocate one internally
    );

    /// Return length along the X-axis.
    double length_x() const { return data_->length_x; }

    /// Return length along the Y-axis.
    double length_y() const { return data_->length_y; }

private:
    /// Update the bounding box for the rectangle.
    void update_bounding_box() override;
};

} // namespace obstacles

} // namespace cogip

/// @}
