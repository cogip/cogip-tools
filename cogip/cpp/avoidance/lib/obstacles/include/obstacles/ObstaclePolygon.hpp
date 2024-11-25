// Copyright (C) 2021 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level
// directory for more details.

/// @ingroup     lib_obstacles
/// @file        ObstaclePolygon.hpp
/// @brief       Declaration of the ObstaclePolygon class, representing a polygonal obstacle.
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include <vector>
#include "obstacles/Obstacle.hpp"

namespace cogip {

namespace obstacles {

/// @class ObstaclePolygon
/// @brief A polygon obstacle defined by a list of points.
class ObstaclePolygon : public Obstacle {
public:
    /// @brief Default constructor.
    ObstaclePolygon() = default;

    /// @brief Constructor with points defining the polygon.
    ObstaclePolygon(
        const std::vector<cogip_defs::Coords> &points ///< [in] List of points defining the polygon.
    );

    /// @brief Check if a point is inside the polygon.
    bool is_point_inside(const cogip_defs::Coords &p) const override;

    /// @brief Check if a segment defined by two points crosses the polygon.
    bool is_segment_crossing(const cogip_defs::Coords &a, const cogip_defs::Coords &b) const override;

    /// @brief Find the nearest point on the polygon's perimeter to a given point.
    cogip_defs::Coords nearest_point(const cogip_defs::Coords &p) const override;

private:
    /// @brief Update the bounding box based on the polygon's points.
    void update_bounding_box_() override;

    /// @brief Calculate the centroid (center of mass) of the polygon.
    /// @return 0 on success, negative number otherwise
    int calculate_polygon_centroid();

    /// @brief Calculate the circumcircle radius of the polygon.
    /// @return 0 on success, negative number otherwise
    int calculate_polygon_radius();

    /// @brief Check if a segment [AB] crosses a line (CD).
    /// @param[in] a Point A
    /// @param[in] b Point B
    /// @param[in] c Point C
    /// @param[in] d Point D
    /// @return True if the segment crosses the line, false otherwise.
    static bool _is_segment_crossing_line(
        const cogip_defs::Coords &a, const cogip_defs::Coords &b,
        const cogip_defs::Coords &c, const cogip_defs::Coords &d);

    /// @brief Check if a segment [AB] crosses another segment [CD].
    /// @param[in] a Point A
    /// @param[in] b Point B
    /// @param[in] c Point C
    /// @param[in] d Point D
    /// @return True if the segments cross, false otherwise.
    static bool _is_segment_crossing_segment(
        const cogip_defs::Coords &a, const cogip_defs::Coords &b,
        const cogip_defs::Coords &c, const cogip_defs::Coords &d);

    std::vector<cogip_defs::Coords> points_; ///< Points defining the polygon.
};

} // namespace obstacles

} // namespace cogip

/// @}
