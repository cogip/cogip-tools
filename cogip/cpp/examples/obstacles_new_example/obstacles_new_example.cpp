// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "obstacles_new_example/obstacles_new_example.hpp"

#include "obstacles_new/Obstacle.hpp"

#include <cmath>
#include <cstddef>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using cogip::models::coords_t;
using cogip::obstacles_new::Obstacle;
using cogip::obstacles_new::obstacle_kind_t;
using cogip::obstacles_new::obstacle_t;

namespace obstacles_new_example {

namespace {

/// sizeof(obstacle_polygon_t) in the obstacles library.
constexpr std::size_t LEGACY_OBSTACLE_POLYGON_SIZE = 8280;

/// Absolute tolerance for the value comparisons, in mm.
constexpr double TOLERANCE = 1e-6;

std::size_t checks_total = 0;
std::size_t checks_failed = 0;

std::string fmt(double value)
{
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(2) << value;
    return oss.str();
}

std::string fmt(double x, double y)
{
    return fmt(x) + " " + fmt(y);
}

std::string fmt(double x, double y, double angle)
{
    return fmt(x) + " " + fmt(y) + " " + fmt(angle);
}

const char* kind_name(obstacle_kind_t kind)
{
    switch (kind) {
        case obstacle_kind_t::Circle:    return "Circle";
        case obstacle_kind_t::Rectangle: return "Rectangle";
        case obstacle_kind_t::Polygon:   return "Polygon";
    }
    return "Unknown";
}

void report(const char* name, bool passed, const std::string& actual, const std::string& expected)
{
    checks_total++;
    if (!passed) {
        checks_failed++;
    }
    std::cout << (passed ? "  ok   " : "  FAIL ")
              << std::left << std::setw(20) << name << " "
              << std::setw(24) << actual << " expected " << expected << "\n";
}

void check(const char* name, const std::string& actual, const std::string& expected)
{
    report(name, actual == expected, actual, expected);
}

void check(const char* name, double actual, double expected)
{
    report(name, std::fabs(actual - expected) < TOLERANCE, fmt(actual), fmt(expected));
}

void check(const char* name, std::size_t actual, std::size_t expected)
{
    report(name, actual == expected, std::to_string(actual), std::to_string(expected));
}

void check(const char* name, bool actual, bool expected)
{
    report(name, actual == expected, actual ? "true" : "false", expected ? "true" : "false");
}

/// Twice the signed area of the outline.
double signed_area_twice(const Obstacle& obstacle)
{
    const std::size_t count = obstacle.point_count();
    double total = 0.0;
    for (std::size_t i = 0, j = count - 1; i < count; j = i++) {
        total += obstacle.point(j).x * obstacle.point(i).y
               - obstacle.point(i).x * obstacle.point(j).y;
    }
    return total;
}

/// Length of the edge between vertex @p index and the next one.
double edge_length(const Obstacle& obstacle, std::size_t index)
{
    const std::size_t next = (index + 1) % obstacle.point_count();
    return std::hypot(
        obstacle.point(next).x - obstacle.point(index).x,
        obstacle.point(next).y - obstacle.point(index).y);
}

/// Distance from the centre to vertex @p index.
double circumradius(const Obstacle& obstacle, std::size_t index)
{
    return std::hypot(
        obstacle.point(index).x - obstacle.center().x,
        obstacle.point(index).y - obstacle.center().y);
}

/// Mean of the outline vertices.
coords_t outline_mean(const Obstacle& obstacle)
{
    coords_t mean{0.0, 0.0};
    for (std::size_t i = 0; i < obstacle.point_count(); i++) {
        mean.x += obstacle.point(i).x;
        mean.y += obstacle.point(i).y;
    }
    mean.x /= static_cast<double>(obstacle.point_count());
    mean.y /= static_cast<double>(obstacle.point_count());
    return mean;
}

void print_outline(const Obstacle& obstacle)
{
    for (std::size_t i = 0; i < obstacle.point_count(); i++) {
        std::cout << "       [" << i << "] " << fmt(obstacle.point(i).x, obstacle.point(i).y) << "\n";
    }
}

} // namespace

void run()
{
    std::cout << "[sizes]\n";
    check("sizeof(obstacle_t)", sizeof(obstacle_t), std::size_t{296});
    check("sizeof(legacy)", LEGACY_OBSTACLE_POLYGON_SIZE, std::size_t{8280});

    std::cout << "\n[make_circle 1000 800 150]\n";
    const Obstacle circle = Obstacle::make_circle(1000, 800, 150);
    check("kind", std::string(kind_name(circle.kind())), std::string("Circle"));
    check("point_count", circle.point_count(), std::size_t{1});
    check("corner_radius", circle.corner_radius(), 150.0);
    check("center", fmt(circle.center().x, circle.center().y, circle.center().angle),
          fmt(1000.0, 800.0, 0.0));
    check("outline[0]", fmt(circle.point(0).x, circle.point(0).y), fmt(1000.0, 800.0));

    std::cout << "\n[make_rectangle 500 500 30 200 100]\n";
    Obstacle rectangle = Obstacle::make_rectangle(500, 500, 30, 200, 100);
    print_outline(rectangle);
    check("kind", std::string(kind_name(rectangle.kind())), std::string("Rectangle"));
    check("point_count", rectangle.point_count(), std::size_t{4});
    check("corner_radius", rectangle.corner_radius(), 0.0);
    check("signed_area_x2", signed_area_twice(rectangle), 2.0 * 200.0 * 100.0);
    check("edge[0]", edge_length(rectangle, 0), 200.0);
    check("edge[1]", edge_length(rectangle, 1), 100.0);
    check("edge[2]", edge_length(rectangle, 2), 200.0);
    check("edge[3]", edge_length(rectangle, 3), 100.0);
    check("circumradius[0]", circumradius(rectangle, 0), std::hypot(100.0, 50.0));
    check("outline_mean", fmt(outline_mean(rectangle).x, outline_mean(rectangle).y),
          fmt(500.0, 500.0));

    std::cout << "\n[make_polygon, input clockwise]\n";
    const std::vector<coords_t> input = {
        {0.0, 0.0}, {0.0, 100.0}, {200.0, 100.0}, {200.0, 0.0},
    };
    std::cout << "    input\n";
    for (std::size_t i = 0; i < input.size(); i++) {
        std::cout << "       [" << i << "] " << fmt(input[i].x, input[i].y) << "\n";
    }
    const Obstacle polygon = Obstacle::make_polygon(input.data(), input.size());
    std::cout << "    stored\n";
    print_outline(polygon);
    check("kind", std::string(kind_name(polygon.kind())), std::string("Polygon"));
    check("point_count", polygon.point_count(), std::size_t{4});
    check("signed_area_x2", signed_area_twice(polygon), 2.0 * 200.0 * 100.0);
    check("center", fmt(polygon.center().x, polygon.center().y, polygon.center().angle),
          fmt(100.0, 50.0, 0.0));

    std::cout << "\n[set_center 1500 200 120]\n";
    rectangle.set_center(cogip::models::pose_t{1500.0, 200.0, 120.0});
    print_outline(rectangle);
    check("center", fmt(rectangle.center().x, rectangle.center().y, rectangle.center().angle),
          fmt(1500.0, 200.0, 120.0));
    check("outline_mean", fmt(outline_mean(rectangle).x, outline_mean(rectangle).y),
          fmt(1500.0, 200.0));
    check("edge[0]", edge_length(rectangle, 0), 200.0);
    check("edge[1]", edge_length(rectangle, 1), 100.0);
    check("signed_area_x2", signed_area_twice(rectangle), 2.0 * 200.0 * 100.0);
    check("circumradius[0]", circumradius(rectangle, 0), std::hypot(100.0, 50.0));

    std::cout << "\n[copy]\n";
    Obstacle original = Obstacle::make_circle(100, 100, 50);
    const Obstacle shallow(original);
    const Obstacle deep(original, true);
    original.set_id(42);
    original.set_enabled(false);
    check("original.id", static_cast<std::size_t>(original.id()), std::size_t{42});
    check("original.enabled", original.enabled(), false);
    check("shallow.id", static_cast<std::size_t>(shallow.id()), std::size_t{42});
    check("shallow.enabled", shallow.enabled(), false);
    check("deep.id", static_cast<std::size_t>(deep.id()), std::size_t{0});
    check("deep.enabled", deep.enabled(), true);

    std::cout << "\n[bounds]\n";
    std::string outcome = "no throw";
    try {
        circle.point(1);
    } catch (const std::runtime_error&) {
        outcome = "throws";
    }
    check("point(1) on 1 point", outcome, std::string("throws"));

    outcome = "no throw";
    const std::vector<coords_t> too_many(17, coords_t{0.0, 0.0});
    try {
        Obstacle::make_polygon(too_many.data(), too_many.size());
    } catch (const std::runtime_error&) {
        outcome = "throws";
    }
    check("make_polygon 17 points", outcome, std::string("throws"));

    outcome = "no throw";
    try {
        Obstacle::make_polygon(nullptr, 0);
    } catch (const std::runtime_error&) {
        outcome = "throws";
    }
    check("make_polygon 0 point", outcome, std::string("throws"));

    std::cout << "\n[summary]\n"
              << "  checks " << checks_total << "\n"
              << "  failed " << checks_failed << "\n";
}

} // namespace obstacles_new_example
