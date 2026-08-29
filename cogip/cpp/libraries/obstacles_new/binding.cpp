// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "obstacles_new/Obstacle.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/stl/pair.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>

#include <sstream>
#include <vector>

namespace nb = nanobind;
using namespace nb::literals;

namespace cogip {

namespace obstacles_new {

NB_MODULE(obstacles_new, m) {
    nb::module_::import_("cogip.cpp.libraries.models");

    // Bind obstacle_kind_t enum. It has to come before obstacle_t, whose kind member refers to it.
    nb::enum_<obstacle_kind_t>(m, "ObstacleKind")
        .value("Circle", obstacle_kind_t::Circle, "One outline point, corner_radius > 0")
        .value("Rectangle", obstacle_kind_t::Rectangle, "Four outline points, corner_radius == 0")
        .value("Polygon", obstacle_kind_t::Polygon, "Arbitrary convex outline, corner_radius == 0");

    // Bind obstacle_t struct.
    // The outline array is deliberately not exposed here, the same way coords_list_t does not
    // expose its elems: reading it goes through the Obstacle class.
    nb::class_<obstacle_t>(m, "ObstacleT")
        .def(nb::init<>(), "Default constructor for obstacle_t")
        .def_rw("id", &obstacle_t::id, "Obstacle id")
        .def_rw("kind", &obstacle_t::kind, "Shape family, for display only")
        .def_rw("enabled", &obstacle_t::enabled, "False when the obstacle must be ignored")
        .def_rw("center", &obstacle_t::center, "Rigid body reference point")
        .def_rw("corner_radius", &obstacle_t::corner_radius, "Dilation radius in mm")
        .def_ro("outline_count", &obstacle_t::outline_count, "Number of valid outline vertices")
        .def("__repr__", [](const obstacle_t& obj) {
            std::ostringstream oss;
            oss << obj;
            return oss.str();
        });

    // Bind Obstacle class.
    nb::class_<Obstacle>(m, "Obstacle")
        .def(nb::init<obstacle_t*>(), "Constructor with existing data", "data"_a = nullptr)
        .def(nb::init<const Obstacle&, bool>(), "Copy constructor", "other"_a, "deep_copy"_a = false)
        .def_static(
            "make_circle", &Obstacle::make_circle,
            "Build a disc, stored as one point dilated by its radius",
            "x"_a, "y"_a, "radius"_a, "data"_a = nullptr)
        .def_static(
            "make_rectangle", &Obstacle::make_rectangle,
            "Build a rectangle, corners laid out counter-clockwise",
            "x"_a, "y"_a, "angle"_a, "length_x"_a, "length_y"_a, "data"_a = nullptr)
        .def_static(
            "make_polygon",
            // Takes a list of (x, y) tuples rather than a list of CoordsT: coords_t is bound
            // without any constructor, so it cannot be built from Python.
            [](const std::vector<std::pair<double, double>>& points, obstacle_t* data) {
                std::vector<models::coords_t> coords;
                coords.reserve(points.size());
                for (const auto& point : points) {
                    coords.push_back(models::coords_t{point.first, point.second});
                }
                return Obstacle::make_polygon(coords.data(), coords.size(), data);
            },
            "Build an arbitrary convex polygon from a list of (x, y) tuples",
            "points"_a, "data"_a = nullptr)
        .def_prop_rw("id", &Obstacle::id, &Obstacle::set_id, "Get or set the obstacle id")
        .def_prop_rw("enabled", &Obstacle::enabled, &Obstacle::set_enabled, "Get or set the enabled flag")
        .def_prop_ro("kind", &Obstacle::kind, "Shape family")
        .def_prop_ro("corner_radius", &Obstacle::corner_radius, "Dilation radius in mm")
        // Returned by copy on purpose: an internal reference would let `obstacle.center.x = ...`
        // move the centre without moving the outline. set_center() is the only way in.
        .def_prop_ro("center", &Obstacle::center, nb::rv_policy::copy, "Rigid body reference point")
        .def(
            "set_center",
            [](Obstacle& self, double x, double y, double angle) {
                self.set_center(models::pose_t{x, y, angle});
            },
            "Move the obstacle as a rigid body, carrying its outline along",
            "x"_a, "y"_a, "angle"_a)
        .def("__len__", &Obstacle::point_count, "Return the number of outline vertices")
        .def("__getitem__", &Obstacle::point, nb::rv_policy::copy, "Get an outline vertex", "index"_a)
        .def("__repr__", [](const Obstacle& obj) {
            std::ostringstream oss;
            oss << obj;
            return oss.str();
        });
}

} // namespace obstacles_new

} // namespace cogip
