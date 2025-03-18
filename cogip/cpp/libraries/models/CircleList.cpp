// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "models/CircleList.hpp"

namespace cogip {

namespace models {

void CircleList::append(double x, double y, double radius)
{
    if (size() >= max_size()) {
        throw std::runtime_error("CircleList is full");
    }
    list_->elems[list_->count].x = x;
    list_->elems[list_->count].y = y;
    list_->elems[list_->count].radius = radius;
    list_->count++;
}

void CircleList::set(std::size_t index, double x, double y, double radius) {
    if (index >= size()) {
        throw std::runtime_error("index out of range");
    }
    list_->elems[index].x = x;
    list_->elems[index].y = y;
    list_->elems[list_->count].radius = radius;
}

} // namespace models

} // namespace cogip
