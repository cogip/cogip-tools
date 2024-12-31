// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       CoordsList declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "models/coords_list.hpp"
#include "models/Coords.hpp"
#include "models/List.hpp"

#include <ostream>

namespace cogip {

namespace models {

class CoordsList: public List<coords_t, Coords, coords_list_t, COORDS_LIST_SIZE_MAX> {
public:
    CoordsList(coords_list_t* list = nullptr) : List(list) {};
    void append(double x, double y);
    void append(const coords_t* elem) { append(elem->x, elem->y); };
    void append(const Coords& elem) { append(elem.x(), elem.y()); };
    void set(std::size_t index, double x, double y);
    void set(std::size_t index, const coords_t* elem) { set(index, elem->x, elem->y); };
    void set(std::size_t index, const Coords& elem) { set(index, elem.x(), elem.y()); };
};

/// Overloads the stream insertion operator for `CoordsList`.
/// Prints the CoordsList in a human-readable format.
/// @param os The output stream.
/// @param coords_list The CoordsList to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, CoordsList& coords_list) {
    os << "CoordsList(count=" << coords_list.size() << ", coords=[";
    for (std::size_t i = 0; i < coords_list.size(); ++i) {
        if (i > 0) os << ", ";
        os << coords_list.get(i);
    }
    os << "])";
    return os;
}

} // namespace models

} // namespace cogip

/// @}
