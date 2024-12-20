// Copyright (C) 2021 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level
// directory for more details.

/// @ingroup     lib_obstacles
/// @{
/// @file
/// @brief       Polygon obstacle class declaration for collision detection and avoidance.
/// @details     Defines an abstract base class representing polygonal obstacles.
///              Includes methods to check for point inclusion, segment intersection,
///              and nearest point calculations.
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include <cstdint>
#include "cogip_defs/Pose.hpp"
#include "cogip_defs/Polygon.hpp"

namespace cogip {

namespace obstacles {

/// @class Obstacle
/// @brief Represents a generic polygonal obstacle for collision detection and avoidance.
class Obstacle : public cogip_defs::Polygon {
public:
    /// @brief Default constructor.
    Obstacle() = default;

    /// @brief Constructor for initializing an obstacle with a center, radius, and bounding box margin.
    /// @param center The center position and orientation of the obstacle.
    /// @param radius The radius of the obstacle.
    /// @param bounding_box_margin The margin to apply around the bounding box.
    Obstacle(
        const cogip_defs::Pose &center,
        double radius,
        double bounding_box_margin
    ) :
        center_(center),
        radius_(radius),
        bounding_box_margin_(bounding_box_margin),
        enabled_(true) {}


    /// Check if the given point is inside the obstacle.
    virtual bool is_point_inside(const cogip_defs::Coords &p) const = 0;

    /// Check if a segment defined by two points A,B is crossing an obstacle.
    virtual bool is_segment_crossing(const cogip_defs::Coords &a, const cogip_defs::Coords &b) const = 0;

    /// Find the nearest point of obstacle perimeter from a given point.
    virtual cogip_defs::Coords nearest_point(const cogip_defs::Coords &p) const = 0;

    /// @brief Return obstacle center.
    inline const cogip_defs::Pose &center() const { return center_; }

    /// @brief Set obstacle center.
    void set_center(const cogip_defs::Pose &center) { center_ = center; }

    /// @brief Return obstacle circumscribed circle radius.
    inline double radius() const { return radius_; }

    /// @brief Return true if the obstacle is enabled, false otherwise.
    inline bool enabled() const { return enabled_; }

    /// @brief Enable or disable the obstacle.
    void enable(bool enabled) { enabled_ = enabled; }

    /// @brief Get the bounding box.
    inline const cogip_defs::Polygon& bounding_box() const { return bounding_box_; }

protected:
    cogip_defs::Pose center_;                ///< Obstacle center.
    double radius_;                          ///< Obstacle circumscribed circle radius.
    cogip_defs::Polygon bounding_box_;       ///< Precomputed bounding box for avoidance.
    bool enabled_ = true;                    ///< Obstacle enabled or not.
    double bounding_box_margin_ = 0.2;       ///< Margin for the bounding box.

private:
    /// Update bounding box.
    virtual void update_bounding_box_() = 0;
};

} // namespace obstacles

} // namespace cogip

/// @}
