// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "models/Polar.hpp"

#include <cstring>

namespace cogip {

namespace models {

Polar::Polar(polar_t *data):
    data_(data),
    external_data_(data != nullptr)
{
    initMemory();
}

Polar::Polar(double distance, double angle, polar_t *data):
    data_(data),
    external_data_(data != nullptr)
{
    initMemory();
    data_->distance = distance;
    data_->angle = angle;
}

Polar::Polar(const Polar& other, bool deep_copy):
    data_(other.data_),
    external_data_(!deep_copy && other.external_data_)
{
    initMemory();
    if (!external_data_) {
        memcpy(data_, other.data_, sizeof(polar_t));
    }
}

Polar& Polar::operator=(const Polar& other)
{
    data_ = other.data_;
    external_data_ = other.external_data_;
    initMemory();
    if (!external_data_) {
        memcpy(data_, other.data_, sizeof(polar_t));
    }
    return *this;
}

Polar::~Polar()
{
    if (!external_data_) {
        delete data_;
    }
}

void Polar::initMemory() {
    if (!external_data_) {
        // Allocate memory if external pointer is not provided
        data_ = new polar_t();
        data_->distance = 0.0;
        data_->angle = 0.0;
    }
}

} // namespace models

} // namespace cogip
