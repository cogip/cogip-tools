// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

// Project includes
#include "obstacles/ObstacleRectangle.hpp"
#include "utils/trigonometry.hpp"

// System includes
#include <cmath>

namespace cogip {

namespace obstacles {

/// Constructor that initializes an obstacle rectangle based on its center, length, and orientation.
ObstacleRectangle::ObstacleRectangle(
    double x,
    double y,
    double angle,
    double length_x,
    double length_y,
    double bounding_box_margin,
    obstacle_polygon_t* data
): ObstaclePolygon(data)
{
    data_->id = 0;
    data_->center.x = x;
    data_->center.y = y;
    data_->center.angle = angle;
    data_->length_x = length_x;
    data_->length_y = length_y;
    data_->bounding_box_margin = bounding_box_margin;
    data_->bounding_box_points_number = 4;

    // Calculate the radius as half of the rectangle's diagonal.
    data_->radius = std::sqrt(length_x * length_x + length_y * length_y) / 2;

    // Precompute trigonometric values for efficiency.
    double cos_theta = std::cos(DEG2RAD(angle));
    double sin_theta = std::sin(DEG2RAD(angle));

    // Add rectangle vertices relative to the center.
    points_.clear();
    points_.append(
        x - (length_x / 2) * cos_theta + (length_y / 2) * sin_theta,
        y - (length_x / 2) * sin_theta - (length_y / 2) * cos_theta
    );
    points_.append(
        x + (length_x / 2) * cos_theta + (length_y / 2) * sin_theta,
        y + (length_x / 2) * sin_theta - (length_y / 2) * cos_theta
    );
    points_.append(
        x + (length_x / 2) * cos_theta - (length_y / 2) * sin_theta,
        y + (length_x / 2) * sin_theta + (length_y / 2) * cos_theta
    );
    points_.append(
        x - (length_x / 2) * cos_theta - (length_y / 2) * sin_theta,
        y - (length_x / 2) * sin_theta + (length_y / 2) * cos_theta
    );

    // Update the bounding box based on the initialized rectangle.
    update_bounding_box();
}

/// Updates the bounding box of the rectangle, including a margin.
void ObstacleRectangle::update_bounding_box()
{
    // Increase dimensions by the bounding box margin.
    double length_x = data_->length_x + data_->bounding_box_margin;
    double length_y = data_->length_y + data_->bounding_box_margin;

    // Precompute trigonometric values for efficiency.
    double cos_theta = std::cos(DEG2RAD(data_->center.angle));
    double sin_theta = std::sin(DEG2RAD(data_->center.angle));

    bounding_box_.clear();

    // Add bounding box vertices relative to the center.
    bounding_box_.append(
        data_->center.x - (length_x / 2) * cos_theta + (length_y / 2) * sin_theta,
        data_->center.y - (length_x / 2) * sin_theta - (length_y / 2) * cos_theta
    );
    bounding_box_.append(
        data_->center.x + (length_x / 2) * cos_theta + (length_y / 2) * sin_theta,
        data_->center.y + (length_x / 2) * sin_theta - (length_y / 2) * cos_theta
    );
    bounding_box_.append(
        data_->center.x + (length_x / 2) * cos_theta - (length_y / 2) * sin_theta,
        data_->center.y + (length_x / 2) * sin_theta + (length_y / 2) * cos_theta
    );
    bounding_box_.append(
        data_->center.x - (length_x / 2) * cos_theta - (length_y / 2) * sin_theta,
        data_->center.y - (length_x / 2) * sin_theta + (length_y / 2) * cos_theta
    );
}

} // namespace obstacles

} // namespace cogip
