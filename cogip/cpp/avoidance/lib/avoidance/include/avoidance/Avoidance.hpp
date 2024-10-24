/// Copyright (C) 2021 COGIP Robotics association <cogip35@gmail.com>
///
/// This file is subject to the terms and conditions of the GNU Lesser
/// General Public License v2.1. See the file LICENSE in the top level
/// directory for more details.

/// @defgroup    lib_avoidance Avoidance module
/// @ingroup     lib
/// @brief       Avoidance module
///
/// Avoidance is split in 2 steps:
///   1. avoidance_build_graph(): build graph of avoidance path to reach finish
///      pose, including obstacles avoidance.
///   2. avoidance_get_pose(): get intermediate pose in avoidance computed path.
///
/// Direct segment to reach final position can be checked to see if it becomes
/// free of obstacles with avoidance_check_recompute()
///
/// @{
/// @file
/// @brief       Public API for avoidance module
/// @author      Gilles DOFFE <g.doffe@gmail.com>

#pragma once

/// Standard includes
#include <cstdint>
#include <deque>
#include <mutex>
#include <set>

/// Project includes
#include "cogip_defs/Coords.hpp"
#include "obstacles/ObstaclePolygon.hpp"
#include "logger/Logger.hpp"


/// @brief Class handling avoidance algorithm and graph management
class Avoidance
{
public:
    static const uint8_t MAX_VERTICES = 64; ///< Maximum number of vertices in the graph
    static const uint32_t MAX_DISTANCE = UINT32_MAX; ///< Maximum distance value used for Dijkstra's algorithm

    /// @brief Constructor that takes obstacle borders as input
    ///
    /// @param borders The obstacle polygon defining the boundaries of the avoidance area
    Avoidance(const cogip::obstacles::ObstaclePolygon &borders);

    /// @brief Checks if a point is inside any obstacle.
    /// @param p Point coordinates to check.
    /// @param filter Optional obstacle filter. If null, checks all obstacles.
    /// @return true if the point is inside an obstacle, false otherwise.
    bool is_point_in_obstacles(const cogip::cogip_defs::Coords &p, const cogip::obstacles::Obstacle *filter);

    /// @brief Get computed avoidance path size.
    ///
    /// @return Number of pose in the path, start and stop pose included
    size_t getPathSize() const;

    /// @brief Get pose at given index in the avoidance path
    ///
    /// @param index Pose index in the avoidance path
    /// @return cogip::cogip_defs::Coords Coordinates of the pose
    cogip::cogip_defs::Coords getPathPose(uint8_t index) const;

    /// @brief Build avoidance graph between start and finish points
    /// @param start Start position
    /// @param finish Finish position
    /// @return true if graph building is successful, false otherwise
    bool buildGraph(const cogip::cogip_defs::Coords &start, const cogip::cogip_defs::Coords &finish);

    /// @brief Check if avoidance recomputation is needed
    /// @param start Start position
    /// @param stop End position
    /// @return true if recomputation is needed, false otherwise
    bool checkRecompute(const cogip::cogip_defs::Coords &start, const cogip::cogip_defs::Coords &stop) const;

    /// @brief Print the computed path for debugging purposes
    void printPath();

    /// @brief Get the current obstacle borders
    /// @return const cogip::obstacles::ObstaclePolygon& Current borders
    const cogip::obstacles::ObstaclePolygon& getBorders() const;

    /// @brief Set new obstacle borders
    /// @param newBorders The new obstacle polygon for the avoidance area
    void setBorders(const cogip::obstacles::ObstaclePolygon &newBorders);

    /// @brief Adds a fixed obstacle to the list
    /// @param obstacle A reference to the obstacle to add
    void addFixedObstacle(cogip::obstacles::Obstacle &obstacle);

    /// @brief Removes a specific fixed obstacle from the list
    /// @param obstacle A reference to the obstacle to remove
    void removeFixedObstacle(cogip::obstacles::Obstacle &obstacle);

    /// @brief Clears the list of fixed obstacles
    void clearFixedObstacles();

    /// @brief Adds a dynamic obstacle to the list
    /// @param obstacle A reference to the obstacle to add
    void addDynamicObstacle(cogip::obstacles::Obstacle &obstacle);

    /// @brief Removes a specific dynamic obstacle from the list
    /// @param obstacle A reference to the obstacle to remove
    void removeDynamicObstacle(cogip::obstacles::Obstacle &obstacle);

    /// @brief Clears the list of dynamic obstacles
    void clearDynamicObstacles();

private:
    cogip::cogip_defs::Coords _validPoints[MAX_VERTICES]; ///< Array of valid points for graph vertices
    uint8_t _validPointsCount; ///< Number of valid points in the graph
    uint64_t _graph[MAX_VERTICES]; ///< Graph of valid segments between points, represented as bitmaps

    cogip::cogip_defs::Coords _startPose; ///< Start pose for the avoidance path
    cogip::cogip_defs::Coords _finishPose; ///< Finish pose for the avoidance path

    std::deque<cogip::cogip_defs::Coords> _path; ///< Indexes of valid points from the start to the finish in the computed path
    bool _isAvoidanceComputed; ///< Flag indicating if the avoidance path has been successfully computed

    cogip::obstacles::ObstaclePolygon _borders; ///< Borders of the avoidance area, used to define the boundaries

    std::vector<std::reference_wrapper<cogip::obstacles::Obstacle>> _fixedObstacles; ///< Fixed obstacles list
    std::vector<std::reference_wrapper<cogip::obstacles::Obstacle>> _dynamicObstacles; ///< Dynamic obstacles list
    std::set<std::vector<std::reference_wrapper<cogip::obstacles::Obstacle>> const *> _allObstacles;  ///< List of all obstacle lists

    std::mutex _dynamicObstaclesMutex; ///< Dynamic obstacles list protection mutex

    Logger _logger; ///< Logger object

    /// @brief Validate obstacle points for building the graph
    void validateObstaclePoints();

    /// @brief Build the avoidance graph using the validated points
    void buildAvoidanceGraph();

    /// @brief Apply the Dijkstra algorithm on the graph to find the shortest path
    /// @return true if the algorithm successfully finds a path, false otherwise
    bool dijkstra();
};

/// @}
