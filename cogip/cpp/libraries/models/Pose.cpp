// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "models/Pose.hpp"

// System includes
#include <cmath>
#include <cstring>
#include <iostream>

namespace cogip {

namespace models {

Pose::Pose(pose_t *data):
    data_(data),
    external_data_(data != nullptr)
{
    initMemory();
    Coords::data_ = nullptr;
    Coords::external_data_ = true;
}

Pose::Pose(double x, double y, double angle, pose_t *data):
    data_(data),
    external_data_(data != nullptr)
{
    initMemory();
    Coords::data_ = nullptr;
    Coords::external_data_ = true;
    data_->x = x;
    data_->y = y;
    data_->angle = angle;
}

Pose::Pose(const Pose& other, bool deep_copy):
    data_(other.data_),
    external_data_(!deep_copy && other.external_data_)
{
    initMemory();
    Coords::data_ = nullptr;
    Coords::external_data_ = true;
    if (!external_data_) {
        memcpy(data_, other.data_, sizeof(pose_t));
    }
}

Pose& Pose::operator=(const Pose& other)
{
    data_ = other.data_;
    external_data_ = other.external_data_;
    initMemory();
    Coords::data_ = nullptr;
    Coords::external_data_ = true;
    if (!external_data_) {
        memcpy(data_, other.data_, sizeof(pose_t));
    }
    return *this;
}

Pose::~Pose()
{
    if (!external_data_) {
        delete data_;
    }
}

void Pose::initMemory() {
    if (!external_data_) {
        // Allocate memory if external pointer is not provided
        data_ = new pose_t();
    }
}

} // namespace models

} // namespace cogip
