// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

// Project includes
#include "obstacles/ObstaclePolygon.hpp"

// System includes
#include <cmath>
#include <cstring>
#include <limits>

namespace cogip {

namespace obstacles {

/// Check if a segment [AB] crosses a line (CD).
/// @param[in] a Point A
/// @param[in] b Point B
/// @param[in] c Point C
/// @param[in] d Point D
/// @return True if the segment crosses the line, false otherwise.
static bool is_segment_crossing_line(
    const models::Coords& a, const models::Coords& b,
    const models::Coords& c, const models::Coords& d)
{
    models::Coords ab(b.x() - a.x(), b.y() - a.y());
    models::Coords ac(c.x() - a.x(), c.y() - a.y());
    models::Coords ad(d.x() - a.x(), d.y() - a.y());

    double det = (ab.x() * ad.y() - ab.y() * ad.x()) * (ab.x() * ac.y() - ab.y() * ac.x());
    return (det < 0);
}

/// Check if a segment [AB] crosses another segment [CD].
/// @param[in] a Point A
/// @param[in] b Point B
/// @param[in] c Point C
/// @param[in] d Point D
/// @return True if the segments cross, false otherwise.
static bool is_segment_crossing_segment(
    const models::Coords& a, const models::Coords& b,
    const models::Coords& c, const models::Coords& d)
{
    return is_segment_crossing_line(a, b, c, d) &&
           is_segment_crossing_line(c, d, a, b);
}

ObstaclePolygon::ObstaclePolygon(obstacle_polygon_t* data):
    data_(data == nullptr ? new obstacle_polygon_t() : data),
    external_data_(data != nullptr),
    points_(models::CoordsList(&data_->points)),
    center_(models::Pose(&data_->center)),
    bounding_box_(models::CoordsList(&data_->bounding_box))
{
}

ObstaclePolygon::ObstaclePolygon(const ObstaclePolygon& other, bool deep_copy):
    data_(deep_copy ? new obstacle_polygon_t() : other.data_),
    external_data_(!deep_copy),
    center_(models::Pose(&data_->center)),
    points_(models::CoordsList(&data_->points)),
    bounding_box_(models::CoordsList(&data_->bounding_box))
{
    if (deep_copy) {
        // Deep copy at the data level
        memcpy(data_, other.data_, sizeof(obstacle_polygon_t));
    }
}

ObstaclePolygon::ObstaclePolygon(
    const models::CoordsList& points,
    double bounding_box_margin,
    uint8_t bounding_box_points_number,
    obstacle_polygon_t* data
):
    data_(data == nullptr ? new obstacle_polygon_t() : data),
    external_data_(data != nullptr),
    points_(models::CoordsList(&data_->points)),
    center_(models::Pose(&data_->center)),
    bounding_box_(models::CoordsList(&data_->bounding_box))
{
    data_->bounding_box_margin = bounding_box_margin;
    data_->bounding_box_points_number = bounding_box_points_number;
    for (const auto& point : points) {
        points_.append(point);
    }

    int res = calculate_polygon_radius();
    if (res == -ERANGE) {
        throw std::runtime_error("Not enough obstacle points, need at least 3");
    }
}

int ObstaclePolygon::calculate_polygon_centroid() {
    double x_sum = 0.0;
    double y_sum = 0.0;
    double area = 0.0;

    if (points_.size() < 3) {
        return -ERANGE;
    }

    for (std::size_t i = 0; i < points_.size(); i++) {
        const auto& p1 = points_[i];
        const auto& p2 = points_[(i + 1) % points_.size()];

        double cross_product = p1.x() * p2.y() - p2.x() * p1.y();
        area += cross_product;
        x_sum += (p1.x() + p2.x()) * cross_product;
        y_sum += (p1.y() + p2.y()) * cross_product;
    }

    area *= 0.5;
    double factor = 1.0 / (6.0 * std::fabs(area));

    center_.set_x(x_sum * factor);
    center_.set_y(y_sum * factor);

    return 0;
}

int ObstaclePolygon::calculate_polygon_radius() {
    int res = calculate_polygon_centroid();
    if (res) {
        return res;
    }

    data_->radius = 0.0;
    for (std::size_t i = 0; i < points_.size(); i++) {
        const models::Coords& point = points_[i];
        double dx = point.x() - center_.x();
        double dy = point.y() - center_.y();
        data_->radius = std::max(data_->radius, std::sqrt(dx * dx + dy * dy));
    }

    return 0;
}

bool ObstaclePolygon::is_point_inside(double x, double y) {
    for (std::size_t i = 0; i < points_.size(); i++) {
        const models::Coords& a = points_[i];
        const models::Coords& b = points_[(i + 1) % points_.size()];

        models::Coords ab(b.x() - a.x(), b.y() - a.y());
        models::Coords ap(x - a.x(), y - a.y());

        if (ab.x() * ap.y() - ab.y() * ap.x() <= 0) {
            return false;
        }
    }
    return true;
}

bool ObstaclePolygon::is_segment_crossing(const models::Coords& a, const models::Coords& b) {
    for (size_t i = 0; i < points_.size(); i++) {
        const models::Coords& p = points_[i];
        const models::Coords& p_next = points_[(i + 1) % points_.size()];

        if (is_segment_crossing_segment(a, b, p, p_next)) {
            return true;
        }

        int index = points_.getIndex(a);
        int index2 = points_.getIndex(b);

        if ((index >= 0 && index2 >= 0 && std::abs(index - index2) != 1) ||
            p.on_segment(a, b)) {
            return true;
        }
    }
    return false;
}

models::Coords ObstaclePolygon::nearest_point(const models::Coords& p) {
    double min_distance = std::numeric_limits<double>::max();
    models::Coords closest_point = p;

    for (size_t i = 0; i < points_.size(); i++) {
        const models::Coords& point = points_[i];
        double distance = p.distance(point);
        if (distance < min_distance) {
            min_distance = distance;
            closest_point = point;
        }
    }

    return closest_point;
}

void ObstaclePolygon::update_bounding_box() {
    bounding_box_.clear();
    for (size_t i = 0; i < points_.size(); i++) {
        models::Coords point = points_[i];
        bounding_box_.append(
            point.x() + data_->bounding_box_margin,
            point.y() + data_->bounding_box_margin
        );
    }
}

} // namespace obstacles

} // namespace cogip
