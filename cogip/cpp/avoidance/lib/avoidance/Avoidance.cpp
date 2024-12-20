// Copyright (C) 2021 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level
// directory for more details.

// Standard includes
#include <cmath>
#include <deque>
#include <iostream>
#include <map>
#include <vector>

// Project includes
#include "avoidance/Avoidance.hpp"
#include "obstacles/ObstaclePolygon.hpp"
#include "utils.hpp"
#include "cogip_defs/Coords.hpp"

#define START_INDEX     0
#define FINISH_INDEX    1

namespace cogip {

namespace avoidance {

Avoidance::Avoidance(const cogip::obstacles::ObstaclePolygon &borders)
    : is_avoidance_computed_(false), borders_(borders), logger_("Avoidance") {
    all_obstacles_.insert(&fixed_obstacles_);
    all_obstacles_.insert(&dynamic_obstacles_);
}

bool Avoidance::avoidance(const cogip::cogip_defs::Coords &start,
                          const cogip::cogip_defs::Coords &finish) {
    std::cout << "avoidance: Starting computation" << std::endl;

    // Initialize start and finish poses
    start_pose_ = start;
    finish_pose_ = finish;
    is_avoidance_computed_ = false;

    // Validate that the finish pose is inside borders
    if (!borders_.is_point_inside(finish_pose_)) {
        std::cerr << "avoidance: Finish pose is outside the borders!" << std::endl;
        return false;
    }

    // Validate that the start and finish poses are not inside any obstacles
    for (const auto &obstacle_list : all_obstacles_) {
        for (const auto &obstacle : *obstacle_list) {
            const auto &current_obstacle = obstacle.get();
            if (current_obstacle.is_point_inside(finish_pose_)) {
                std::cerr << "avoidance: Finish pose is inside an obstacle!" << std::endl;
                return false;
            }
            if (current_obstacle.is_point_inside(start_pose_)) {
                start_pose_ = current_obstacle.nearest_point(start_pose_);
            }
        }
    }

    std::cout << "avoidance: Poses validated" << std::endl;

    // Prepare valid points for pathfinding
    valid_points_ = {start_pose_, finish_pose_};

    // Build avoidance graph and compute path using Dijkstra
    std::cout << "avoidance: Building graph and computing path" << std::endl;
    build_avoidance_graph();

    bool ret = dijkstra();
    if (ret) {
        std::cout << "avoidance: Path successfully computed" << std::endl;
    } else {
        std::cerr << "avoidance: Failed to compute path" << std::endl;
    }

    return ret;
}

bool Avoidance::is_point_in_obstacles(const cogip::cogip_defs::Coords &point, const cogip::obstacles::Obstacle *filter) const
{
    for (const auto &obstacles : all_obstacles_) {
        for (const auto &obstacle : *obstacles) {
            if (!obstacle.get().enabled() || &obstacle.get() == filter) {
                continue;
            }
            if (obstacle.get().is_point_inside(point)) {
                return true;
            }
        }
    }
    return false;
}

bool Avoidance::check_recompute(const cogip::cogip_defs::Coords &start,
                                const cogip::cogip_defs::Coords &stop) const
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
    for (const auto &list : all_obstacles_) {
        for (const auto &obstacle_wrapper : *list) {
            const auto &obstacle = obstacle_wrapper.get();

            if (!obstacle.enabled()) {
                continue;
            }

            if (!borders_.is_point_inside(obstacle.center())) {
                continue;
            }

            for (const auto &point : obstacle.bounding_box()) {
                if (!borders_.is_point_inside(point) || is_point_in_obstacles(point, nullptr)) {
                    continue;
                }
                valid_points_.emplace_back(point.x(), point.y());
            }
        }
    }

    std::cout << "validate_obstacle_points: number of valid points = " << valid_points_.size() << std::endl;
    //for (const auto &point : valid_points_) {
    //    std::cout << "{" << point.x() << ", " << point.y() << "}" << std::endl;
    //}
}

void Avoidance::build_avoidance_graph()
{
    std::cout << "build_avoidance_graph: build avoidance graph" << std::endl;

    validate_obstacle_points();
    graph_.clear();

    for (size_t i = 0; i < valid_points_.size(); i++) {
        for (size_t j = i + 1; j < valid_points_.size(); j++) {
            bool collide = false;
            for (const auto &list : all_obstacles_) {
                for (const auto &obstacle : *list) {
                    if (obstacle.get().enabled() &&
                        obstacle.get().is_segment_crossing(valid_points_[i], valid_points_[j])) {
                        collide = true;
                        break;
                    }
                }
            }
            if (!collide) {
                double distance = utils::calculate_distance(valid_points_[i], valid_points_[j]);
                graph_[i][j] = distance;
                graph_[j][i] = distance;
            }
        }
    }

    //print_graph();
}

bool Avoidance::dijkstra()
{
    constexpr double MAX_DISTANCE = std::numeric_limits<double>::infinity();
    std::cout << "dijkstra: Compute Dijkstra" << std::endl;

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
        std::cerr << "dijkstra: Start pose has no reachable neighbors!" << std::endl;
        is_avoidance_computed_ = false;
        return false;
    }

    int v = start;
    while ((v != finish) && !checked[v]) {
        checked[v] = true;

        for (const auto &[neighbor, weight] : graph_[v]) {
            if (distances[neighbor] > distances[v] + weight) {
                distances[neighbor] = distances[v] + weight;
                parents[neighbor] = v;
            }
        }

        double min_distance = MAX_DISTANCE;
        for (const auto &[index, distance] : distances) {
            if (!checked[index] && distance < min_distance) {
                min_distance = distance;
                v = index;
            }
        }

        if (min_distance == MAX_DISTANCE) {
            std::cerr << "dijkstra: No more points to check!" << std::endl;
            is_avoidance_computed_ = false;
            return false;
        }
    }

    //_print_parents(parents);

    int current = finish;
    while (current != -1 && current != start) {
        path_.emplace_front(valid_points_[current]);
        current = parents[current];
    }
    path_.emplace_front(valid_points_[start]);

    is_avoidance_computed_ = true;
    //print_path();
    return true;
}

cogip::cogip_defs::Coords Avoidance::get_path_pose(uint8_t index) const
{
    // Check if index is within range of _path
    if (index < get_path_size()) {
        return path_[index];
    }

    // If index is out of range, throw an exception
    throw std::out_of_range("Index out of range in Avoidance::getPose");
}

void Avoidance::add_dynamic_obstacle(cogip::obstacles::Obstacle &obstacle) {
    std::lock_guard<std::mutex> lock(dynamic_obstacles_mutex_);
    dynamic_obstacles_.emplace_back(obstacle);
}

void Avoidance::remove_dynamic_obstacle(cogip::obstacles::Obstacle &obstacle) {
    std::lock_guard<std::mutex> lock(dynamic_obstacles_mutex_);
    dynamic_obstacles_.erase(
        std::remove_if(dynamic_obstacles_.begin(), dynamic_obstacles_.end(),
                       [&obstacle](auto &o) { return &o.get() == &obstacle; }),
        dynamic_obstacles_.end());
}

void Avoidance::clear_dynamic_obstacles() {
    std::lock_guard<std::mutex> lock(dynamic_obstacles_mutex_);
    dynamic_obstacles_.clear();
}

void Avoidance::print_graph() const {
    for (const auto &[node, edges] : graph_) {
        std::cout << "Point " << node << "("
                  << valid_points_[node].x() << ", "
                  << valid_points_[node].y() << ") -> { ";
        for (const auto &[neighbor, distance] : edges) {
            std::cout << "(" << neighbor << ": " << distance << ") ";
        }
        std::cout << "}" << std::endl;
    }
}

void Avoidance::print_path() const {
    std::cout << "Path (size = " << path_.size() << "): ";
    for (const auto &coords : path_) {
        std::cout << "(" << coords.get().x() << ", " << coords.get().y() << ") ";
    }
    std::cout << std::endl;
}

void Avoidance::_print_parents(const std::map<int, int> &parents) {
    std::cout << "Parents: ";
    for (const auto &[child, parent] : parents) {
        std::cout << "(" << child << ", " << parent << ") ";
    }
    std::cout << std::endl;
}

const cogip::obstacles::ObstaclePolygon &Avoidance::borders() const {
    return borders_;
}

void Avoidance::set_borders(const cogip::obstacles::ObstaclePolygon &new_borders) {
    borders_ = new_borders;
}

} // namespace avoidance

} // namespace cogip
