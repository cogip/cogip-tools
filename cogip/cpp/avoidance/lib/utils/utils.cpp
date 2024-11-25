#include "utils.hpp"

#include <cmath>

namespace cogip {

namespace utils {

bool areDoublesEqual(double a, double b, double epsilon) {
    return std::fabs(a - b) < epsilon;
}

double calculate_distance(const cogip_defs::Coords &a, const cogip_defs::Coords &b)
{
    // Compute the weight (Euclidean distance between two points)
    return std::hypot(
        b.x() - a.x(),
        b.y() - a.y()
    );
}

} // namespace utils

} // namespace cogip
