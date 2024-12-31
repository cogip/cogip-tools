// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       Pose class declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

// System includes
#include <cmath>

// Project includes
#include "models/pose.hpp"
#include "models/Coords.hpp"
#include "models/Polar.hpp"
#include "utils/trigonometry.hpp"

namespace cogip {

namespace models {

/// Pose in 2D space with an orientation.
class Pose : public Coords {
public:
    /// Constructor.
    Pose(
        pose_t *data             ///< [in] Pointer to an existing data structure
                                 ///<      If nullptr, will allocate one internally
    );

    /// Constructor with initial values.
    Pose(
        double x=0.0,            ///< [in] X coordinate
        double y=0.0,            ///< [in] Y coordinate
        double angle=0.0,        ///< [in] orientation
        pose_t *data=nullptr     ///< [in] Pointer to an existing data structure
                                 ///<      If nullptr, will allocate one internally
    );

    /// Copy constructor
    Pose(
        const Pose& other,       ///< [in] The Pose to copy
        bool deep_copy=false     ///< [in] If true, will perform a deep copy of the data
    );

    /// Assignment operator
    Pose& operator=(
        const Pose& other        ///< [in] The Coords to copy
    );


    /// Destructor.
    ~Pose();

    double x() const override { return data_->x; }
    void set_x(double x) override { data_->x = x; }

    double y() const override { return data_->y; }
    void set_y(double y) override { data_->y = y; }

    /// Return coordinates in a new Coords object.
    Coords coords() const { return Coords(x(), y()); };

    /// Set coordinates from Coords object.
    void set_coords(
        const Coords &coords  ///< [in] new coordinates
    ) { data_->x = coords.x(); data_->y = coords.y();};

    /// Return orientation.
    double angle(void) const { return data_->angle; };

    /// Set orientation.
    void set_angle(
        double angle              ///< [in] new 0-orientation
    ) { data_->angle = angle; };

    /// Check if this pose is equal to another.
    /// @return true if poses are equal, false otherwise
    bool operator == (
        const Pose& other      ///< [in] pose to compare
        ) const { return x() == other.x() && y() == other.y() && angle() == other.angle(); };

    Polar operator-(const Pose& p) const {
        double error_x = x() - p.x();
        double error_y = y() - p.y();
        double error_angle = utils::limit_angle_rad(atan2(error_y, error_x) - DEG2RAD(p.angle()));

        return Polar(
            sqrt(square(error_x) + square(error_y)),
            RAD2DEG(error_angle)
        );
    };

protected:
    void initMemory();

    pose_t* data_;        ///< pointer to internal data structure
    bool external_data_;    ///< Flag to indicate if memory is externally managed
};

/// Overloads the stream insertion operator for `Pose`.
/// Prints the pose in a human-readable format.
/// @param os The output stream.
/// @param pose The pose to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, Pose& pose) {
    pose.set_y(888);
    os << "Pose(x=" << pose.x() << ", y=" << pose.y() << ", angle=" << pose.angle() << ")";
    return os;
}

} // namespace cogip_defs

} // namespace cogip

/// @}
