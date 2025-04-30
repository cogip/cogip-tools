// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       CircleList declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "models/circle_list.hpp"
#include "models/Circle.hpp"
#include "models/List.hpp"

#include <ostream>

namespace cogip {

namespace models {

class CircleList: public List<circle_t, Circle, circle_list_t, CIRCLE_LIST_SIZE_MAX> {
public:
    CircleList(circle_list_t* list = nullptr) : List(list) {};
    void append(double x, double y, double radius = 0.0);
    void append(const circle_t* elem) { append(elem->x, elem->y); };
    void append(const Circle& elem) { append(elem.x(), elem.y()); };
    void set(std::size_t index, double x, double y, double radius = 0.0);
    void set(std::size_t index, const circle_t* elem) { set(index, elem->x, elem->y); };
    void set(std::size_t index, const Circle& elem) { set(index, elem.x(), elem.y()); };
};

/// Overloads the stream insertion operator for `CircleList`.
/// Prints the CircleList in a human-readable format.
/// @param os The output stream.
/// @param circle_list The CircleList to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, CircleList& circle_list) {
    os << "CircleList(count=" << circle_list.size() << ", circle=[";
    for (std::size_t i = 0; i < circle_list.size(); ++i) {
        if (i > 0) os << ", ";
        os << circle_list.get(i);
    }
    os << "])";
    return os;
}

} // namespace models

} // namespace cogip

/// @}
