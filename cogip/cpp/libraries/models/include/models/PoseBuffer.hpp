// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       PoseBuffer declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "models/pose_buffer.hpp"
#include "models/Pose.hpp"

#include <ostream>

namespace cogip {

namespace models {

class PoseBuffer {
public:
    /// Constructor.
    PoseBuffer(
        pose_buffer_t* data      ///< [in] Pointer to an existing data structure
                                 ///<      If nullptr, will allocate one internally
    );

    /// Destructor
    ~PoseBuffer();

    /// Return the pointer to the underlying data structure.
    pose_buffer_t* data() { return data_; };

    /// Return head.
    double head() const { return data_->head; };

    /// Return tail.
    double tail() const { return data_->tail; };

    /// Return true if the buffer is full, false otherwise.
    double full() const { return data_->full; };

    /// Get the number of stored positions
    std::size_t size() const;

    /// Add a new pose to the buffer.
    void push(float x, float y, float angle);

    /// Get last pose pushed in the buffer.
    Pose last() const { return get(0); };

    /// Get the N-th position from head (0 is the most recent).
    Pose get(std::size_t n) const;

protected:
    pose_buffer_t* data_;   ///< pointer to internal data structure
    bool external_data_;    ///< Flag to indicate if memory is externally managed
};

/// Overloads the stream insertion operator for `PoseBuffer`.
/// Prints the PoseBuffer in a human-readable format.
/// @param os The output stream.
/// @param buffer The PoseBuffer to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const PoseBuffer& buffer) {
    os << "PoseBuffer(size=" << buffer.size() << "/" << POSE_BUFFER_SIZE_MAX << ", head=" << buffer.head() << ", tail=" << buffer.tail() << ")";
    return os;
}

} // namespace models

} // namespace cogip

/// @}
