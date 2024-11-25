// Copyright (C) 2021 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level
// directory for more details.

/// @ingroup     lib_obstacles
/// @file        ObstacleCircle.hpp
/// @brief       Declaration of the ObstacleCircle class, representing a circular obstacle.
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "obstacles/Obstacle.hpp"

namespace cogip {

namespace obstacles {

/// @class ObstacleCircle
/// @brief Circle obstacle defined by its center and radius.
class ObstacleCircle : public Obstacle {
public:
    /// @brief Constructor.
    ObstacleCircle(
        const cogip::cogip_defs::Pose &center,  ///< [in] Center of the circle.
        double radius,                          ///< [in] Radius of the circle.
        double bounding_box_margin,             ///< [in] Bounding box margin.
        uint32_t bounding_box_points_number = 8 ///< [in] Number of points for the bounding box.
    );

    /// @brief Check if a point is inside the circle.
    bool is_point_inside(const cogip_defs::Coords &p) const override;

    /// @brief Check if a segment defined by two points crosses the circle.
    bool is_segment_crossing(const cogip_defs::Coords &a, const cogip_defs::Coords &b) const override;

    /// @brief Find the nearest point on the circle's perimeter to a given point.
    cogip_defs::Coords nearest_point(const cogip_defs::Coords &p) const override;

private:
    uint32_t bounding_box_points_number_; ///< Number of points to define the bounding box.

    /// @brief Update the bounding box.
    void update_bounding_box_() override;

    /// @brief Check if a line defined by two points crosses the circle.
    /// @return True if (AB) crosses the circle, false otherwise.
    bool is_line_crossing_circle(
        const cogip_defs::Coords &a, ///< [in] Point A.
        const cogip_defs::Coords &b  ///< [in] Point B.
    ) const;
};

} // namespace obstacles

} // namespace cogip

/// @}
