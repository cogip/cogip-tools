// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_obstacles
/// @{
/// @file
/// @brief       Polygon obstacle class declaration for collision detection and avoidance.
/// @details     Defines an abstract base class representing polygonal obstacles.
///              Includes methods to check for point inclusion, segment intersection,
///              and nearest point calculations.
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "models/CoordsList.hpp"
#include "models/Pose.hpp"

#include <cstdint>

namespace cogip {

namespace obstacles {

constexpr std::size_t OBSTACLE_LIST_SIZE_MAX = 256;

/// @class Obstacle
/// @brief Represents a generic obstacle for collision detection and avoidance.
class Obstacle {
public:
    /// Default constructor.
    Obstacle() {};

    /// Check if the given point is inside the obstacle.
    virtual bool is_point_inside(double x, double y) = 0;
    virtual bool is_point_inside(const models::Coords& p) = 0;

    /// Check if a segment defined by two points A,B is crossing an obstacle.
    virtual bool is_segment_crossing(double ax, double ay, double bx, double by) = 0;
    virtual bool is_segment_crossing(const models::Coords& a, const models::Coords& b) = 0;

    /// Find the nearest point of obstacle perimeter from a given point.
    virtual models::Coords nearest_point(const models::Coords& p) = 0;

    /// Return obstacle id.
    virtual uint32_t id() const = 0;

    /// Set obstacle id.
    virtual void set_id(uint32_t id) = 0;

    /// Return obstacle center.
    virtual const models::Pose& center() const = 0;

    /// Set obstacle center.
    virtual void set_center(const models::Pose& center) = 0;

    /// Return obstacle circumscribed circle radius.
    virtual double radius() const = 0;

    /// Return margin for the bounding box.
    virtual double bounding_box_margin() const = 0;

    /// Return obstacle circumscribed circle radius.
    virtual uint8_t bounding_box_points_number() const = 0;

    /// Get the bounding box.
    virtual models::CoordsList& bounding_box() = 0;

private:
    /// Update bounding box.
    virtual void update_bounding_box() = 0;
};

} // namespace obstacles

} // namespace cogip

/// @}
