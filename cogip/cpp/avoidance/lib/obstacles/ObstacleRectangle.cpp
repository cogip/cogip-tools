// Copyright (C) 2021 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

// System includes
#include <cmath>

// Project includes
#include "obstacles/ObstacleRectangle.hpp"
#include "trigonometry.h"
#include "utils.hpp"

namespace cogip {

namespace obstacles {

/// Constructor that initializes an obstacle rectangle based on its center, length, and orientation.
ObstacleRectangle::ObstacleRectangle(const cogip_defs::Pose &center, double length_x, double length_y)
    : length_x_(length_x), length_y_(length_y)
{
    center_ = center;

    // Calculate the radius as half of the rectangle's diagonal.
    radius_ = std::sqrt(length_x_ * length_x_ + length_y_ * length_y_) / 2;

    // Precompute trigonometric values for efficiency.
    double cos_theta = std::cos(DEG2RAD(center_.O()));
    double sin_theta = std::sin(DEG2RAD(center_.O()));

    // Add rectangle vertices relative to the center.
    push_back(cogip_defs::Coords(
        center_.x() - (length_x_ / 2) * cos_theta + (length_y_ / 2) * sin_theta,
        center_.y() - (length_x_ / 2) * sin_theta - (length_y_ / 2) * cos_theta
    ));
    push_back(cogip_defs::Coords(
        center_.x() + (length_x_ / 2) * cos_theta + (length_y_ / 2) * sin_theta,
        center_.y() + (length_x_ / 2) * sin_theta - (length_y_ / 2) * cos_theta
    ));
    push_back(cogip_defs::Coords(
        center_.x() + (length_x_ / 2) * cos_theta - (length_y_ / 2) * sin_theta,
        center_.y() + (length_x_ / 2) * sin_theta + (length_y_ / 2) * cos_theta
    ));
    push_back(cogip_defs::Coords(
        center_.x() - (length_x_ / 2) * cos_theta - (length_y_ / 2) * sin_theta,
        center_.y() - (length_x_ / 2) * sin_theta + (length_y_ / 2) * cos_theta
    ));

    // Update the bounding box based on the initialized rectangle.
    update_bounding_box_();
}

/// Updates the bounding box of the rectangle, including a margin.
void ObstacleRectangle::update_bounding_box_()
{
    // Increase dimensions by the bounding box margin.
    double length_x = length_x_ * (1 + bounding_box_margin_);
    double length_y = length_y_ * (1 + bounding_box_margin_);

    // Precompute trigonometric values for efficiency.
    double cos_theta = std::cos(DEG2RAD(center_.O()));
    double sin_theta = std::sin(DEG2RAD(center_.O()));

    // Add bounding box vertices relative to the center.
    bounding_box_.push_back(cogip_defs::Coords(
        center_.x() - (length_x / 2) * cos_theta + (length_y / 2) * sin_theta,
        center_.y() - (length_x / 2) * sin_theta - (length_y / 2) * cos_theta
    ));
    bounding_box_.push_back(cogip_defs::Coords(
        center_.x() + (length_x / 2) * cos_theta + (length_y / 2) * sin_theta,
        center_.y() + (length_x / 2) * sin_theta - (length_y / 2) * cos_theta
    ));
    bounding_box_.push_back(cogip_defs::Coords(
        center_.x() + (length_x / 2) * cos_theta - (length_y / 2) * sin_theta,
        center_.y() + (length_x / 2) * sin_theta + (length_y / 2) * cos_theta
    ));
    bounding_box_.push_back(cogip_defs::Coords(
        center_.x() - (length_x / 2) * cos_theta - (length_y / 2) * sin_theta,
        center_.y() - (length_x / 2) * sin_theta + (length_y / 2) * cos_theta
    ));
}

} // namespace obstacles

} // namespace cogip
