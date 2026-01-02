// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "models/PoseOrderList.hpp"

namespace cogip {

namespace models {

void PoseOrderList::append(
    double x,
    double y,
    double angle,
    std::uint8_t max_speed_linear,
    std::uint8_t max_speed_angular,
    MotionDirection motion_direction,
    bool bypass_anti_blocking,
    bool bypass_final_orientation,
    std::uint32_t timeout_ms,
    bool is_intermediate,
    double stop_before_distance
)
{
    if (size() >= max_size()) {
        throw std::runtime_error("PoseOrderList is full");
    }
    list_->elems[list_->count].x = x;
    list_->elems[list_->count].y = y;
    list_->elems[list_->count].angle = angle;
    list_->elems[list_->count].max_speed_linear = max_speed_linear;
    list_->elems[list_->count].max_speed_angular = max_speed_angular;
    list_->elems[list_->count].motion_direction = motion_direction;
    list_->elems[list_->count].bypass_anti_blocking = bypass_anti_blocking;
    list_->elems[list_->count].bypass_final_orientation = bypass_final_orientation;
    list_->elems[list_->count].timeout_ms = timeout_ms;
    list_->elems[list_->count].is_intermediate = is_intermediate;
    list_->elems[list_->count].stop_before_distance = stop_before_distance;
    list_->count++;
}

void PoseOrderList::set(
    std::size_t index,
    double x,
    double y,
    double angle,
    std::uint8_t max_speed_linear,
    std::uint8_t max_speed_angular,
    MotionDirection motion_direction,
    bool bypass_anti_blocking,
    bool bypass_final_orientation,
    std::uint32_t timeout_ms,
    bool is_intermediate,
    double stop_before_distance
) {
    if (index >= size()) {
        throw std::runtime_error("index out of range");
    }
    list_->elems[index].x = x;
    list_->elems[index].y = y;
    list_->elems[index].angle = angle;
    list_->elems[index].max_speed_linear = max_speed_linear;
    list_->elems[index].max_speed_angular = max_speed_angular;
    list_->elems[index].motion_direction = motion_direction;
    list_->elems[index].bypass_anti_blocking = bypass_anti_blocking;
    list_->elems[index].bypass_final_orientation = bypass_final_orientation;
    list_->elems[index].timeout_ms = timeout_ms;
    list_->elems[index].is_intermediate = is_intermediate;
    list_->elems[index].stop_before_distance = stop_before_distance;
}

} // namespace models

} // namespace cogip
