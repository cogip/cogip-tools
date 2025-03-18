// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       circle_list_t declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "models/circle.hpp"

#include <ostream>

namespace cogip {

namespace models {

constexpr std::size_t CIRCLE_LIST_SIZE_MAX = 1024;

typedef struct {
    std::size_t count;
    circle_t elems[CIRCLE_LIST_SIZE_MAX];
} circle_list_t;

/// Overloads the stream insertion operator for `circle_list_t`.
/// Prints the circle_list_t in a human-readable format.
/// @param os The output stream.
/// @param circle_list The circle_list_t to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const circle_list_t& circle_list) {
    os << "circle_list_t(count=" << circle_list.count << ", circle=[";
    for (std::size_t i = 0; i < circle_list.count; ++i) {
        if (i > 0) os << ", ";
        os << circle_list.elems[i];
    }
    os << "])";
    return os;
}

} // namespace models

} // namespace cogip

/// @}
