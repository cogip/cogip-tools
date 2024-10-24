
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
        center.x() - (length_x_ / 2) * cos(DEG2RAD(center.O())) + (length_y_ / 2) * sin(DEG2RAD(center.O())),
        center.y() - (length_x_ / 2) * sin(DEG2RAD(center.O())) - (length_y_ / 2) * cos(DEG2RAD(center.O()))
    ));
    push_back(cogip_defs::Coords(
        center.x() + (length_x_ / 2) * cos(DEG2RAD(center.O())) + (length_y_ / 2) * sin(DEG2RAD(center.O())),
        center.y() + (length_x_ / 2) * sin(DEG2RAD(center.O())) - (length_y_ / 2) * cos(DEG2RAD(center.O()))
    ));
    push_back(cogip_defs::Coords(
        center.x() + (length_x_ / 2) * cos(DEG2RAD(center.O())) - (length_y_ / 2) * sin(DEG2RAD(center.O())),
        center.y() + (length_x_ / 2) * sin(DEG2RAD(center.O())) + (length_y_ / 2) * cos(DEG2RAD(center.O()))
    ));
    push_back(cogip_defs::Coords(
        center.x() - (length_x_ / 2) * cos(DEG2RAD(center.O())) - (length_y_ / 2) * sin(DEG2RAD(center.O())),
        center.y() - (length_x_ / 2) * sin(DEG2RAD(center.O())) + (length_y_ / 2) * cos(DEG2RAD(center.O()))
    ));

    for (const auto & point: *this) {
        bounding_box_.push_back(point);
    }
}

} // namespace obstacles

} // namespace cogip
