// Copyright (C) 2021 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level
// directory for more details.

/// @ingroup     lib_obstacles
/// @file        ObstacleRectangle.hpp
/// @brief       Declaration of the ObstacleRectangle class, representing a rectangular obstacle.
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "obstacles/ObstaclePolygon.hpp"

namespace cogip {

namespace obstacles {

/// @class ObstacleRectangle
/// @brief A rectangular obstacle that simplifies the representation of a polygon.
///
/// This class provides a simplified way to define rectangular obstacles by specifying
/// a center pose, orientation, and lengths along the X and Y axes.
class ObstacleRectangle : public ObstaclePolygon {
public:
    /// @brief Constructor for ObstacleRectangle.
    /// @param center Center pose of the rectangle.
    /// @param length_x Length of the rectangle along the X-axis.
    /// @param length_y Length of the rectangle along the Y-axis.
    ObstacleRectangle(
        const cogip_defs::Pose &center, ///< [in] Center of the rectangle.
        double length_x,                ///< [in] Length along the X-axis.
        double length_y                 ///< [in] Length along the Y-axis.
    );

private:
    /// @brief Update the bounding box for the rectangle.
    void update_bounding_box_() override;

    double length_x_; ///< Length of the rectangle along the X-axis.
    double length_y_; ///< Length of the rectangle along the Y-axis.
};

} // namespace obstacles

} // namespace cogip

/// @}
