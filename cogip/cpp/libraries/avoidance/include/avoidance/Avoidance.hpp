// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level
// directory for more details.

/// @defgroup    lib_avoidance Avoidance module
/// @ingroup     lib
/// @brief       Avoidance module
///
/// The Avoidance module is responsible for computing paths that avoid obstacles.
/// It operates in two main phases:
/// 1. **Graph Building:** Use `avoidance()` to create a graph representing valid paths.
/// 2. **Path Retrieval:** Access specific poses in the computed path using `get_path_pose()`.
///
/// The module can also periodically check if a direct path to the destination becomes available using `check_recompute()`.
///
/// @{
/// @file
/// @brief       Public API for the Avoidance module.
/// @author      Gilles DOFFE <g.doffe@gmail.com>

#pragma once

/// Standard includes
#include <cstdint>
#include <deque>
#include <map>
#include <mutex>
#include <set>
#include <vector>

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>

/// Project includes
#include "models/Coords.hpp"
#include "obstacles/ObstaclePolygon.hpp"
#include "shared_memory/SharedMemory.hpp"

namespace nb = nanobind;

namespace cogip {

namespace avoidance {

/// @brief Class managing the avoidance algorithm and graph representation.
class Avoidance
{
public:
    static constexpr uint32_t max_distance = UINT32_MAX; ///< Maximum distance used for Dijkstra's algorithm.

    /// @brief Constructor initializing the avoidance system with obstacle borders.
    /// @param name Name of the shared memory segment.
    Avoidance(const std::string& name);

    /// @brief Checks if a point is inside any obstacle.
    /// @param point The coordinates of the point to check.
    /// @param filter Optional filter to specify a subset of obstacles. Checks all if null.
    /// @return True if the point is inside an obstacle, false otherwise.
    bool is_point_in_obstacles(const models::Coords& point, const obstacles::Obstacle* filter = nullptr) const;

    /// @brief Retrieves the size of the computed avoidance path.
    /// @return The number of poses in the path, including start and finish.
    size_t get_path_size() const { return path_.size(); }

    /// @brief Retrieves the pose at a specific index in the computed path.
    /// @param index The index of the pose in the path.
    /// @return The coordinates of the pose at the given index.
    models::Coords get_path_pose(uint8_t index) const;

    /// @brief Builds the avoidance graph between the start and finish positions.
    /// @param start The starting position.
    /// @param finish The finishing position.
    /// @return True if the graph was successfully built, false otherwise.
    bool avoidance(const models::Coords& start, const models::Coords& finish);

    /// @brief Checks whether recomputation of the path is necessary.
    /// @param start The starting position.
    /// @param stop The stopping position.
    /// @return True if recomputation is needed, false otherwise.
    bool check_recompute(const models::Coords& start, const models::Coords& stop);

    /// @brief Adds a dynamic obstacle to the list of obstacles.
    /// @param obstacle The dynamic obstacle to add.
    void add_dynamic_obstacle(obstacles::Obstacle& obstacle);

    /// @brief Clears all dynamic obstacles.
    void clear_dynamic_obstacles();

private:
    shared_memory::SharedMemory shared_memory_; ///< Shared memory instance.
    shared_memory::shared_properties_t& shared_memory_properties_; ///< Pointer to shared properties in shared memory.
    std::vector<models::Coords> valid_points_; ///< List of valid points for graph vertices.
    std::map<uint64_t, std::map<uint64_t, double>> graph_; ///< Graph representation using adjacency lists.

    models::Coords start_pose_;  ///< The starting pose for path computation.
    models::Coords finish_pose_; ///< The finishing pose for path computation.

    std::deque<std::reference_wrapper<models::Coords>> path_; ///< Path from start to finish.
    bool is_avoidance_computed_; ///< Flag indicating whether the path has been computed.

    float *table_limits_; ///< The limits of the table.
    float table_limits_margin_;  ///< Margin inside the table limits.

    std::vector<std::reference_wrapper<obstacles::Obstacle>> dynamic_obstacles_; ///< List of dynamic obstacles.

    /// @brief Validates the obstacle points and ensures they can be used for graph building.
    void validate_obstacle_points();

    /// @brief Builds the avoidance graph using the validated points.
    void build_avoidance_graph();

    /// @brief Prints the graph for debugging purposes.
    void print_graph();

    /// @brief Prints the computed path for debugging purposes.
    void print_path();

    /// @brief Prints the parent map used in pathfinding algorithms.
    /// @param parent The map of parent nodes.
    void print_parents(const std::map<int, int>& parent);

    /// @brief Executes Dijkstra's algorithm on the graph to find the shortest path.
    /// @return True if a path was found, false otherwise.
    bool dijkstra();

    /// @brief Checks if a point is within the table limits.
    /// @param point The coordinates of the point to check.
    /// @return True if the point is within the table limits, false otherwise.
    bool is_point_in_table_limits(const models::Coords& point) const
    {
        return (
            (table_limits_[0] + table_limits_margin_ < point.x() &&
            point.x() < table_limits_[1] - table_limits_margin_) &&
            (table_limits_[2] + table_limits_margin_ < point.y() &&
            point.y() < table_limits_[3] - table_limits_margin_)
        );
    }
};

} // namespace avoidance

} // namespace cogip

/// @}
