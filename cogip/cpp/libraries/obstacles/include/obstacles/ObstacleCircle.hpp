// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_obstacles
/// @file        ObstacleCircle.hpp
/// @brief       Declaration of the ObstacleCircle class, representing a circular obstacle.
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "obstacles/Obstacle.hpp"
#include "obstacles/obstacle_circle.hpp"

namespace cogip {

namespace obstacles {

/// @class ObstacleCircle
/// Circle obstacle defined by its center and radius.
class ObstacleCircle : public Obstacle {
public:
    /// Default constructor.
    ObstacleCircle() = delete;

    /// Constructor.
    ObstacleCircle(
        obstacle_circle_t* data  ///< [in] Pointer to an existing data structure
                                 ///<      If nullptr, will allocate one internally
    );

    /// Copy constructor.
    /// @param other The obstacle to copy.
    /// @param deep_copy If true, will perform a deep copy of the data.
    ObstacleCircle(const ObstacleCircle& other, bool deep_copy=false);

    /// Constructor with initial values.
    ObstacleCircle(
        double x,                            ///< [in] X coordinate of the center.
        double y,                            ///< [in] Y coordinate of the center.
        double angle,                        ///< [in] Orientation angle in degrees.
        double radius,                       ///< [in] Radius of the circle.
        double bounding_box_margin,          ///< [in] Bounding box margin.
        uint8_t bounding_box_points_number,  ///< [in] Number of points for the bounding box.
        obstacle_circle_t* data=nullptr      ///< [in] Pointer to an existing data structure
                                             ///<      If nullptr, will allocate one internally
    );

    /// Destructor.
    ~ObstacleCircle();

    /// Check if a point is inside the circle.
    bool is_point_inside(double x, double y) override { return center_.distance(x, y) <= data_->radius; };
    bool is_point_inside(const models::Coords& p) override { return is_point_inside(p.x(), p.y()); };

    /// Check if a segment defined by two points crosses the circle.
    bool is_segment_crossing(const models::Coords& a, const models::Coords& b) override;

    /// Find the nearest point on the circle's perimeter to a given point.
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
    virtual models::CoordsList& bounding_box() override { return bounding_box_; };

    /// Equality operator.
    bool operator==(obstacle_circle_t& other) const {
        return data_->center.x == other.center.x &&
               data_->center.y == other.center.y &&
               data_->center.angle == other.center.angle &&
               data_->radius == other.radius &&
               data_->bounding_box_margin == other.bounding_box_margin &&
               data_->bounding_box_points_number == other.bounding_box_points_number;
    }

private:
    obstacle_circle_t* data_;  ///< pointer to internal data structure
    bool external_data_;       ///< Flag to indicate if memory is externally managed

    /// C++ wrappers.
    models::Pose center_;
    models::CoordsList bounding_box_;

    /// Update the bounding box.
    void update_bounding_box() override;

    /// Check if a line defined by two points crosses the circle.
    /// @return True if (AB) crosses the circle, false otherwise.
    bool is_line_crossing_circle(
        const models::Coords& a, ///< [in] Point A.
        const models::Coords& b  ///< [in] Point B.
    );
};

// Overload the stream insertion operator for obstacle_circle_t
inline std::ostream& operator<<(std::ostream& os, ObstacleCircle& obj) {
    os << "ObstacleCircle(center=" << obj.center()
       << ", radius=" << obj.radius()
       << ", bounding_box_margin=" << obj.bounding_box_margin()
       << ", bounding_box_points_number=" << obj.bounding_box_points_number()
       << ", bounding_box=" << obj.bounding_box()
       << ")";
    return os;
}

} // namespace obstacles

} // namespace cogip

/// @}
