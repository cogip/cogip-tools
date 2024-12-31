// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       NbSharedArrayIterator class template declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include <nanobind/nanobind.h>

namespace nb = nanobind;
using namespace nb::literals;

namespace cogip {

namespace models {

/// @class NbSharedArrayIterator
/// @brief An iterator class used to generate bindings for classes with custom iterators.
/// @tparam DataType The type of data to be iterated over.
/// @tparam ArrayType The type of the array being iterated over.
template<typename DataType, typename ArrayType> class NbSharedArrayIterator {
public:
    /// Constructs an iterator for the given array starting at the specified index.
    /// @param array The array to iterate over.
    /// @param index The starting index for the iteration.
    NbSharedArrayIterator(ArrayType& array, std::size_t index) : array_(array), index_(index) {}

    /// Returns the next element in the array.
    /// @return DataType The next element in the array.
    /// @throws nb::stop_iteration if the end of the array is reached.
    DataType next() {
        if (index_ >= array_.size()) {
            throw nb::stop_iteration();  // Raise StopIteration in Python
        }
        return DataType(array_[index_++]);
    }

private:
    ArrayType& array_;  ///< Reference to the array being iterated over.
    std::size_t index_; ///< Current index in the array.
};

} // namespace models

} // namespace cogip

/// @}
