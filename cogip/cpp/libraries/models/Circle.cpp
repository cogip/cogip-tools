// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "models/Circle.hpp"

// System includes
#include <cmath>
#include <cstring>
#include <iostream>

namespace cogip {

namespace models {

Circle::Circle(circle_t *data):
    data_(data),
    external_data_(data != nullptr)
{
    initMemory();
    Coords::data_ = nullptr;
    Coords::external_data_ = true;
}

Circle::Circle(double x, double y, double radius, circle_t *data):
    data_(data),
    external_data_(data != nullptr)
{
    initMemory();
    Coords::data_ = nullptr;
    Coords::external_data_ = true;
    data_->x = x;
    data_->y = y;
    data_->radius = radius;
}

Circle::Circle(const Circle& other, bool deep_copy):
    data_(other.data_),
    external_data_(!deep_copy && other.external_data_)
{
    initMemory();
    Coords::data_ = nullptr;
    Coords::external_data_ = true;
    if (!external_data_) {
        memcpy(data_, other.data_, sizeof(circle_t));
    }
}

Circle& Circle::operator=(const Circle& other)
{
    data_ = other.data_;
    external_data_ = other.external_data_;
    initMemory();
    Coords::data_ = nullptr;
    Coords::external_data_ = true;
    if (!external_data_) {
        memcpy(data_, other.data_, sizeof(circle_t));
    }
    return *this;
}

Circle::~Circle()
{
    if (!external_data_) {
        delete data_;
    }
}

void Circle::initMemory() {
    if (!external_data_) {
        // Allocate memory if external pointer is not provided
        data_ = new circle_t();
    }
}

} // namespace models

} // namespace cogip
