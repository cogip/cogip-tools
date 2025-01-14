// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "models/CoordsList.hpp"
#include "models/Pose.hpp"
#include "models/binding.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>

#include <sstream>

namespace nb = nanobind;
using namespace nb::literals;

namespace cogip {

namespace models {

using CoordsIterator = NbSharedArrayIterator<Coords, CoordsList>;

NB_MODULE(models, m) {

    m.doc() = "models module for Python bindings";

    // Bind coords_t structure
    nb::class_<coords_t>(m, "CoordsT")
        .def_rw("x", &coords_t::x, "X-coordinate")
        .def_rw("y", &coords_t::y, "Y-coordinate")
        .def("__repr__", [](const coords_t& coords) {
            std::ostringstream oss;
            oss << coords;
            return oss.str();
        })
    ;

    // Bind Coords class
    nb::class_<Coords>(m, "Coords")
        .def(
            nb::init<double, double, coords_t*>(),
            "Constructor with initial values",
            "x"_a = 0.0,
            "y"_a = 0.0,
            "data"_a = nullptr
        )
        .def(nb::init<const Coords&, bool>(), "Copy constructor", "other"_a, "deep_copy"_a = false)
        .def("__assign__", [](Coords &self, const Coords &other) -> Coords& { return self = other; }, "Assignment operator")
        .def_prop_rw("x", &Coords::x, &Coords::set_x, "Get or set the X coordinate")
        .def_prop_rw("y", &Coords::y, &Coords::set_y, "Get or set the Y coordinate")
        .def("distance", nb::overload_cast<double, double>(&Coords::distance, nb::const_), "Compute the distance to a destination point", "x"_a, "y"_a)
        .def("distance", nb::overload_cast<const Coords&>(&Coords::distance, nb::const_), "Compute the distance to a destination point", "dest"_a)
        .def("on_segment", &Coords::on_segment, "Check if this point is on a segment defined by two points", "a"_a, "b"_a)
        .def("__eq__", [](const Coords &self, const Coords &other) { return self == other; }, "Equality operator for Coords")
        .def("__repr__", [](const Coords &coords) {
            std::ostringstream oss;
            oss << coords;
            return oss.str();
        })
    ;

    // Bind coords_list_t structure
    nb::class_<coords_list_t>(m, "CoordsListT")
        .def("__repr__", [](const coords_list_t& list) {
            std::ostringstream oss;
            oss << list;
            return oss.str();
        })
    ;

    // Bind CoordsIterator class
    nb::class_<CoordsIterator>(m, "CoordsArrayIterator")
        .def("__next__", &CoordsIterator::next, "Get the next element")  // Python's equivalent of `__next__`
        .def("__iter__", [](CoordsIterator& self) -> CoordsIterator& {
            return self;  // An iterator must return itself for `__iter__`
        });

    // Bind CoordsList class
    nb::class_<CoordsList>(m, "CoordsList")
        .def(nb::init<coords_list_t*>(), "Constructor with existing data", "coords_list"_a = nullptr)
        .def("clear", &CoordsList::clear, "Clear the list")
        .def("size", &CoordsList::size, "Get the number of coordinates")
        .def("max_size", &CoordsList::max_size, "Get the maximum number of coordinates")
        .def("get", &CoordsList::get, "Get Coords at index", "index"_a)
        .def("__getitem__", &CoordsList::operator[], "Get Coords at index", "index"_a)
        .def("append", nb::overload_cast<double, double>(&CoordsList::append), "Append coordinates", "x"_a, "y"_a)
        .def("append", nb::overload_cast<const Coords&>(&CoordsList::append), "Append Coords", "coords"_a)
        .def("set", nb::overload_cast<std::size_t, double, double>(&CoordsList::set), "Set coordinates at index", "index"_a, "x"_a, "y"_a)
        .def("set", nb::overload_cast<std::size_t, const Coords&>(&CoordsList::set), "Set Coords at index", "index"_a, "coords"_a)
        .def("__setitem__", nb::overload_cast<std::size_t, const Coords&>(&CoordsList::set), "Set Coords at index", "index"_a, "coords"_a)
        .def("get_index", &CoordsList::getIndex, "Return index of elem or -1 if not found", "elem"_a)
        .def("__len__", &CoordsList::size, "Return the length of the list")
        .def("__iter__", [](CoordsList& self) { return CoordsIterator(self, 0); }, "Return an iterator object")
        .def("__repr__", [](const CoordsList& self) {
            std::ostringstream oss;
            oss << "CoordsList(size=" << self.size() << ", max_size=" << self.max_size() << ")";
            return oss.str();
        })
    ;

    // Bind polar_t structure
    nb::class_<polar_t>(m, "PolarT")
        .def_rw("distance", &polar_t::distance, "Distance in polar coordinates")
        .def_rw("angle", &polar_t::angle, "Angle in polar coordinates")
        .def("__repr__", [](const polar_t& polar) {
            std::ostringstream oss;
            oss << polar;
            return oss.str();
        })
    ;

    // Bind Polar class
    nb::class_<Polar>(m, "Polar")
        .def(
            nb::init<double, double, polar_t*>(),
            "Constructor with initial values",
            "distance"_a = 0.0,
            "angle"_a = 0.0,
            "data"_a = nullptr
        )
        .def(nb::init<const Polar&, bool>(), "Copy constructor", "other"_a, "deep_copy"_a = false)
        .def("__assign__", [](Polar &self, const Polar &other) -> Polar& { return self = other; }, "Assignment operator")
        .def_prop_rw("distance", &Polar::distance, &Polar::set_distance, "Get or set the distance in polar coordinates")
        .def_prop_rw("angle", &Polar::angle, &Polar::set_angle, "Get or set the angle in polar coordinates")
        .def("reverse_distance", &Polar::reverse_distance, "Reverse the distance")
        .def("reverse_angle", &Polar::reverse_angle, "Reverse the angle")
        .def("reverse", &Polar::reverse, "Reverse both distance and angle")
        .def("__repr__", [](const Polar &polar) {
            std::ostringstream oss;
            oss << polar;
            return oss.str();
        })
    ;

    // Bind pose_t structure
    nb::class_<pose_t>(m, "PoseT")
        .def_rw("x", &pose_t::x, "X coordinate")
        .def_rw("y", &pose_t::y, "Y coordinate")
        .def_rw("angle", &pose_t::angle, "Orientation angle")
    ;

    // Bind Pose class
    nb::class_<Pose, Coords>(m, "Pose")
        .def(nb::init<double, double, double, pose_t*>(),
            "Constructor",
            "x"_a = 0.0,
            "y"_a = 0.0,
            "angle"_a = 0.0,
            "data"_a = nullptr
        )
        .def(nb::init<const Pose&, bool>(), "Copy constructor", "other"_a, "deep_copy"_a = false)
        .def("__assign__", [](Pose &self, const Pose &other) -> Pose& { return self = other; }, "Assignment operator")
        .def_prop_rw("x", &Pose::x, &Pose::set_x, "Get or set the X coordinate")
        .def_prop_rw("y", &Pose::y, &Pose::set_y, "Get or set the Y coordinate")
        .def_prop_rw("coords", &Pose::coords, &Pose::set_coords, "Get/set coordinates to/from a Coords object")
        .def_prop_rw("angle", &Pose::angle, &Pose::set_angle, "Get or set the orientation angle")
        .def("__eq__", &Pose::operator==, "Equality operator")
        .def("__sub__", &Pose::operator-, "Subtraction operator returning Polar object", "p"_a)
        .def(
            "__repr__",
            [](const Pose& pose) {
                std::ostringstream oss;
                oss << pose;
                return oss.str();
            }
        )
    ;
}

} // namespace models

} // namespace cogip
