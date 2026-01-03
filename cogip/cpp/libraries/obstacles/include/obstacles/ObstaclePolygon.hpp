// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_obstacles
/// @file        ObstaclePolygon.hpp
/// @brief       Declaration of the ObstaclePolygon class, representing a polygonal obstacle.
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "models/Coords.hpp"
#include "obstacles/Obstacle.hpp"
#include "obstacles/obstacle_polygon.hpp"
#include "models/List.hpp"

namespace cogip {

namespace obstacles {

/// @class ObstaclePolygon
/// @brief A polygon obstacle defined by a list of points.
class ObstaclePolygon : public Obstacle {
public:
    /// Default constructor.
    ObstaclePolygon() = default;

    /// Constructor.
    ObstaclePolygon(
        obstacle_polygon_t* data  ///< [in] Pointer to an existing data structure
                                  ///<      If nullptr, will allocate one internally
    );

    /// Copy constructor.
    /// @param other The obstacle to copy.
    /// @param deep_copy If true, will perform a deep copy of the data.
    ObstaclePolygon(const ObstaclePolygon& other, bool deep_copy=false);

    /// Constructor with points defining the polygon.
    ObstaclePolygon(
        const models::CoordsList& points,    ///< [in] List of points defining the polygon.
        double bounding_box_margin,          ///< [in] Bounding box margin.
        obstacle_polygon_t* data=nullptr     ///< [in] Pointer to an existing data structure
                                             ///<      If nullptr, will allocate one internally
    );

    /// Check if a point is inside the polygon.
    bool is_point_inside(double x, double y) override;
    bool is_point_inside(const models::Coords& p) override { return is_point_inside(p.x(), p.y()); };

    /// Check if a segment defined by two points crosses the polygon.
    bool is_segment_crossing(double ax, double ay, double bx, double by) override;
    bool is_segment_crossing(const models::Coords& a, const models::Coords& b) override;

    /// Find the nearest point on the polygon's perimeter to a given point.
    models::Coords nearest_point(const models::Coords& p) override;

    /// Return obstacle id.
    uint32_t id() const override { return data_->id; }

    /// Set obstacle id.
    void set_id(uint32_t id) override {
        data_->id = id;
    }

    /// Return obstacle center.
    const models::Pose& center() const override { return center_; }

    /// Set obstacle center.
    void set_center(const models::Pose& center) override {
        data_->center.x = center.x();
        data_->center.y = center.y();
        data_->center.angle = center.angle();
    }

    /// Return obstacle circumscribed circle radius.
    double radius() const override { return data_->radius; }

    /// Return margin for the bounding box.
    double bounding_box_margin() const override { return data_->bounding_box_margin; }

    /// Return obstacle circumscribed circle radius.
    uint8_t bounding_box_points_number() const override { return data_->bounding_box_points_number; }

    /// Get the bounding box.
    models::CoordsList& bounding_box() override { return bounding_box_; };

    models::CoordsList& points() { return points_; }

    /// Equality operator.
    bool operator==(obstacle_polygon_t& other) const {
        return data_->center.x == other.center.x &&
               data_->center.y == other.center.y &&
               data_->center.angle == other.center.angle &&
               data_->radius == other.radius &&
               data_->bounding_box_margin == other.bounding_box_margin &&
               data_->bounding_box_points_number == other.bounding_box_points_number;
    };

protected:
    obstacle_polygon_t* data_;  ///< pointer to internal data structure
    bool external_data_;        ///< Flag to indicate if memory is externally managed

    /// C++ wrappers.
    models::CoordsList points_; ///< Points defining the polygon.
    models::Pose center_;
    models::CoordsList bounding_box_;

    /// Update the bounding box based on the polygon's points.
    virtual void update_bounding_box() override;

    /// Calculate the centroid (center of mass) of the polygon.
    /// @return 0 on success, negative number otherwise
    int calculate_polygon_centroid();

    /// Calculate the circumcircle radius of the polygon.
    /// @return 0 on success, negative number otherwise
    int calculate_polygon_radius();
};

// Overload the stream insertion operator for ObstaclePolygon
inline std::ostream& operator<<(std::ostream& os, ObstaclePolygon& obj) {
    os << "ObstaclePolygon(center=" << obj.center()
       << ", radius=" << obj.radius()
       << ", points=" << obj.points()
       << ", bounding_box_points_number=" << obj.bounding_box_points_number()
       << ", bounding_box_margin=" << obj.bounding_box_margin()
       << ", bounding_box=" << obj.bounding_box()
       << ")";
    return os;
}

} // namespace obstacles

} // namespace cogip

/// @}
