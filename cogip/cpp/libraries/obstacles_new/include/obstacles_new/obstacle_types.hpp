// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @defgroup    lib_obstacles_new Obstacles module
/// @ingroup     lib
/// @brief       Obstacles module
///
/// An obstacle is a convex outline dilated by a corner radius, stored in a trivially copyable
/// structure so it can live in shared memory, and wrapped by a class that owns nothing but the
/// invariants of that outline.
///
/// @{
/// @file        obstacle_types.hpp
/// @brief       Declaration of obstacle_t, the storage representation of an obstacle, and of the
///              types and limits that come with it.
/// @author      Mathis Lécrivain <lecrivain.mathis@gmail.com>

#pragma once

#include "models/coords.hpp"
#include "models/pose.hpp"

#include <cstddef>
#include <cstdint>
#include <ostream>
#include <type_traits>

namespace cogip {

namespace obstacles_new {

/// Maximum number of vertices of an obstacle outline.
constexpr std::size_t OBSTACLE_OUTLINE_SIZE_MAX = 16;

/// Shape family of an obstacle.
///
/// Purely informative. The geometry is fully described by the outline and the corner radius, so no
/// algorithm needs to branch on this; it exists so display code can pick a representation without
/// re-deriving it from the vertex count.
enum class obstacle_kind_t : uint8_t {
    Circle = 0,     ///< One outline point, corner_radius > 0.
    Rectangle = 1,  ///< Four outline points, corner_radius == 0.
    Polygon = 2,    ///< Arbitrary convex outline, corner_radius == 0.
};

/// An obstacle is a convex outline dilated by a corner radius.
///
/// The outline is always stored counter-clockwise, and this is an invariant readers may rely on
/// rather than a convention they should re-check. It is established when the outline is stored,
/// see Obstacle::make_polygon().
typedef struct {
    uint32_t id;            ///< Optional identifier.
    obstacle_kind_t kind;   ///< Shape family, for display only.
    bool enabled;           ///< False when the obstacle must be ignored.
    uint8_t outline_count;  ///< Number of valid entries in outline.
    models::pose_t center;  ///< Rigid body reference point. Angle in degrees.
    double corner_radius;   ///< Dilation radius in mm. Zero means sharp edges.
    models::coords_t outline[OBSTACLE_OUTLINE_SIZE_MAX];  ///< Outline, absolute mm. Counter-clockwise.
} obstacle_t;

// This structure is meant to be mapped into POSIX shared memory, so it has to stay copyable byte
// by byte and keep a layout both processes agree on. A default member initialiser, a user provided
// constructor or a non trivial member would break that silently.
static_assert(std::is_trivial_v<obstacle_t>);
static_assert(std::is_standard_layout_v<obstacle_t>);
static_assert(std::is_trivially_copyable_v<obstacle_t>);

// Same guarantees for the borrowed members, so an upstream change in models is caught here rather
// than at run time in another process.
static_assert(std::is_trivial_v<models::pose_t>);
static_assert(std::is_standard_layout_v<models::pose_t>);
static_assert(std::is_trivial_v<models::coords_t>);
static_assert(std::is_standard_layout_v<models::coords_t>);

/// Overloads the stream insertion operator for `obstacle_t`.
/// @param os The output stream.
/// @param obstacle The obstacle to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const obstacle_t& obstacle) {
    os << "obstacle_t(id=" << obstacle.id
       << ", kind=" << static_cast<int>(obstacle.kind)
       << ", enabled=" << obstacle.enabled
       << ", center=" << obstacle.center
       << ", corner_radius=" << obstacle.corner_radius
       << ", outline_count=" << static_cast<int>(obstacle.outline_count)
       << ")";
    return os;
}

} // namespace obstacles_new

} // namespace cogip

/// @}
