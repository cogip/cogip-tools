// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_models
/// @{
/// @file
/// @brief       List class declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include <cstddef>
#include <stdexcept>

namespace cogip {

namespace models {

template<
    typename ElemTypeC,
    typename ElemTypeCpp,
    typename ArrayType,
    std::size_t LIST_SIZE_MAX
>
class List {
public:
    /// Constructor.
    /// @param list Pointer to an existing data structure.
    List(ArrayType* list = nullptr):
        list_(list),
        external_data_(list != nullptr)
    {
        if (!external_data_) {
            // Allocate memory if external pointer is not provided
            list_ = new ArrayType();
        }
    };

    /// Destructor.
    ~List()
    {
        if (!external_data_) {
            delete list_;
        }
    };

    void clear() { list_->count = 0; };

    std::size_t size() const { return list_->count; };

    std::size_t max_size() const { return LIST_SIZE_MAX; };

    ElemTypeC* get_data(std::size_t index) {
        if (index >= size()) {
            throw std::runtime_error("index out of range");
        }
        return &list_->elems[index];
    };

    ElemTypeCpp get(std::size_t index) { return ElemTypeCpp(get_data(index)); };

    ElemTypeCpp operator[](std::size_t index) { return get(index); }

    int getIndex(const ElemTypeCpp &elem) const {
        for (std::size_t i{0}; i < size(); ++i) {
            if (elem == list_->elems[i]) {
                return i;
            }
        }
        return -1;
    };

    // Iterator class
    class Iterator {
    public:
        Iterator(ElemTypeC* ptr) : ptr_(ptr) {}
        Iterator operator++() { ++ptr_; return *this; }
        bool operator!=(const Iterator& other) const { return ptr_ != other.ptr_; }
        const ElemTypeCpp operator*() const { return ElemTypeCpp(ptr_); }

    protected:
        ElemTypeC* ptr_;
    };

    // Iterator methods
    Iterator begin() { return Iterator(&list_->elems[0]); }
    Iterator end() { return Iterator(&list_->elems[list_->count]); }
    Iterator begin() const { return Iterator(&list_->elems[0]); }
    Iterator end() const { return Iterator(&list_->elems[list_->count]); }

protected:
    ArrayType* list_;        ///< pointer to internal data structure
    bool external_data_;     ///< Flag to indicate if memory is externally managed
};

} // namespace models

} // namespace cogip

/// @}
