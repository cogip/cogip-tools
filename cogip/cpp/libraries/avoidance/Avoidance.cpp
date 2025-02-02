// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level
// directory for more details.

// Standard includes
#include <algorithm>
#include <cmath>
#include <deque>
#include <iostream>
#include <map>
#include <vector>

// Project includes
#include "avoidance/Avoidance.hpp"
#include "obstacles/ObstaclePolygon.hpp"
#include "utils/trigonometry.hpp"
#include "models/Coords.hpp"

#define START_INDEX     0
#define FINISH_INDEX    1

namespace cogip {

namespace avoidance {

Avoidance::Avoidance(const cogip::obstacles::ObstaclePolygon& borders)
    : is_avoidance_computed_(false), borders_(borders),
    logger_("Avoidance", cogip::logger::LogLevel::DEBUG) {
}

bool Avoidance::avoidance(const models::Coords& start,
                          const models::Coords& finish) {
    logger_.debug() << "avoidance: Starting computation" << std::endl;

    // Initialize start and finish poses
    start_pose_ = start;
    finish_pose_ = finish;
    is_avoidance_computed_ = false;

    logger_.debug() << "start = " << start << std::endl;
    logger_.debug() << "start_pose_ = " << start_pose_ << std::endl;
    logger_.debug() << "finish = " << finish << std::endl;
    logger_.debug() << "finish_pose_ = " << finish_pose_ << std::endl;

    // Validate that the finish pose is inside borders
    if (!borders_.is_point_inside(finish_pose_)) {
        logger_.error() << "avoidance: Finish pose is outside the borders" << std::endl;
        return false;
    }

    // Validate that the start and finish poses are not inside any obstacles
    for (const auto& obstacle : dynamic_obstacles_) {
        auto& current_obstacle = obstacle.get();
        if (current_obstacle.is_point_inside(finish_pose_)) {
            logger_.error() << "avoidance: Finish pose is inside an obstacle" << std::endl;
            return false;
        }
        if (current_obstacle.is_point_inside(start_pose_)) {
            start_pose_ = current_obstacle.nearest_point(start_pose_);
            logger_.debug() << "start pose inside obstacle, updated: " << start_pose_ << std::endl;
        }
    }

    logger_.debug() << "avoidance: Poses validated" << std::endl;

    // Prepare valid points for pathfinding
    valid_points_ = {start_pose_, finish_pose_};
    logger_.debug() << "valid_points_[0] = " << valid_points_[0] << std::endl;
    logger_.debug() << "valid_points_[1] = " << valid_points_[1] << std::endl;

    // Build avoidance graph and compute path using Dijkstra
    logger_.debug() << "avoidance: Building graph and computing path" << std::endl;
    build_avoidance_graph();

    bool ret = dijkstra();
    if (ret) {
        logger_.debug() << "avoidance: Path successfully computed" << std::endl;
    } else {
        logger_.error() << "avoidance: Failed to compute path" << std::endl;
    }

    return ret;
}

bool Avoidance::is_point_in_obstacles(const models::Coords& point, const cogip::obstacles::Obstacle* filter) const
{
    for (const auto& obstacle : dynamic_obstacles_) {
        if (&obstacle.get() == filter) {
            continue;
        }
        if (obstacle.get().is_point_inside(point)) {
            return true;
        }
    }
    return false;
}

bool Avoidance::check_recompute(const models::Coords& start,
                                const models::Coords& stop)
{
    for (auto obstacle : dynamic_obstacles_) {
        if (!borders_.is_point_inside(obstacle.get().center())) {
            continue;
        }
        if (obstacle.get().is_segment_crossing(start, stop)) {
            return true;
        }
    }
    return false;
}

void Avoidance::validate_obstacle_points()
{
    for (const auto& obstacle_wrapper : dynamic_obstacles_) {
        auto& obstacle = obstacle_wrapper.get();

        if (!borders_.is_point_inside(obstacle.center())) {
            continue;
        }

        for (const auto& point : obstacle.bounding_box()) {
            if (!borders_.is_point_inside(point) || is_point_in_obstacles(point, nullptr)) {
                continue;
            }
            valid_points_.emplace_back(point.x(), point.y());
        }
    }

    logger_.debug() << "validate_obstacle_points: number of valid points = " << valid_points_.size() << std::endl;
    for (const auto& point : valid_points_) {
        logger_.debug() << "{" << point << "}" << std::endl;
    }
}

void Avoidance::build_avoidance_graph()
{
    logger_.debug() << "build_avoidance_graph: build avoidance graph" << std::endl;

    validate_obstacle_points();
    graph_.clear();

    for (size_t i = 0; i < valid_points_.size(); i++) {
        const auto& point_i = valid_points_[i];
        for (size_t j = i + 1; j < valid_points_.size(); j++) {
            const auto& point_j = valid_points_[j];
            bool collide = false;
            for (const auto& obstacle : dynamic_obstacles_) {
                if (obstacle.get().is_segment_crossing(point_i, point_j)) {
                    collide = true;
                    break;
                }
            }
            if (!collide) {
                double distance = utils::calculate_distance(
                    point_i.x(),
                    point_i.y(),
                    point_j.x(),
                    point_j.y()
                );
                graph_[i][j] = distance;
                graph_[j][i] = distance;
            }
        }
    }

    print_graph();
}

bool Avoidance::dijkstra()
{
    constexpr double MAX_DISTANCE = std::numeric_limits<double>::infinity();
    logger_.debug() << "dijkstra: Compute Dijkstra" << std::endl;

    std::map<int, bool> checked;
    std::map<int, double> distances;
    std::map<int, int> parents;

    int start = START_INDEX;
    int finish = FINISH_INDEX;

    for (size_t i = 0; i < valid_points_.size(); ++i) {
        checked[i] = false;
        distances[i] = MAX_DISTANCE;
        parents[i] = -1;
    }
    path_.clear();
    distances[start] = 0;

    if (graph_.find(start) == graph_.end() || graph_[start].empty()) {
        logger_.error() << "dijkstra: Start pose has no reachable neighbors" << std::endl;
        is_avoidance_computed_ = false;
        return false;
    }

    int v = start;
    while ((v != finish) && !checked[v]) {
        checked[v] = true;

        for (const auto& [neighbor, weight] : graph_[v]) {
            if (distances[neighbor] > distances[v] + weight) {
                distances[neighbor] = distances[v] + weight;
                parents[neighbor] = v;
            }
        }

        double min_distance = MAX_DISTANCE;
        for (const auto& [index, distance] : distances) {
            if (!checked[index] && distance < min_distance) {
                min_distance = distance;
                v = index;
            }
        }

        if (min_distance == MAX_DISTANCE) {
            logger_.error() << "dijkstra: No more points to check" << std::endl;
            is_avoidance_computed_ = false;
            return false;
        }
    }

    print_parents(parents);

    int current = parents[finish];
    while (current != -1 && current != start) {
        path_.emplace_front(valid_points_[current]);
        current = parents[current];
    }
    path_.emplace_front(valid_points_[start]);

    is_avoidance_computed_ = true;
    print_path();
    return true;
}

models::Coords Avoidance::get_path_pose(uint8_t index) const
{
    // Check if index is within range of _path
    if (index < get_path_size()) {
        return path_[index];
    }

    // If index is out of range, throw an exception
    throw std::out_of_range("Avoidance::get_path_pose: index out of range in ");
}

void Avoidance::add_dynamic_obstacle(cogip::obstacles::Obstacle& obstacle) {
    dynamic_obstacles_.emplace_back(obstacle);
}

void Avoidance::clear_dynamic_obstacles() {
    dynamic_obstacles_.clear();
}

void Avoidance::print_graph() {
    for (const auto& [node, edges] : graph_) {
        logger_.debug() << "Point " << node << "("
                        << valid_points_[node].x() << ", "
                        << valid_points_[node].y() << ") -> { " << std::endl;
        for (const auto& [neighbor, distance] : edges) {
            logger_.debug() << "    (" << neighbor << ": " << distance << ")" << std::endl;
        }
        logger_.debug() << "}" << std::endl;
    }
}

void Avoidance::print_path() {
    logger_.debug() << "Path (size = " << path_.size() << "): " << std::endl;
    for (const auto& coords : path_) {
        logger_.debug() << "    (" << coords.get().x() << ", " << coords.get().y() << ")" << std::endl;
    }
    logger_.debug() << std::endl;
}

void Avoidance::print_parents(const std::map<int, int>& parents) {
    logger_.debug() << "Parents: " << std::endl;
    for (const auto& [child, parent] : parents) {
        logger_.debug() << "    (" << child << ", " << parent << ")" << std::endl;
    }
    logger_.debug() << std::endl;
}

const cogip::obstacles::ObstaclePolygon& Avoidance::borders() const {
    return borders_;
}

void Avoidance::set_borders(const cogip::obstacles::ObstaclePolygon& new_borders) {
    borders_ = new_borders;
}

} // namespace avoidance

} // namespace cogip
