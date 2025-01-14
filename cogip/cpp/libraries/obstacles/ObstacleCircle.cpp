// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "obstacles/ObstacleCircle.hpp"

// System includes
#include <cmath>
#include <cstring>

namespace cogip {

namespace obstacles {

ObstacleCircle::ObstacleCircle(obstacle_circle_t* data):
    data_(data == nullptr ? new obstacle_circle_t() : data),
    external_data_(data != nullptr),
    center_(models::Pose(&data_->center)),
    bounding_box_(models::CoordsList(&data_->bounding_box))
{
}

ObstacleCircle::ObstacleCircle(const ObstacleCircle& other, bool deep_copy):
    data_(deep_copy ? new obstacle_circle_t() : other.data_),
    external_data_(!deep_copy),
    center_(models::Pose(&data_->center)),
    bounding_box_(models::CoordsList(&data_->bounding_box))
{
    if (deep_copy) {
        memcpy(data_, other.data_, sizeof(obstacle_circle_t));
    }
}

ObstacleCircle::ObstacleCircle(
    double x,
    double y,
    double angle,
    double radius,
    double bounding_box_margin,
    uint8_t bounding_box_points_number,
    obstacle_circle_t* data
):
    data_(data == nullptr ? new obstacle_circle_t() : data),
    external_data_(data != nullptr),
    center_(models::Pose(&data_->center)),
    bounding_box_(models::CoordsList(&data_->bounding_box))
{
    data_->id = 0;
    data_->center.x = x;
    data_->center.y = y;
    data_->center.angle = angle;
    data_->radius = radius;
    data_->bounding_box_margin = bounding_box_margin;
    data_->bounding_box_points_number = bounding_box_points_number;
    update_bounding_box();
}

ObstacleCircle::~ObstacleCircle()
{
    if (!external_data_) {
        delete data_;
    }
}

bool ObstacleCircle::is_segment_crossing(const models::Coords& a, const models::Coords& b)
{
    if (!is_line_crossing_circle(a, b)) {
        return false;
    }
    if (is_point_inside(a) || is_point_inside(b)) {
        return true;
    }

    models::Coords vect_ab(b.x() - a.x(), b.y() - a.y());
    models::Coords vect_ac(data_->center.x - a.x(), data_->center.y - a.y());
    models::Coords vect_bc(data_->center.x - b.x(), data_->center.y - b.y());

    double scal1 = vect_ab.x() * vect_ac.x() + vect_ab.y() * vect_ac.y();
    double scal2 = (-vect_ab.x()) * vect_bc.x() + (-vect_ab.y()) * vect_bc.y();

    return (scal1 >= 0 && scal2 >= 0);
}

models::Coords ObstacleCircle::nearest_point(const models::Coords& p)
{
    models::Coords vect(p.x() - data_->center.x, p.y() - data_->center.y);
    double vect_norm = std::hypot(vect.x(), vect.y());

    double scale = (data_->radius * (1 + data_->bounding_box_margin)) / vect_norm;

    return models::Coords(
        data_->center.x + vect.x() * scale,
        data_->center.y + vect.y() * scale
    );
}

bool ObstacleCircle::is_line_crossing_circle(const models::Coords& a, const models::Coords& b)
{
    models::Coords vect_ab(b.x() - a.x(), b.y() - a.y());
    models::Coords vect_ac(data_->center.x - a.x(), data_->center.y - a.y());

    double numerator = std::abs(vect_ab.x() * vect_ac.y() - vect_ab.y() * vect_ac.x());
    double denominator = std::hypot(vect_ab.x(), vect_ab.y());

    return (numerator / denominator) < data_->radius;
}

void ObstacleCircle::update_bounding_box()
{
    if (data_->radius <= 0) return;

    double circumscribed_radius = (data_->radius / cos(M_PI / data_->bounding_box_points_number)) + data_->bounding_box_margin;
    bounding_box_.clear();

    for (uint8_t i = 0; i < data_->bounding_box_points_number; ++i) {
        double angle = (static_cast<double>(i) * 2 * M_PI) / data_->bounding_box_points_number;
        bounding_box_.append(
            data_->center.x + circumscribed_radius * cos(angle),
            data_->center.y + circumscribed_radius * sin(angle)
        );
    }
}

} // namespace obstacles

} // namespace cogip
