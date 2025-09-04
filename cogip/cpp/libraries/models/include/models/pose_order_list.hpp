// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       pose_order_list_t declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "models/pose_order.hpp"

#include <ostream>

namespace cogip {

namespace models {

constexpr std::size_t POSE_ORDER_LIST_SIZE_MAX = 32;

typedef struct {
    std::size_t count;
    pose_order_t elems[POSE_ORDER_LIST_SIZE_MAX];
} pose_order_list_t;

/// Overloads the stream insertion operator for `pose_order_list_t`.
/// Prints the pose_order_list_t in a human-readable format.
/// @param os The output stream.
/// @param pose_order_list The pose_order_list_t to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const pose_order_list_t& pose_order_list) {
    os << "pose_order_list_t(count=" << pose_order_list.count << ", pose_orders=[";
    for (std::size_t i = 0; i < pose_order_list.count; ++i) {
        if (i > 0) os << ", ";
        os << pose_order_list.elems[i];
    }
    os << "])";
    return os;
}

} // namespace models

} // namespace cogip

/// @}
