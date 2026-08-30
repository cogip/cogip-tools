// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_obstacles_new
/// @{
/// @file        Obstacle.hpp
/// @brief       Obstacle class declaration.
/// @details     Thin non owning wrapper over an obstacle_t, holding data access, memory ownership
///              and the invariants of the stored outline. It carries no geometric predicate on
///              purpose: those belong to free functions over plain structures, which can be tested
///              without shared memory and without nanobind.
/// @author      Mathis Lécrivain <lecrivain.mathis@gmail.com>

#pragma once

#include "obstacles_new/obstacle_types.hpp"

#include <cstddef>
#include <cstdint>
#include <ostream>

namespace cogip {

namespace obstacles_new {

/// @class Obstacle
/// @brief Represents a single obstacle, whatever its shape.
///
/// @par Ownership
/// `data_` is either borrowed from the caller, typically a slot of a shared memory array, or
/// allocated here when the caller passes nullptr. `external_data_` records which case applies and
/// the destructor frees the structure only when this object owns it.
///
/// @par Why there is no vtable
/// A disc, a rectangle and a polygon are the same structure, so there is nothing left to dispatch.
/// Constructing this class costs a pointer and a boolean, which matters because the avoidance
/// visibility graph builds one wrapper per element access inside its hot loops.
class Obstacle final {
public:
    /// Build a disc.
    ///
    /// A disc is one point dilated by its radius, which is exact and keeps every reader of the
    /// structure free of a special case.
    ///
    /// @return The constructed obstacle.
    static Obstacle make_circle(
        double x,                 ///< [in] X coordinate of the centre, mm.
        double y,                 ///< [in] Y coordinate of the centre, mm.
        double radius,            ///< [in] Radius, mm.
        obstacle_t* data=nullptr  ///< [in] Pointer to an existing data structure.
                                  ///<      If nullptr, will allocate one internally.
    );

    /// Build a rectangle.
    ///
    /// Corners are laid out counter-clockwise from the bottom left one, so the winding invariant of
    /// obstacle_t holds by construction and nothing has to be checked here.
    ///
    /// @return The constructed obstacle.
    static Obstacle make_rectangle(
        double x,                 ///< [in] X coordinate of the centre, mm.
        double y,                 ///< [in] Y coordinate of the centre, mm.
        double angle,             ///< [in] Orientation angle, in degrees.
        double length_x,          ///< [in] Length along the local X axis, mm.
        double length_y,          ///< [in] Length along the local Y axis, mm.
        obstacle_t* data=nullptr  ///< [in] Pointer to an existing data structure.
                                  ///<      If nullptr, will allocate one internally.
    );

    /// Build an arbitrary polygon.
    ///
    /// This is the only constructor whose vertex order comes from the caller, so it is where the
    /// counter-clockwise winding invariant of obstacle_t is established. The shoelace sum over the
    /// outline is positive counter-clockwise and negative clockwise; only that sign is read, and
    /// the vertices are reversed when it is negative. Paying for it once here is what lets every
    /// later predicate read a cross product sign as inside or outside without re-deriving the
    /// winding. Fewer than three vertices bound no area, hence no winding to normalise.
    ///
    /// Convexity is checked here rather than trusted. It costs one pass over at most sixteen
    /// vertices, on a path walked once per obstacle update, whereas a concave outline fails
    /// silently: its inflated hull is wrong where it turns inwards, so the planner routes through
    /// the obstacle instead of around it. The check rejects a shape that turns both ways; it does
    /// not rule out a self-intersecting one.
    ///
    /// @return The constructed obstacle.
    /// @throws std::runtime_error if @p count is zero or above OBSTACLE_OUTLINE_SIZE_MAX, or if
    ///         the outline is not convex.
    static Obstacle make_polygon(
        const models::coords_t* points,  ///< [in] Vertices, absolute mm. Not owned.
        std::size_t count,               ///< [in] Number of vertices.
        obstacle_t* data=nullptr         ///< [in] Pointer to an existing data structure.
                                         ///<      If nullptr, will allocate one internally.
    );

    /// Constructor.
    explicit Obstacle(
        obstacle_t* data=nullptr  ///< [in] Pointer to an existing data structure.
                                  ///<      If nullptr, will allocate one internally.
    );

    /// Copy constructor.
    Obstacle(
        const Obstacle& other,  ///< [in] The obstacle to copy.
        bool deep_copy=false    ///< [in] If true, copy the data structure instead of sharing it.
    );

    /// Move constructor.
    ///
    /// Required for obstacles to be stored by value in a standard container. The copy constructor
    /// shares the data structure rather than duplicating it when deep_copy is false, so a vector
    /// reallocation would copy-construct aliases and then destroy the originals, freeing the
    /// structure the aliases still point at. Moving transfers ownership instead, and the noexcept
    /// is what makes the container prefer it over the copy.
    Obstacle(Obstacle&& other) noexcept;

    /// An obstacle wraps a pointer it may own, so assignment would either alias or double free.
    /// Copy construction, which takes an explicit deep_copy flag, is the supported way.
    Obstacle& operator=(const Obstacle&) = delete;
    Obstacle& operator=(Obstacle&&) = delete;

    /// Destructor. Releases the data structure unless it is externally managed.
    ~Obstacle();

    /// Return the pointer to the underlying data structure.
    ///
    /// @warning Writing to center or outline through this pointer bypasses set_center() and leaves
    ///          the two inconsistent.
    obstacle_t* data() { return data_; };
    const obstacle_t* data() const { return data_; };

    /// Return obstacle id.
    uint32_t id() const { return data_->id; };

    /// Set obstacle id.
    void set_id(uint32_t id) { data_->id = id; };

    /// Return the shape family.
    obstacle_kind_t kind() const { return data_->kind; };

    /// Return true if the obstacle must be taken into account.
    bool enabled() const { return data_->enabled; };

    /// Enable or disable the obstacle.
    void set_enabled(bool enabled) { data_->enabled = enabled; };

    /// Return the dilation radius, in mm.
    double corner_radius() const { return data_->corner_radius; };

    /// Return the rigid body reference point.
    const models::pose_t& center() const { return data_->center; };

    /// Move the obstacle to a new centre, carrying its outline along.
    ///
    /// The obstacle is displaced as a rigid body: the outline is rotated around the previous centre
    /// by the angle difference, then translated. Writing only the centre would leave the outline
    /// behind, and the obstacle would keep reporting collisions where it no longer is.
    void set_center(
        const models::pose_t& center  ///< [in] New centre. Angle in degrees.
    );

    /// Return the number of outline vertices.
    std::size_t point_count() const { return data_->outline_count; };

    /// Return an outline vertex.
    /// @throws std::runtime_error if @p index is out of range.
    const models::coords_t& point(
        std::size_t index  ///< [in] Vertex index.
    ) const;

private:
    obstacle_t* data_;    ///< Pointer to internal data structure.
    bool external_data_;  ///< Flag to indicate if memory is externally managed.
};

/// Overloads the stream insertion operator for `Obstacle`.
/// @param os The output stream.
/// @param obstacle The obstacle to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const Obstacle& obstacle) {
    os << "Obstacle(" << *obstacle.data() << ")";
    return os;
}

} // namespace obstacles_new

} // namespace cogip

/// @}
