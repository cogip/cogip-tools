// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "models/PoseOrder.hpp"

// System includes
#include <cmath>
#include <cstring>
#include <iostream>

namespace cogip {

namespace models {

PoseOrder::PoseOrder(pose_order_t *data):
    data_(data),
    external_data_(data != nullptr)
{
    initMemory();
}

PoseOrder::PoseOrder(
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
    pose_order_t *data
):
    data_(data),
    external_data_(data != nullptr)
{
    initMemory();
    data_->x = x;
    data_->y = y;
    data_->angle = angle;
    data_->max_speed_linear = max_speed_linear;
    data_->max_speed_angular = max_speed_angular;
    data_->motion_direction = motion_direction;
    data_->bypass_anti_blocking = bypass_anti_blocking;
    data_->bypass_final_orientation = bypass_final_orientation;
    data_->timeout_ms = timeout_ms;
    data_->is_intermediate = is_intermediate;
}

PoseOrder::PoseOrder(const PoseOrder& other, bool deep_copy):
    data_(other.data_),
    external_data_(!deep_copy && other.external_data_)
{
    initMemory();
    if (!external_data_) {
        memcpy(data_, other.data_, sizeof(pose_order_t));
    }
}

PoseOrder& PoseOrder::operator=(const PoseOrder& other)
{
    external_data_ = other.external_data_;
    initMemory();
    if (!external_data_) {
        memcpy(data_, other.data_, sizeof(pose_order_t));
    }
    else {
        data_ = other.data_;
    }
    return *this;
}

PoseOrder::~PoseOrder()
{
    if (!external_data_) {
        delete data_;
    }
}

void PoseOrder::initMemory() {
    if (!external_data_) {
        // Allocate memory if external pointer is not provided
        data_ = new pose_order_t();
    }
}

} // namespace models

} // namespace cogip
