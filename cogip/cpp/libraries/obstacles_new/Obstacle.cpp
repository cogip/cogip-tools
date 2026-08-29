// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "obstacles_new/Obstacle.hpp"

#include "utils/trigonometry.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace cogip {

namespace obstacles_new {

/// Twice the signed area of a polygon, computed with the shoelace formula.
///
/// @param[in] points Vertices, absolute mm.
/// @param[in] count Number of vertices. Below three the result is zero.
/// @return Twice the signed area, in mm². Positive counter-clockwise, negative clockwise.
static double signed_area_twice(const models::coords_t* points, std::size_t count)
{
    double total = 0.0;

    // previous trails current by one vertex and starts at the last one, so the closing edge needs
    // no special case: the pairs visited are (n-1, 0), (0, 1), ... (n-2, n-1).
    for (std::size_t current = 0, previous = count - 1; current < count; previous = current++) {
        total += points[previous].x * points[current].y - points[current].x * points[previous].y;
    }

    return total;
}

Obstacle Obstacle::make_circle(double x, double y, double radius, obstacle_t* data)
{
    Obstacle obstacle(data);
    obstacle_t* obstacle_data = obstacle.data_;

    obstacle_data->id = 0;
    obstacle_data->kind = obstacle_kind_t::Circle;
    obstacle_data->enabled = true;
    obstacle_data->outline_count = 1;
    obstacle_data->center = models::pose_t{x, y, 0.0};
    obstacle_data->corner_radius = radius;
    obstacle_data->outline[0] = models::coords_t{x, y};

    return obstacle;
}

Obstacle Obstacle::make_rectangle(
    double x, double y, double angle, double length_x, double length_y, obstacle_t* data)
{
    Obstacle obstacle(data);
    obstacle_t* obstacle_data = obstacle.data_;

    obstacle_data->id = 0;
    obstacle_data->kind = obstacle_kind_t::Rectangle;
    obstacle_data->enabled = true;
    obstacle_data->outline_count = 4;
    obstacle_data->center = models::pose_t{x, y, angle};
    obstacle_data->corner_radius = 0.0;

    const double cos_theta = std::cos(DEG2RAD(angle));
    const double sin_theta = std::sin(DEG2RAD(angle));
    const double half_x = length_x / 2;
    const double half_y = length_y / 2;

    const double local[4][2] = {
        { -half_x, -half_y },
        {  half_x, -half_y },
        {  half_x,  half_y },
        { -half_x,  half_y },
    };

    for (std::size_t i = 0; i < 4; i++) {
        obstacle_data->outline[i].x = x + local[i][0] * cos_theta - local[i][1] * sin_theta;
        obstacle_data->outline[i].y = y + local[i][0] * sin_theta + local[i][1] * cos_theta;
    }

    return obstacle;
}

Obstacle Obstacle::make_polygon(const models::coords_t* points, std::size_t count, obstacle_t* data)
{
    if (points == nullptr || count == 0) {
        throw std::runtime_error("an obstacle outline needs at least one point");
    }
    if (count > OBSTACLE_OUTLINE_SIZE_MAX) {
        throw std::runtime_error("obstacle outline is full");
    }

    Obstacle obstacle(data);
    obstacle_t* obstacle_data = obstacle.data_;

    obstacle_data->id = 0;
    obstacle_data->kind = obstacle_kind_t::Polygon;
    obstacle_data->enabled = true;
    obstacle_data->outline_count = static_cast<uint8_t>(count);
    obstacle_data->corner_radius = 0.0;

    std::copy(points, points + count, obstacle_data->outline);
    
    // Normalise the winding once, here, rather than letting every future predicate assume it.
    // Below three vertices there is no area, hence no winding to speak of.
    if (count >= 3 && signed_area_twice(obstacle_data->outline, count) < 0.0) {
        std::reverse(obstacle_data->outline, obstacle_data->outline + count);
    }

    // Any point rigidly attached to the outline serves as a reference for a rigid motion. The mean
    // of the vertices is the cheapest one, and unlike the true centroid it needs no geometry.
    double sum_x = 0.0;
    double sum_y = 0.0;
    for (std::size_t i = 0; i < count; i++) {
        sum_x += obstacle_data->outline[i].x;
        sum_y += obstacle_data->outline[i].y;
    }
    obstacle_data->center = models::pose_t{sum_x / count, sum_y / count, 0.0};

    return obstacle;
}

Obstacle::Obstacle(obstacle_t* data):
    data_(data == nullptr ? new obstacle_t() : data),
    external_data_(data != nullptr)
{
}

Obstacle::Obstacle(const Obstacle& other, bool deep_copy):
    data_(deep_copy ? new obstacle_t() : other.data_),
    external_data_(!deep_copy)
{
    if (deep_copy) {
        *data_ = *other.data_;
    }
}

Obstacle::Obstacle(Obstacle&& other) noexcept:
    data_(other.data_),
    external_data_(other.external_data_)
{
    // The source must not release what this object now owns.
    other.external_data_ = true;
}

Obstacle::~Obstacle()
{
    if (!external_data_) {
        delete data_;
    }
}

void Obstacle::set_center(const models::pose_t& center)
{
    const double old_x = data_->center.x;
    const double old_y = data_->center.y;
    const double delta_angle = center.angle - data_->center.angle;
    const double cos_theta = std::cos(DEG2RAD(delta_angle));
    const double sin_theta = std::sin(DEG2RAD(delta_angle));

    // The outline is stored in absolute table coordinates, so it has to follow. Keeping it in
    // local coordinates instead would make this free, but would cost a sine and a cosine per
    // vertex on every geometric query; the visibility graph runs those far more often than moves.
    for (std::size_t i = 0; i < data_->outline_count; i++) {
        const double dx = data_->outline[i].x - old_x;
        const double dy = data_->outline[i].y - old_y;
        data_->outline[i].x = center.x + dx * cos_theta - dy * sin_theta;
        data_->outline[i].y = center.y + dx * sin_theta + dy * cos_theta;
    }

    data_->center = center;
}

const models::coords_t& Obstacle::point(std::size_t index) const
{
    if (index >= data_->outline_count) {
        throw std::runtime_error("index out of range");
    }
    return data_->outline[index];
}

} // namespace obstacles_new

} // namespace cogip
