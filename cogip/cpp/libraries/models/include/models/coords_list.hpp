// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       coords_list_t declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "models/coords.hpp"

#include <ostream>

namespace cogip {

namespace models {

constexpr std::size_t COORDS_LIST_SIZE_MAX = 256;

typedef struct {
    std::size_t count;
    coords_t elems[COORDS_LIST_SIZE_MAX];
} coords_list_t;

/// Overloads the stream insertion operator for `coords_list_t`.
/// Prints the coords_list_t in a human-readable format.
/// @param os The output stream.
/// @param coords_list The coords_list_t to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const coords_list_t& coords_list) {
    os << "coords_list_t(count=" << coords_list.count << ", coords=[";
    for (std::size_t i = 0; i < coords_list.count; ++i) {
        if (i > 0) os << ", ";
        os << coords_list.elems[i];
    }
    os << "])";
    return os;
}

} // namespace models

} // namespace cogip

/// @}
