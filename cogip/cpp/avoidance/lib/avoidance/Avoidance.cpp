/* Standard includes */
#include <cmath>
#include <deque>
#include <iostream>
#include <map>
#include <vector>

/* Project includes */
#include "avoidance/Avoidance.hpp"
#include "obstacles/ObstaclePolygon.hpp"
#include "utils.hpp"
#include "cogip_defs/Coords.hpp"

#define START_INDEX     0
#define FINISH_INDEX    1

namespace cogip {

namespace avoidance {

Avoidance::Avoidance(const cogip::obstacles::ObstaclePolygon &borders)
    : _isAvoidanceComputed(false), _borders(borders), _logger("Avoidance") {
        _allObstacles.insert(&_fixedObstacles);
        _allObstacles.insert(&_dynamicObstacles);
}

bool Avoidance::is_point_in_obstacles(const cogip::cogip_defs::Coords &p, const cogip::obstacles::Obstacle *filter)
{
    for (auto obstacles: _allObstacles) {
        for (auto obstacle: *obstacles) {
            if (! obstacle.get().enabled()) {
                continue;
            }
            if (filter == &(obstacle.get())) {
                continue;
            }
            if (obstacle.get().is_point_inside(p)) {
                return true;
            }
        }
    }
    return false;
}

void Avoidance::validateObstaclePoints()
{
    for (auto l: _allObstacles) {
        for (auto obstacleWrapper: *l) {
            /* Obstacle Polygon */
            const cogip::obstacles::Obstacle &obstacle = obstacleWrapper.get();

            if (!obstacle.enabled()) {
                continue;
            }

            /* Check if obstacle center is inside borders */
            if (!_borders.is_point_inside(obstacle.center())) {
                continue;
            }

            /* Check if the center of this obstacle is not in another obstacle */
            //if (is_point_in_obstacles(obstacle.center(), &obstacle)) {
            //    continue;
            //}

            /* Validate bounding box points */
            for (auto &point: obstacle.bounding_box()) {
                if (!_borders.is_point_inside(point)) {
                    continue;
                }
                if (is_point_in_obstacles(point, nullptr)) {
                    continue;
                }
                /* Found a valid point */
                _validPoints.push_back(cogip::cogip_defs::Coords(point.x(), point.y()));
            }
        }
    }

    std::cout << "validateObstaclePoints: number of valid points = " << _validPoints.size() << std::endl;
    std::cout << "validateObstaclePoints: valid points list = " << std::endl;
    for (const auto& point : _validPoints) {
        std::cout << "{"
                      << point.x()
                      << ", "
                      << point.y()
                      << "}" << std::endl;
    }
}

void Avoidance::buildAvoidanceGraph()
{
    std::cout << "buildAvoidanceGraph: build avoidance graph" << std::endl;

    /* Validate all possible points */
    validateObstaclePoints();
    _graph.clear();

    /* For each segment of the valid points list */
    for (int p = 0; p < _validPoints.size(); p++) {
        for (int p2 = p + 1; p2 < _validPoints.size(); p2++) {
            bool collide = false;
            /* Check if that segment crosses a polygon */
            for (auto l: _allObstacles) {
                for (auto obstacle: *l) {
                    if (!obstacle.get().enabled()) {
                        continue;
                    }
                    if (obstacle.get().is_segment_crossing(_validPoints[p], _validPoints[p2])) {
                        collide = true;
                        break;
                    }
                }
            }
            /* If no collision, both points of the segment are added to
             * the graph with distance between them */
            if (!collide) {
                // Calcul de la distance entre p et p2
                double distance = utils::calculate_distance(_validPoints[p], _validPoints[p2]);
                _graph[p][p2] = distance;
                _graph[p2][p] = distance;
                std::cout << "buildAvoidanceGraph: graph size = " << _graph.size() << std::endl;
            }
        }
    }

    printGraph();
}

void Avoidance::printGraph() const {
    // Iterate through the outer map
    for (const auto& outerPair : _graph) {
        std::cout << "Point " << outerPair.first << " -> { ";

        // Iterate through the inner map for each outer key
        for (const auto& innerPair : outerPair.second) {
            std::cout << "(" << innerPair.first << ": " << innerPair.second << ") ";
        }

        std::cout << "}" << std::endl;
    }
}

bool Avoidance::dijkstra()
{
    constexpr double MAX_DISTANCE = std::numeric_limits<double>::infinity();

    std::cout << "dijkstra: Compute Dijkstra" << std::endl;

    std::map<int, bool> checked;               // List of vertices already checked
    std::map<int, double> distance;           // Distance of each vertex from the start
    std::map<int, int> parent;                // Parent relationship for path recovery

    int start = START_INDEX;
    int finish = FINISH_INDEX;

    // Initialization
    for (size_t i = 0; i < _validPoints.size(); ++i) {
        checked[i] = false;
        distance[i] = MAX_DISTANCE;
        parent[i] = -1;
    }
    _path.clear();

    // Start point has a distance of 0
    distance[start] = 0;

    // Check if the start point has reachable neighbors
    if (_graph.find(start) == _graph.end() || _graph[start].empty()) {
        std::cerr << "dijkstra: Start pose has no reachable neighbors !" << std::endl;
        _isAvoidanceComputed = false;
        return false;
    }

    // Dijkstra: main loop
    int v = start;
    while ((v != finish) && !checked[v]) {
        std::cout << "dijkstra: Checking point N°" << v << std::endl;

        double min_distance = MAX_DISTANCE;

        // Mark the current vertex as checked
        checked[v] = true;

        // Iterate through neighbors of the current vertex
        for (auto it = _graph[v].begin(); it != _graph[v].end(); ++it) {
            uint64_t neighbor = it->first;
            double weight = it->second;

            // Update distance and parent if a better path is found
            if (distance[neighbor] > distance[v] + weight) {
                distance[neighbor] = distance[v] + weight;
                parent[neighbor] = v;
            }
        }

        // Find the next vertex with the smallest distance
        min_distance = MAX_DISTANCE;
        for (const auto& [index, dist] : distance) {
            if (!checked[index] && dist < min_distance) {
                min_distance = dist;
                v = index;
            }
        }

        // No more vertices to check
        if (min_distance == MAX_DISTANCE) {
            std::cerr << "dijkstra: No more point to check !" << std::endl;
            _isAvoidanceComputed = false;
            _isAvoidanceComputed = false;
            return false;
        }
    }

    printParent(parent);

    // Build the final path by following the parent relationships from finish to start
    int current = finish;
    while (current != -1 && current != start) {
        _path.push_front(_validPoints[current]);
        current = parent[current];
        std::cout << "dijkstra: current point index = " << current << std::endl;
        std::cout << "dijkstra: path size = " << _path.size() << std::endl;
    }
    //_path.push_front(_validPoints[start]);

    _isAvoidanceComputed = true;

    // Print the computed path
    printPath();
    return true;
}

size_t Avoidance::getPathSize() const
{
    return _path.size();
}

cogip::cogip_defs::Coords Avoidance::getPathPose(uint8_t index) const
{
    // Check if index is within range of _path
    if (index < _path.size()) {
        return _path[index];
    }

    // If index is out of range, throw an exception
    throw std::out_of_range("Index out of range in Avoidance::getPose");
}

bool Avoidance::avoidance(const cogip::cogip_defs::Coords &start, const cogip::cogip_defs::Coords &finish)
{
    std::cout << "avoidance: Compute avoidance" << std::endl;

    _startPose = start;
    _finishPose = finish;
    _isAvoidanceComputed = false;

    if (!_borders.is_point_inside(_finishPose)) {
        std::cerr << "avoidance: Finish pose outside borders !" << std::endl;
        return false;
    }

    std::cout << "avoidance: Check start and finish poses" << std::endl;

    /* Check that the start and destination are not inside obstacles */
    for (auto l: _allObstacles) {
        for (auto obstacle: *l) {
            std::cout << "avoidance: Check obstacle {"
                      << obstacle.get().center().x()
                      << ", "
                      << obstacle.get().center().y()
                      << "}" << std::endl;
            if (obstacle.get().is_point_inside(_finishPose)) {
                std::cerr << "Finish pose inside obstacle !" << std::endl;
                return false;
            }
            if (obstacle.get().is_point_inside(_startPose)) {
                _startPose = obstacle.get().nearest_point(_startPose);
            }
        }
    }

    std::cout << "avoidance: Check OK" << std::endl;

    _validPoints.clear();
    _validPoints.push_back(_startPose);
    _validPoints.push_back(_finishPose);

    std::cout << "avoidance: Start and finish poses are checked" << std::endl;

    buildAvoidanceGraph();
    return dijkstra();
}

bool Avoidance::checkRecompute(const cogip::cogip_defs::Coords &start, const cogip::cogip_defs::Coords &stop) const
{
    //std::lock_guard<std::mutex> lock(_dynamicObstaclesMutex);  // Lock the mutex during access

    for (auto obstacle : _dynamicObstacles) {  // Use the member variable for dynamic obstacles
        if (!_borders.is_point_inside(obstacle.get().center())) {
            continue;
        }
        if (obstacle.get().is_segment_crossing(start, stop)) {
            return true;
        }
    }
    return false;
}

void Avoidance::printPath() const {
    std::cout << "Path (size = " << _path.size() << ")" << std::endl;

    // Iterate through the deque and print each Coords
    for (const auto& coordsWrapper : _path) {
        const cogip::cogip_defs::Coords& coords = coordsWrapper.get();
        std::cout << "(" << coords.x() << ", " << coords.y() << ") ";
    }

    std::cout << std::endl;
}

void Avoidance::printParent(const std::map<int, int>& parent) {
    std::cout << "Parent map: ";

    // Iterate through the map and print each key-value pair
    for (const auto& pair : parent) {
        std::cout << "(" << pair.first << ", " << pair.second << ") ";
    }

    std::cout << std::endl;
}

const cogip::obstacles::ObstaclePolygon& Avoidance::getBorders() const
{
    return _borders;
}

void Avoidance::setBorders(const cogip::obstacles::ObstaclePolygon &newBorders)
{
    _borders = newBorders;
}

void Avoidance::addDynamicObstacle(cogip::obstacles::Obstacle &obstacle) {
    std::lock_guard<std::mutex> lock(_dynamicObstaclesMutex);
    _dynamicObstacles.push_back(obstacle);
}

void Avoidance::removeDynamicObstacle(cogip::obstacles::Obstacle &obstacle) {
    std::lock_guard<std::mutex> lock(_dynamicObstaclesMutex);

    _dynamicObstacles.erase(
        // std::remove_if() move at the end of the list all elements that need to be deleted
        std::remove_if(_dynamicObstacles.begin(), _dynamicObstacles.end(),
                       // lambda to compare list elements
                       [&obstacle](std::reference_wrapper<cogip::obstacles::Obstacle> &o) {
                           return &o.get() == &obstacle;
                       }),
        _dynamicObstacles.end()
    );
}

void Avoidance::clearDynamicObstacles() {
    std::lock_guard<std::mutex> lock(_dynamicObstaclesMutex);
    _dynamicObstacles.clear();
}

} // namespace avoidance

} // namespace cogip
