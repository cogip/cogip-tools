// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "models/Coords.hpp"

#include <cmath>
#include <cstring>

namespace cogip {

namespace models {

Coords::Coords(coords_t* data):
    data_(data),
    external_data_(data != nullptr)
{
    initMemory();
}

Coords::Coords(double x, double y, coords_t* data):
    data_(nullptr),
    external_data_(data != nullptr)
{
    initMemory();
    data_->x = x;
    data_->y = y;
}

Coords::Coords(const Coords& other, bool deep_copy):
    data_(other.data_),
    external_data_(!deep_copy && other.external_data_)
{
    initMemory();
    if (!external_data_) {
        memcpy(data_, other.data_, sizeof(coords_t));
    }
}

Coords& Coords::operator=(const Coords& other)
{
    data_ = other.data_;
    external_data_ = other.external_data_;
    initMemory();
    if (!external_data_) {
        memcpy(data_, other.data_, sizeof(coords_t));
    }
    return *this;
}

Coords::~Coords()
{
    if (!external_data_) {
        delete data_;
    }
}

void Coords::initMemory() {
    if (!external_data_) {
        // Allocate memory if external pointer is not provided
        data_ = new coords_t();
    }
}

double Coords::distance(double x, double y) const
{
    return sqrt((x - this->x()) * (x - this->x())
                + (y - this->y()) * (y - this->y()));
}

bool Coords::on_segment(const Coords& a, const Coords& b) const
{
    bool res = false;

    if ((b.x() - a.x()) / (b.y() - a.y()) == (b.x() - x()) / (b.y() - y())) {
        if (a.x() < b.x()) {
            if ((x() < b.x()) && (x() > a.x())) {
                res = true;
            }
        }
        else {
            if ((x() < a.x()) && (x() > b.x())) {
                res = true;
            }
        }
    }
    return res;
}

} // namespace models

} // namespace cogip
