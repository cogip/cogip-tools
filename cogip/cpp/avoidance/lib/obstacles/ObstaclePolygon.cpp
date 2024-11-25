// Copyright (C) 2021 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

// Project includes
#include "obstacles/ObstaclePolygon.hpp"
#include "utils.hpp"

// System includes
#include <cmath>
#include <limits>

namespace cogip {

namespace obstacles {

bool ObstaclePolygon::_is_segment_crossing_line(
    const cogip_defs::Coords &a, const cogip_defs::Coords &b,
    const cogip_defs::Coords &c, const cogip_defs::Coords &d)
{
    cogip_defs::Coords ab(b.x() - a.x(), b.y() - a.y());
    cogip_defs::Coords ac(c.x() - a.x(), c.y() - a.y());
    cogip_defs::Coords ad(d.x() - a.x(), d.y() - a.y());

    double det = (ab.x() * ad.y() - ab.y() * ad.x()) * (ab.x() * ac.y() - ab.y() * ac.x());
    return (det < 0);
}

bool ObstaclePolygon::_is_segment_crossing_segment(
    const cogip_defs::Coords &a, const cogip_defs::Coords &b,
    const cogip_defs::Coords &c, const cogip_defs::Coords &d)
{
    return _is_segment_crossing_line(a, b, c, d) &&
           _is_segment_crossing_line(c, d, a, b);
}

ObstaclePolygon::ObstaclePolygon(const std::vector<cogip_defs::Coords> &points)
{
    for (const auto &point : points) {
        push_back(point);
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

    if (size() < 3) {
        return -ERANGE;
    }

    for (auto it = begin(); it != end(); ++it) {
        const auto &p1 = *it;
        const auto &p2 = (it + 1 == end()) ? front() : *(it + 1);

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

    radius_ = 0.0;
    for (const auto &point : *this) {
        double dx = point.x() - center_.x();
        double dy = point.y() - center_.y();
        radius_ = std::max(radius_, std::sqrt(dx * dx + dy * dy));
    }

    return 0;
}

bool ObstaclePolygon::is_point_inside(const cogip_defs::Coords &p) const {
    for (size_t i = 0; i < size(); i++) {
        const cogip_defs::Coords &a = at(i);
        const cogip_defs::Coords &b = (i == size() - 1) ? front() : at(i + 1);

        cogip_defs::Coords ab(b.x() - a.x(), b.y() - a.y());
        cogip_defs::Coords ap(p.x() - a.x(), p.y() - a.y());

        if (ab.x() * ap.y() - ab.y() * ap.x() <= 0) {
            return false;
        }
    }
    return true;
}

bool ObstaclePolygon::is_segment_crossing(const cogip_defs::Coords &a, const cogip_defs::Coords &b) const {
    for (size_t i = 0; i < size(); i++) {
        const cogip_defs::Coords &p_next = (i + 1 == size()) ? front() : at(i + 1);

        if (_is_segment_crossing_segment(a, b, at(i), p_next)) {
            return true;
        }

        int index = point_index(a);
        int index2 = point_index(b);

        if ((index >= 0 && index2 >= 0 && std::abs(index - index2) != 1) ||
            at(i).on_segment(a, b)) {
            return true;
        }
    }
    return false;
}

cogip_defs::Coords ObstaclePolygon::nearest_point(const cogip_defs::Coords &p) const {
    double min_distance = std::numeric_limits<double>::max();
    cogip_defs::Coords closest_point = p;

    for (const auto &point : *this) {
        double distance = p.distance(point);
        if (distance < min_distance) {
            min_distance = distance;
            closest_point = point;
        }
    }

    return closest_point;
}

void ObstaclePolygon::update_bounding_box_() {
    for (auto &point : *this) {
        point.set_x(center_.x() + (point.x() - center_.x()) * (1 + bounding_box_margin_));
        point.set_y(center_.y() + (point.y() - center_.y()) * (1 + bounding_box_margin_));
    }
}

} // namespace obstacles

} // namespace cogip
