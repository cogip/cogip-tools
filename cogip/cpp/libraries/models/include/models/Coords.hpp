// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       Coords declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "models/coords.hpp"

#include <ostream>

namespace cogip {

namespace models {

/// Absolute coordinates along X and Y axis
class Coords {
public:
    /// Constructor.
    Coords(
        coords_t* data           ///< [in] Pointer to an existing data structure
                                 ///<      If nullptr, will allocate one internally
    );

    /// Constructor with initial values.
    Coords(
        double x=0.0,            ///< [in] X coordinate
        double y=0.0,            ///< [in] Y coordinate
        coords_t* data=nullptr   ///< [in] Pointer to an existing data structure
                                 ///<      If nullptr, will allocate one internally
    );

    /// Copy constructor
    Coords(
        const Coords& other,     ///< [in] The Coords to copy
        bool deep_copy=false     ///< [in] If true, will perform a deep copy of the data
    );

    /// Assignment operator
    Coords& operator=(
        const Coords& other      ///< [in] The Coords to copy
    );

    /// Destructor
    ~Coords();

    /// Return the pointer to the underlying data structure.
    coords_t* data() { return data_; };

    /// Return X coordinate.
    virtual double x() const { return data_->x; };

    /// Return Y coordinate.
    virtual double y() const { return data_->y; };

    /// Set X coordinate.
    virtual void set_x(
        double x            ///< [in] new X coordinate
    ) { data_->x = x; };

    /// Set Y coordinate.
    virtual void set_y(
        double y            ///< [in] new Y coordinate
    ) { data_->y = y; };

    /// Compute the distance the destination Coords.
    double distance(
        double x,           ///< [in] X destination
        double y            ///< [in] Y destination
    ) const;

    double distance(
        const Coords& dest  ///< [in] destination
    ) const { return distance(dest.x(), dest.y()); };

    /// Check if this Coords is placed on a segment defined by two Coords A,B.
    /// @return true if on [AB], false otherwise
    bool on_segment(
        const Coords& a,    ///< [in] point A
        const Coords& b     ///< [in] point A
    ) const;

    /// Check if this Coords is equal to another.
    /// @return true if Coords are equal, false otherwise
    bool operator == (
        const Coords& other  ///< [in] Coords to compare
    ) const { return x() == other.x() && y() == other.y(); };

    /// Check if this Coords is equal to a coords_t.
    /// @return true if Coords and coords_t are equal, false otherwise
    bool operator == (
        const coords_t& other  ///< [in] point to compare
    ) const { return x() == other.x && y() == other.y; };

protected:
    void initMemory();

    coords_t* data_;        ///< pointer to internal data structure
    bool external_data_;    ///< Flag to indicate if memory is externally managed
};

/// Overloads the stream insertion operator for `Coords`.
/// Prints the Coords in a human-readable format.
/// @param os The output stream.
/// @param coords The Coords to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const Coords& coords) {
    os << "Coords(x=" << coords.x() << ", y=" << coords.y() << ")";
    return os;
}

} // namespace models

} // namespace cogip

/// @}
