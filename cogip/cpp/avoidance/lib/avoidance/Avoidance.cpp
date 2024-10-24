/* Standard includes */
#include <math.h>
#include <stdio.h>
#include <deque>

/* Project includes */
#include "avoidance/Avoidance.hpp"
#include "obstacles/ObstaclePolygon.hpp"
#include "utils.hpp"
#include "cogip_defs/Coords.hpp"

#define START_INDEX     0
#define FINISH_INDEX    1

Avoidance::Avoidance(const cogip::obstacles::ObstaclePolygon &borders)
    : _validPointsCount(0), _isAvoidanceComputed(false), _borders(borders), _logger("Avoidance") {
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
            if (is_point_in_obstacles(obstacle.center(), &obstacle)) {
                continue;
            }

            /* Validate bounding box points */
            for (auto &point: obstacle) {
                if (!_borders.is_point_inside(point)) {
                    continue;
                }
                if (is_point_in_obstacles(point, nullptr)) {
                    continue;
                }
                /* Found a valid point */
                _validPoints[_validPointsCount++] = { point.x(), point.y() };
            }
        }
    }
}

void Avoidance::buildAvoidanceGraph()
{
    /* Validate all possible points */
    validateObstaclePoints();

    /* For each segment of the valid points list */
    for (int p = 0; p < _validPointsCount; p++) {
        for (int p2 = p + 1; p2 < _validPointsCount; p2++) {
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
            if ((p < MAX_VERTICES) && (p2 < MAX_VERTICES)) {
                if (!collide) {
                    _graph[p] |= (1 << p2);
                    _graph[p2] |= (1 << p);
                } else {
                    _graph[p] &= ~(1 << p2);
                    _graph[p2] &= ~(1 << p);
                }
            }
        }
    }
}

bool Avoidance::dijkstra()
{
    bool checked[MAX_VERTICES];  /**< List of vertices already checked */
    double distance[MAX_VERTICES]; /**< Distance of each vertex from the start */
    uint16_t v;  /**< Current vertex index */
    uint16_t i;  /**< Index for iterating vertices */

    int parent[MAX_VERTICES];  /**< Parent relationship for path recovery */
    uint8_t start = START_INDEX;

    /* Initialize arrays */
    for (i = 0; i <= _validPointsCount; i++) {
        checked[i] = false;
        distance[i] = MAX_DISTANCE;
        parent[i] = -1;
    }
    _path.clear();

    /* Start point has a weight of 0 */
    distance[start] = 0;
    v = start;

    /* If start point has no reachable neighbor, return error */
    if (_graph[v] == 0) {
        _isAvoidanceComputed = false;
        return false;
    }

    /* Loop until finish point is found or all points are checked */
    while ((v != FINISH_INDEX) && (!checked[v])) {
        double min_distance = MAX_DISTANCE;

        checked[v] = true;

        /* Parse all valid points */
        for (i = 0; i < _validPointsCount; i++) {
            /* Check if the current valid point is a neighbor */
            if (_graph[v] & (1 << i)) {
                double weight = (_validPoints[v].x() - _validPoints[i].x());
                weight *= (_validPoints[v].x() - _validPoints[i].x());
                weight += (_validPoints[v].y() - _validPoints[i].y())
                          * (_validPoints[v].y() - _validPoints[i].y());
                weight = sqrt(weight);

                if ((weight >= 0) && (distance[i] > (distance[v] + weight))) {
                    distance[i] = distance[v] + weight;
                    parent[i] = v;
                }
            }
        }

        /* Select the next vertex with the lowest distance */
        for (i = 1; i < _validPointsCount; i++) {
            if ((!checked[i]) && (min_distance > distance[i])) {
                min_distance = distance[i];
                v = i;
            }
        }
    }

    /* Build child path from start to finish pose by reversing parent path */
    i = 1;
    while (parent[i] > 0) {
        _path.push_front(_validPoints[parent[i]]);
        i = parent[i];
    }

    _isAvoidanceComputed = true;
    printPath();
    return _isAvoidanceComputed;
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

bool Avoidance::buildGraph(const cogip::cogip_defs::Coords &start, const cogip::cogip_defs::Coords &finish)
{
    _startPose = start;
    _finishPose = finish;
    _isAvoidanceComputed = false;

    if (!_borders.is_point_inside(_finishPose)) {
        std::cerr << "Finish pose outside borders !" << std::endl;
        return false;
    }

    /* Check that the start and destination are not inside obstacles */
    for (auto l: _allObstacles) {
        for (auto obstacle: *l) {
            if (obstacle.get().is_point_inside(_finishPose)) {
                std::cerr << "Finish pose inside obstacle !" << std::endl;
                return false;
            }
            if (obstacle.get().is_point_inside(_startPose)) {
                _startPose = obstacle.get().nearest_point(_startPose);
            }
        }
    }

    _validPointsCount = 0;
    _validPoints[_validPointsCount++] = _startPose;
    _validPoints[_validPointsCount++] = _finishPose;

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

void Avoidance::printPath()
{
    std::cout << "[" << std::endl;
    if (_isAvoidanceComputed) {

        for (auto p: _path) {
            std::cout << "{\"x\":" << p.x() << ",\"y\":" << p.y() << "}," << std::endl;
        }
    }
    std::cout << "]" << std::endl;
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
