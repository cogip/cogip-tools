// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       pose_buffer_t class declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "models/pose.hpp"

#include <ostream>

namespace cogip {

namespace models {

constexpr std::size_t POSE_BUFFER_SIZE_MAX = 256;

/// A circular buffer to store pose_t.
typedef struct {
    pose_t poses[POSE_BUFFER_SIZE_MAX];  ///< Poses list
    size_t head;                         ///< Next write pose
    size_t tail;                         ///< Oldest pose
    bool full;                           ///< Indicates if the buffer is full
} pose_buffer_t;

/// Overloads the stream insertion operator for `pose_buffer_t`.
/// Prints the pose in a human-readable format.
/// @param os The output stream.
/// @param buffer The buffer to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const pose_buffer_t& buffer) {
        size_t size = 0;
        if (buffer.head >= buffer.tail){
            size = buffer.head - buffer.tail;
        }
        else {
            size = POSE_BUFFER_SIZE_MAX + buffer.head - buffer.tail;
        }

    os << "pose_buffer_t(size=" << size << "/" << POSE_BUFFER_SIZE_MAX << ", head=" << buffer.head << ", tail=" << buffer.tail << ")";
    return os;
}

} // namespace cogip_defs

} // namespace cogip

/// @}
