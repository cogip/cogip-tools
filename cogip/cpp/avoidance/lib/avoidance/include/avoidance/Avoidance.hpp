// Copyright (C) 2021 COGIP Robotics association <cogip35@gmail.com>
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

/// Project includes
#include "cogip_defs/Coords.hpp"
#include "obstacles/ObstaclePolygon.hpp"
#include "logger/Logger.hpp"

namespace cogip {

namespace avoidance {

/// @brief Class managing the avoidance algorithm and graph representation.
class Avoidance
{
public:
    static constexpr uint32_t max_distance = UINT32_MAX; ///< Maximum distance used for Dijkstra's algorithm.

    /// @brief Constructor initializing the avoidance system with obstacle borders.
    /// @param borders The polygon defining the boundaries of the avoidance area.
    Avoidance(const cogip::obstacles::ObstaclePolygon &borders);

    /// @brief Checks if a point is inside any obstacle.
    /// @param point The coordinates of the point to check.
    /// @param filter Optional filter to specify a subset of obstacles. Checks all if null.
    /// @return True if the point is inside an obstacle, false otherwise.
    bool is_point_in_obstacles(const cogip::cogip_defs::Coords &point, const cogip::obstacles::Obstacle *filter = nullptr) const;

    /// @brief Retrieves the size of the computed avoidance path.
    /// @return The number of poses in the path, including start and finish.
    size_t get_path_size() const { return path_.size(); }

    /// @brief Retrieves the pose at a specific index in the computed path.
    /// @param index The index of the pose in the path.
    /// @return The coordinates of the pose at the given index.
    cogip::cogip_defs::Coords get_path_pose(uint8_t index) const;

    /// @brief Builds the avoidance graph between the start and finish positions.
    /// @param start The starting position.
    /// @param finish The finishing position.
    /// @return True if the graph was successfully built, false otherwise.
    bool avoidance(const cogip::cogip_defs::Coords &start, const cogip::cogip_defs::Coords &finish);

    /// @brief Checks whether recomputation of the path is necessary.
    /// @param start The starting position.
    /// @param stop The stopping position.
    /// @return True if recomputation is needed, false otherwise.
    bool check_recompute(const cogip::cogip_defs::Coords &start, const cogip::cogip_defs::Coords &stop) const;

    /// @brief Retrieves the current obstacle borders.
    /// @return A constant reference to the obstacle polygon defining the borders.
    const cogip::obstacles::ObstaclePolygon& borders() const;

    /// @brief Updates the obstacle borders with a new polygon.
    /// @param new_borders The new polygon defining the borders of the avoidance area.
    void set_borders(const cogip::obstacles::ObstaclePolygon &new_borders);

    /// @brief Adds a fixed obstacle to the list of obstacles.
    /// @param obstacle The obstacle to add.
    void add_fixed_obstacle(cogip::obstacles::Obstacle &obstacle);

    /// @brief Removes a specific fixed obstacle from the list.
    /// @param obstacle The obstacle to remove.
    void remove_fixed_obstacle(cogip::obstacles::Obstacle &obstacle);

    /// @brief Clears all fixed obstacles.
    void clear_fixed_obstacles();

    /// @brief Adds a dynamic obstacle to the list of obstacles.
    /// @param obstacle The dynamic obstacle to add.
    void add_dynamic_obstacle(cogip::obstacles::Obstacle &obstacle);

    /// @brief Removes a specific dynamic obstacle from the list.
    /// @param obstacle The dynamic obstacle to remove.
    void remove_dynamic_obstacle(cogip::obstacles::Obstacle &obstacle);

    /// @brief Clears all dynamic obstacles.
    void clear_dynamic_obstacles();

private:
    std::vector<cogip::cogip_defs::Coords> valid_points_; ///< List of valid points for graph vertices.
    std::map<uint64_t, std::map<uint64_t, double>> graph_; ///< Graph representation using adjacency lists.

    cogip::cogip_defs::Coords start_pose_;  ///< The starting pose for path computation.
    cogip::cogip_defs::Coords finish_pose_; ///< The finishing pose for path computation.

    std::deque<std::reference_wrapper<cogip::cogip_defs::Coords>> path_; ///< Path from start to finish.
    bool is_avoidance_computed_; ///< Flag indicating whether the path has been computed.

    cogip::obstacles::ObstaclePolygon borders_; ///< The polygon defining the borders of the avoidance area.

    std::vector<std::reference_wrapper<cogip::obstacles::Obstacle>> fixed_obstacles_; ///< List of fixed obstacles.
    std::vector<std::reference_wrapper<cogip::obstacles::Obstacle>> dynamic_obstacles_; ///< List of dynamic obstacles.
    std::set<std::vector<std::reference_wrapper<cogip::obstacles::Obstacle>> const *> all_obstacles_; ///< Set of all obstacles.

    std::mutex dynamic_obstacles_mutex_; ///< Mutex for protecting the dynamic obstacle list.

    Logger logger_; ///< Logger instance for logging.

    /// @brief Validates the obstacle points and ensures they can be used for graph building.
    void validate_obstacle_points();

    /// @brief Builds the avoidance graph using the validated points.
    void build_avoidance_graph();

    /// @brief Prints the graph for debugging purposes.
    void print_graph() const;

    /// @brief Prints the computed path for debugging purposes.
    void print_path() const;

    /// @brief Prints the parent map used in pathfinding algorithms.
    /// @param parent The map of parent nodes.
    static void _print_parents(const std::map<int, int>& parent);

    /// @brief Executes Dijkstra's algorithm on the graph to find the shortest path.
    /// @return True if a path was found, false otherwise.
    bool dijkstra();
};

} // namespace avoidance

} // namespace cogip

/// @}
