// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "models/CoordsList.hpp"

namespace cogip {

namespace models {

void CoordsList::append(double x, double y)
{
    if (size() >= max_size()) {
        throw std::runtime_error("CoordsList is full");
    }
    list_->elems[list_->count].x = x;
    list_->elems[list_->count].y = y;
    list_->count++;
}

void CoordsList::set(std::size_t index, double x, double y) {
    if (index >= size()) {
        throw std::runtime_error("index out of range");
    }
    list_->elems[index].x = x;
    list_->elems[index].y = y;
}

} // namespace models

} // namespace cogip
