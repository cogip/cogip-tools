// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       Circle class declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

// System includes
#include <cmath>

// Project includes
#include "models/circle.hpp"
#include "models/Coords.hpp"

namespace cogip {

namespace models {

/// Circle in 2D space.
class Circle : public Coords {
public:
    /// Constructor.
    Circle(
        circle_t *data           ///< [in] Pointer to an existing data structure
                                 ///<      If nullptr, will allocate one internally
    );

    /// Constructor with initial values.
    Circle(
        double x=0.0,            ///< [in] X coordinate
        double y=0.0,            ///< [in] Y coordinate
        double angle=0.0,        ///< [in] radius
        circle_t *data=nullptr   ///< [in] Pointer to an existing data structure
                                 ///<      If nullptr, will allocate one internally
    );

    /// Copy constructor
    Circle(
        const Circle& other,     ///< [in] The Circle to copy
        bool deep_copy=false     ///< [in] If true, will perform a deep copy of the data
    );

    /// Assignment operator
    Circle& operator=(
        const Circle& other        ///< [in] The Circle to copy
    );


    /// Destructor.
    ~Circle();

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
    double radius(void) const { return data_->radius; };

    /// Set radius.
    void set_radius(
        double radius              ///< [in] new radius
    ) { data_->radius = radius; };

    /// Check if this circle is equal to another.
    /// @return true if circles are equal, false otherwise
    bool operator == (
        const Circle& other      ///< [in] circle to compare
        ) const { return x() == other.x() && y() == other.y() && radius() == other.radius(); };

    /// Check if this Circle is equal to a circle_t.
    /// @return true if Circle and circle_t are equal, false otherwise
    bool operator == (
        const circle_t& other  ///< [in] circle to compare
    ) const { return x() == other.x && y() == other.y && radius() == other.radius; };


protected:
    void initMemory();

    circle_t* data_;        ///< pointer to internal data structure
    bool external_data_;    ///< Flag to indicate if memory is externally managed
};

/// Overloads the stream insertion operator for `Circle`.
/// Prints the circle in a human-readable format.
/// @param os The output stream.
/// @param circle The circle to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, Circle& circle) {
    circle.set_y(888);
    os << "Circle(x=" << circle.x() << ", y=" << circle.y() << ", radius=" << circle.radius() << ")";
    return os;
}

} // namespace cogip_defs

} // namespace cogip

/// @}
