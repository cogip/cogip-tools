// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       PoseOrderList declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "models/pose_order_list.hpp"
#include "models/PoseOrder.hpp"
#include "models/List.hpp"

#include <ostream>

namespace cogip {

namespace models {

class PoseOrderList: public List<pose_order_t, PoseOrder, pose_order_list_t, POSE_ORDER_LIST_SIZE_MAX> {
public:
    PoseOrderList(pose_order_list_t* list = nullptr) : List(list) {};
    void append(
        double x,
        double y,
        double angle = 0.0,
        std::uint8_t max_speed_linear = 66,
        std::uint8_t max_speed_angular = 66,
        bool allow_reverse = true,
        bool bypass_anti_blocking = false,
        bool bypass_final_orientation = false,
        std::uint32_t timeout_ms = 0,
        bool is_intermediate = false
    );
    void append(const pose_order_t* elem) {
        append(
            elem->x,
            elem->y,
            elem->angle,
            elem->max_speed_linear,
            elem->max_speed_angular,
            elem->allow_reverse,
            elem->bypass_anti_blocking,
            elem->bypass_final_orientation,
            elem->timeout_ms,
            elem->is_intermediate
        );
    };
    void append(const PoseOrder& elem) {
        append(
            elem.x(),
            elem.y(),
            elem.angle(),
            elem.max_speed_linear(),
            elem.max_speed_angular(),
            elem.allow_reverse(),
            elem.bypass_anti_blocking(),
            elem.bypass_final_orientation(),
            elem.timeout_ms(),
            elem.is_intermediate()
        );
    };
    void set(
        std::size_t index,
        double x,
        double y,
        double angle = 0.0,
        std::uint8_t max_speed_linear = 66,
        std::uint8_t max_speed_angular = 66,
        bool allow_reverse = true,
        bool bypass_anti_blocking = false,
        bool bypass_final_orientation = false,
        std::uint32_t timeout_ms = 0,
        bool is_intermediate = false
    );
    void set(std::size_t index, const pose_order_t* elem) {
        set(
            index,
            elem->x,
            elem->y,
            elem->angle,
            elem->max_speed_linear,
            elem->max_speed_angular,
            elem->allow_reverse,
            elem->bypass_anti_blocking,
            elem->bypass_final_orientation,
            elem->timeout_ms,
            elem->is_intermediate
        );
    };
    void set(std::size_t index, const PoseOrder& elem) {
        set(
            index,
            elem.x(),
            elem.y(),
            elem.angle(),
            elem.max_speed_linear(),
            elem.max_speed_angular(),
            elem.allow_reverse(),
            elem.bypass_anti_blocking(),
            elem.bypass_final_orientation(),
            elem.timeout_ms(),
            elem.is_intermediate()
        );
    };
};

/// Overloads the stream insertion operator for `PoseOrderList`.
/// Prints the PoseOrderList in a human-readable format.
/// @param os The output stream.
/// @param pose_order_list The PoseOrderList to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, PoseOrderList& pose_order_list) {
    os << "PoseOrderList(count=" << pose_order_list.size() << ", pose_orders=[";
    for (std::size_t i = 0; i < pose_order_list.size(); ++i) {
        if (i > 0) os << ", ";
        os << pose_order_list.get(i);
    }
    os << "])";
    return os;
}

} // namespace models

} // namespace cogip

/// @}
