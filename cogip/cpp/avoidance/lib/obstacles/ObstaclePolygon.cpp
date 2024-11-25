// Project includes
#include "obstacles/ObstaclePolygon.hpp"
#include "utils.hpp"

// System includes
#include <cmath>

namespace cogip {

namespace obstacles {


/// @brief Check if a segment defined by two points A,B is crossing line
///        defined by two other points C,D.
/// @param[in]   a           point A
/// @param[in]   b           point B
/// @param[in]   c           point C
/// @param[in]   d           point D
/// @return                  true if [AB] crosses (CD), false otherwise
static bool _is_segment_crossing_line(
    const cogip_defs::Coords &a, const cogip_defs::Coords &b,
    const cogip_defs::Coords &c, const cogip_defs::Coords &d)
{
    cogip_defs::Coords ab(b.x() - a.x(), b.y() - a.y());
    cogip_defs::Coords ac(c.x() - a.x(), c.y() - a.y());
    cogip_defs::Coords ad(d.x() - a.x(), d.y() - a.y());

    double det = (ab.x() * ad.y() - ab.y() * ad.x()) * (ab.x() * ac.y() - ab.y() * ac.x());

    return (det < 0);
}


/// @brief Check if a segment defined by two points A,B is crossing segment
///        defined by two other points C,D.
/// @param[in]   a           point A
/// @param[in]   b           point B
/// @param[in]   c           point C
/// @param[in]   d           point D
/// @return                  true if [AB] crosses [CD], false otherwise
static bool _is_segment_crossing_segment(
    const cogip_defs::Coords &a, const cogip_defs::Coords &b,
    const cogip_defs::Coords &c, const cogip_defs::Coords &d)
{
    if (!_is_segment_crossing_line(a, b, c, d)) {
        return false;
    }
    if (!_is_segment_crossing_line(c, d, a, b)) {
        return false;
    }
    return true;
}

ObstaclePolygon::ObstaclePolygon(const std::vector<cogip_defs::Coords> & points)
{
    for (const auto &point: points) {
        push_back(point);
    }

    int res = calculatePolygonRadius();
    switch (res) {
        case -ERANGE:
            throw "Not enough obstacle points, need 3 at least";
            break;
    }
}

int ObstaclePolygon::calculatePolygonCentroid() {
    double x_sum = 0.0;  // Weighted sum of x-coordinates for centroid calculation
    double y_sum = 0.0;  // Weighted sum of y-coordinates for centroid calculation
    double area = 0.0;   // Accumulated signed area of the polygon

    if (size() < 3) {
        // A valid polygon requires at least 3 points.
        // Returning a default point if the polygon is degenerate, as centroid calculation isn't meaningful.
        return -ERANGE;
    }

    for (auto it = begin(); it != end(); ++it) {
        // Current vertex
        const auto &p1 = *it;
        // Next vertex, wrapping around at the last point
        const auto &p2 = (it + 1 == end()) ? front() : *(it + 1);

        // Calculate the cross product of the vectors formed by the edge (p1 to p2).
        // This determines the "signed" area contribution of the edge.
        double cross_product = p1.x() * p2.y() - p2.x() * p1.y();

        // Accumulate the signed area. The sum of cross products gives twice the actual polygon area.
        area += cross_product;

        // Accumulate the weighted sums of x and y coordinates using the cross product as a weight.
        // This weights vertices more heavily when they span a larger "area" relative to the origin.
        x_sum += (p1.x() + p2.x()) * cross_product;
        y_sum += (p1.y() + p2.y()) * cross_product;
    }

    // The total area is half the sum of cross products, as each cross product represents a parallelogram.
    // Dividing by 2 gives the area of the triangle formed by each edge and the origin.
    area *= 0.5;

    // The factor 1 / (6 * area) is derived from the formula for the centroid of a polygon:
    // The factor accounts for both the averaging of the coordinates and the normalization of the cross products.
    double factor = 1.0 / (6.0 * std::fabs(area));

    // Apply the factor to obtain the final centroid coordinates.
    // This scales the weighted sums to produce the average position of all vertices, weighted by area.
    center_.set_x(x_sum * factor);
    center_.set_x(y_sum * factor);

    return 0;
}

int ObstaclePolygon::calculatePolygonRadius() {
    // Cannot calculate radius without calculating centroid first
    int res = calculatePolygonCentroid();
    if (res) {
        return res;
    }

    radius_ = 0.0;

    // Iterate through each vertex to find the maximum distance from the centroid
    for (const auto& point : *this) {
        double dx = point.x() - center_.x();
        double dy = point.y() - center_.y();
        double distance = std::sqrt(dx * dx + dy * dy);

        if (distance > radius_) {
            radius_ = distance;
        }
    }

    return 0;
}

bool ObstaclePolygon::is_point_inside(const cogip_defs::Coords &p) const {
    for (size_t i = 0; i < size(); i++) {
        cogip_defs::Coords a = at(i);
        cogip_defs::Coords b = (i == (size() - 1) ? at(0) : at(i + 1));
        cogip_defs::Coords ab(b.x() - a.x(), b.y() - a.y());
        cogip_defs::Coords ap(p.x() - a.x(), p.y() - a.y());

        if (ab.x() * ap.y() - ab.y() * ap.x() <= 0) {
            return false;
        }
    }
    return true;
}

bool ObstaclePolygon::is_segment_crossing(const cogip_defs::Coords &a, const cogip_defs::Coords &b) const
{
    // Check if that segment crosses a polygon
    for (size_t i = 0; i < size(); i++) {
        const cogip_defs::Coords &p_next = ((i + 1 == size()) ? at(0) : at(i + 1));

        if (_is_segment_crossing_segment(a, b, at(i), p_next)) {
            return true;
        }

        // If A and B are vertices of the polygon
        int index = point_index(a);
        int index2 = point_index(b);
        // Consecutive vertices: no collision
        if (((index == 0) && (index2 == ((int)size() - 1)))
            || ((index2 == 0) && (index == ((int)size() - 1)))) {
            continue;
        }
        // If not consecutive vertices: collision
        if ((index >= 0) && (index2 >= 0) && (abs(index - index2) != 1)) {
            return true;
        }

        // If polygon vertice is on segment [AB]
        if (at(i).on_segment(a, b)) {
            return true;
        }
    }

    return false;
}

cogip_defs::Coords ObstaclePolygon::nearest_point(const cogip_defs::Coords &p) const
{
    double min = UINT32_MAX;
    cogip_defs::Coords tmp = p;

    for (const auto &point: *this) {
        double distance = p.distance(point);
        if (distance < min) {
            min = distance;
            tmp = point;
        }
    }

    return tmp;
}

void ObstaclePolygon::update_bounding_box_() {
    // Enlarge each point
    for (auto &point : *this) {
        double new_x = center_.x()
                       + (point.x() - center_.x()) * (1 + bounding_box_margin_);
        double new_y = center_.y()
                       + (point.y() - center_.y()) * (1 + bounding_box_margin_);
        point = cogip_defs::Coords(new_x, new_y);
    }
}

} // namespace obstacles

} // namespace cogip
