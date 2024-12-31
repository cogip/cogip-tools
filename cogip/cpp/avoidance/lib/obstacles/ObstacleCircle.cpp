// Copyright (C) 2021 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level
// directory for more details.

#include "obstacles/ObstacleCircle.hpp"
#include "utils.hpp"

// System includes
#include <cmath>

namespace cogip {

namespace obstacles {

ObstacleCircle::ObstacleCircle(
    const cogip_defs::Pose &center,
    double radius,
    double bounding_box_margin,
    uint32_t bounding_box_points_number
) : Obstacle(center, radius, bounding_box_margin),
    bounding_box_points_number_(bounding_box_points_number)
{
    update_bounding_box_();
}

bool ObstacleCircle::is_point_inside(const cogip_defs::Coords &p) const
{
    return center_.distance(p) <= radius_;
}

bool ObstacleCircle::is_segment_crossing(const cogip_defs::Coords &a, const cogip_defs::Coords &b) const
{
    if (!is_line_crossing_circle(a, b)) {
        return false;
    }
    if (is_point_inside(a) || is_point_inside(b)) {
        return true;
    }

    cogip_defs::Coords vect_ab(b.x() - a.x(), b.y() - a.y());
    cogip_defs::Coords vect_ac(center_.x() - a.x(), center_.y() - a.y());
    cogip_defs::Coords vect_bc(center_.x() - b.x(), center_.y() - b.y());

    double scal1 = vect_ab.x() * vect_ac.x() + vect_ab.y() * vect_ac.y();
    double scal2 = (-vect_ab.x()) * vect_bc.x() + (-vect_ab.y()) * vect_bc.y();

    return (scal1 >= 0 && scal2 >= 0);
}

cogip_defs::Coords ObstacleCircle::nearest_point(const cogip_defs::Coords &p) const
{
    cogip_defs::Coords vect(p.x() - center_.x(), p.y() - center_.y());
    double vect_norm = std::hypot(vect.x(), vect.y());

    double scale = (radius_ * (1 + bounding_box_margin_)) / vect_norm;

    return cogip_defs::Coords(
        center_.x() + vect.x() * scale,
        center_.y() + vect.y() * scale
    );
}

bool ObstacleCircle::is_line_crossing_circle(const cogip_defs::Coords &a, const cogip_defs::Coords &b) const
{
    cogip_defs::Coords vect_ab(b.x() - a.x(), b.y() - a.y());
    cogip_defs::Coords vect_ac(center_.x() - a.x(), center_.y() - a.y());

    double numerator = std::abs(vect_ab.x() * vect_ac.y() - vect_ab.y() * vect_ac.x());
    double denominator = std::hypot(vect_ab.x(), vect_ab.y());

    return (numerator / denominator) < radius_;
}

void ObstacleCircle::update_bounding_box_()
{
    if (radius_ <= 0) return;

    double adjusted_radius = radius_ * (1 + bounding_box_margin_);
    bounding_box_.clear();

    for (uint8_t i = 0; i < bounding_box_points_number_; ++i) {
        double angle = (static_cast<double>(i) * 2 * M_PI) / bounding_box_points_number_;
        bounding_box_.emplace_back(
            center_.x() + adjusted_radius * cos(angle),
            center_.y() + adjusted_radius * sin(angle)
        );
    }
}

} // namespace obstacles

} // namespace cogip
