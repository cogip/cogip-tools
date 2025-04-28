// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "models/PoseBuffer.hpp"

#include <cmath>
#include <cstring>

namespace cogip {

namespace models {

PoseBuffer::PoseBuffer(pose_buffer_t* data):
    data_(data),
    external_data_(data != nullptr)
{
    if (!external_data_) {
        // Allocate memory if external pointer is not provided
        data_ = new pose_buffer_t();
    }
    data_->head = 0;
    data_->tail = 0;
    data_->full = false;

}

PoseBuffer::~PoseBuffer()
{
    if (!external_data_) {
        delete data_;
    }
};

std::size_t PoseBuffer::size() const
{
    if (data_->full) return POSE_BUFFER_SIZE_MAX;
    if (data_->head >= data_->tail) return data_->head - data_->tail;
    return POSE_BUFFER_SIZE_MAX + data_->head - data_->tail;
};

void PoseBuffer::push(float x, float y, float angle)
{
    data_->poses[data_->head].x = x;
    data_->poses[data_->head].y = y;
    data_->poses[data_->head].angle = angle;
    if (data_->full) {
        data_->tail = (data_->tail + 1) % POSE_BUFFER_SIZE_MAX; // Advance tail if full
    }
    data_->head = (data_->head + 1) % POSE_BUFFER_SIZE_MAX;
    data_->full = (data_->head == data_->tail);
};

Pose PoseBuffer::get(std::size_t n) const
{
    if (n >= size()) {
        throw std::out_of_range("Requested index is out of bounds.");
    }

    // Calculate index relative to head (reverse order)
    size_t index = (data_->head + POSE_BUFFER_SIZE_MAX - 1 - n) % POSE_BUFFER_SIZE_MAX;
    return Pose(&data_->poses[index]);
};

} // namespace models

} // namespace cogip
