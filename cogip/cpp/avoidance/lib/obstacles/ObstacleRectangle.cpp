
// System includes
#include "cmath"

// Project includes
#include "obstacles/ObstacleRectangle.hpp"
#include "trigonometry.h"
#include "utils.hpp"

namespace cogip {

namespace obstacles {

ObstacleRectangle::ObstacleRectangle(
    const cogip_defs::Pose &center,
    double length_x, double length_y)
    : length_x_(length_x), length_y_(length_y)
{
    center_ = center;
    radius_ = sqrt(length_x_ * length_x_ + length_y_ * length_y_) / 2;

    push_back(cogip_defs::Coords(
        center_.x() - (length_x_ / 2) * cos(DEG2RAD(center_.O())) + (length_y_ / 2) * sin(DEG2RAD(center_.O())),
        center_.y() - (length_x_ / 2) * sin(DEG2RAD(center_.O())) - (length_y_ / 2) * cos(DEG2RAD(center_.O()))
    ));
    push_back(cogip_defs::Coords(
        center_.x() + (length_x_ / 2) * cos(DEG2RAD(center_.O())) + (length_y_ / 2) * sin(DEG2RAD(center_.O())),
        center_.y() + (length_x_ / 2) * sin(DEG2RAD(center_.O())) - (length_y_ / 2) * cos(DEG2RAD(center_.O()))
    ));
    push_back(cogip_defs::Coords(
        center_.x() + (length_x_ / 2) * cos(DEG2RAD(center_.O())) - (length_y_ / 2) * sin(DEG2RAD(center_.O())),
        center_.y() + (length_x_ / 2) * sin(DEG2RAD(center_.O())) + (length_y_ / 2) * cos(DEG2RAD(center_.O()))
    ));
    push_back(cogip_defs::Coords(
        center_.x() - (length_x_ / 2) * cos(DEG2RAD(center_.O())) - (length_y_ / 2) * sin(DEG2RAD(center_.O())),
        center_.y() - (length_x_ / 2) * sin(DEG2RAD(center_.O())) + (length_y_ / 2) * cos(DEG2RAD(center_.O()))
    ));

    update_bounding_box();
}

void ObstacleRectangle::update_bounding_box()
{
    double length_x = length_x_ * (1 + OBSTACLE_BOUNDING_BOX_MARGIN);
    double length_y = length_y_ * (1 + OBSTACLE_BOUNDING_BOX_MARGIN);

    bounding_box_.push_back(cogip_defs::Coords(
        center_.x() - (length_x / 2) * cos(DEG2RAD(center_.O())) + (length_y / 2) * sin(DEG2RAD(center_.O())),
        center_.y() - (length_x / 2) * sin(DEG2RAD(center_.O())) - (length_y / 2) * cos(DEG2RAD(center_.O()))
    ));
    bounding_box_.push_back(cogip_defs::Coords(
        center_.x() + (length_x / 2) * cos(DEG2RAD(center_.O())) + (length_y / 2) * sin(DEG2RAD(center_.O())),
        center_.y() + (length_x / 2) * sin(DEG2RAD(center_.O())) - (length_y / 2) * cos(DEG2RAD(center_.O()))
    ));
    bounding_box_.push_back(cogip_defs::Coords(
        center_.x() + (length_x / 2) * cos(DEG2RAD(center_.O())) - (length_y / 2) * sin(DEG2RAD(center_.O())),
        center_.y() + (length_x / 2) * sin(DEG2RAD(center_.O())) + (length_y / 2) * cos(DEG2RAD(center_.O()))
    ));
    bounding_box_.push_back(cogip_defs::Coords(
        center_.x() - (length_x / 2) * cos(DEG2RAD(center_.O())) - (length_y / 2) * sin(DEG2RAD(center_.O())),
        center_.y() - (length_x / 2) * sin(DEG2RAD(center_.O())) + (length_y / 2) * cos(DEG2RAD(center_.O()))
    ));
}

} // namespace obstacles

} // namespace cogip
