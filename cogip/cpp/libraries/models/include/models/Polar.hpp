// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       Polar class declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "models/polar.hpp"

#include <ostream>

namespace cogip {

namespace models {

/// Polar coordinate
class Polar {
public:
    /// Constructor.
    Polar(
        polar_t *data          ///< [in] Pointer to an existing data structure
                               ///<      If nullptr, will allocate one internally
    );

    /// Constructor with initial values.
    Polar(
        double distance = 0.0, ///< [in] distance
        double angle = 0.0,    ///< [in] angle
        polar_t *data=nullptr  ///< [in] Pointer to an existing data structure
                               ///<      If nullptr, will allocate one internally
    );

    /// Copy constructor
    Polar(
        const Polar& other,    ///< [in] The Polar to copy
        bool deep_copy=false   ///< [in] If true, will perform a deep copy of the data
    );

    /// Assignment operator
    Polar& operator=(
        const Polar& other      ///< [in] The Coords to copy
    );

    /// Destructor.
    ~Polar();

    /// Return distance.
    double distance(void) const { return data_->distance; };

    /// Return angle.
    double angle(void) const { return data_->angle; };

    /// Set distance.
    void set_distance(
        double distance        ///< [in] new distance
        ) { data_->distance = distance; };

    /// Set angle.
    void set_angle(
        double angle           ///< [in] new angle
        ) { data_->angle = angle; };

    /// Reverse distance
    void reverse_distance() {
        data_->distance *= -1;
    }

    /// Reverse angle
    void reverse_angle() {
        if (data_->angle < 0) {
            data_->angle += 180;
        }
        else {
            data_->angle -= 180;
        }
    };

    /// Reverse distance and angle
    void reverse() {
        reverse_distance();
        reverse_angle();
    };

private:
    void initMemory();

    polar_t* data_;        ///< pointer to internal data structure
    bool external_data_;    ///< Flag to indicate if memory is externally managed
};

/// Overloads the stream insertion operator for `Polar`.
/// Prints the polar in a human-readable format.
/// @param os The output stream.
/// @param polar The polar to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const Polar& polar) {
    os << "Polar(distance=" << polar.distance() << ", angle=" << polar.angle() << ")";
    return os;
}

} // namespace models

} // namespace cogip

/// @}
