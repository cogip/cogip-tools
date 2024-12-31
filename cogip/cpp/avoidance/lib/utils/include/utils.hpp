#pragma once

#include "cogip_defs/Coords.hpp"

namespace cogip {

namespace utils {

/**
 * @brief Compare two floating-point numbers (double) with a specified tolerance.
 *
 * This function checks if the absolute difference between two doubles is less than a given tolerance (epsilon),
 * which helps to address the imprecision of floating-point calculations.
 *
 * @param[in]   a       The first floating-point number to compare.
 * @param[in]   b       The second floating-point number to compare.
 * @param[in]   epsilon The tolerance used for comparison (default value: 1e-3).
 * @return true         If the absolute difference between a and b is less than epsilon.
 * @return false        Otherwise.
 */
bool areDoublesEqual(double a, double b, double epsilon = 1e-3);

/**
 * @brief Calculate the Euclidean distance between two coordinates.
 *
 * This function computes the straight-line distance between two points
 * in a 2D space, represented by the Coords class.
 *
 * @param[in]   a   The first coordinate point.
 * @param[in]   b   The second coordinate point.
 * @return double   The Euclidean distance between the two points.
 */
double calculate_distance(const cogip_defs::Coords &a, const cogip_defs::Coords &b);

} // namespace utils

} // namespace cogip
