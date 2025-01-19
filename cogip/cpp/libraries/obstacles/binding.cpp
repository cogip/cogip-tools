// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "obstacles/ObstacleCircleList.hpp"
#include "obstacles/ObstaclePolygonList.hpp"
#include "obstacles/ObstacleRectangleList.hpp"
#include "models/binding.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>

#include <sstream>

namespace nb = nanobind;
using namespace nb::literals;

namespace cogip {

namespace obstacles {

using ObstacleCircleIterator = models::NbSharedArrayIterator<ObstacleCircle, ObstacleCircleList>;
using ObstaclePolygonIterator = models::NbSharedArrayIterator<ObstaclePolygon, ObstaclePolygonList>;
using ObstacleRectangleIterator = models::NbSharedArrayIterator<ObstacleRectangle, ObstacleRectangleList>;

NB_MODULE(obstacles, m) {
    auto models_module = nb::module_::import_("cogip.cpp.libraries.models");

    // Bind obstacle_circle_t struct
    nb::class_<obstacle_circle_t>(m, "ObstacleCircleT")
        .def(nb::init<>(), "Default constructor for obstacle_circle_t")
        .def_rw("id", &obstacle_circle_t::id, "Obstacle id")
        .def_rw("center", &obstacle_circle_t::center, "Obstacle center")
        .def_rw("radius", &obstacle_circle_t::radius, "Obstacle circumscribed circle radius")
        .def_rw("bounding_box_margin", &obstacle_circle_t::bounding_box_margin, "Margin for the bounding box")
        .def_rw("bounding_box_points_number", &obstacle_circle_t::bounding_box_points_number, "Number of points to define the bounding box")
        .def_rw("bounding_box", &obstacle_circle_t::bounding_box, "Precomputed bounding box for avoidance")
        .def("__repr__", [](const obstacle_circle_t& obj) {
            std::ostringstream oss;
            oss << obj;
            return oss.str();
        });

    nb::class_<Obstacle>(m, "Obstacle");

    // Bind ObstacleCircle class
    nb::class_<ObstacleCircle, Obstacle>(m, "ObstacleCircle")
        .def(nb::init<double, double, double, double, double, uint8_t, obstacle_circle_t*>(),
             "Constructor with initial values",
             "x"_a, "y"_a, "angle"_a, "radius"_a, "bounding_box_margin"_a, "bounding_box_points_number"_a, "data"_a = nullptr)
        .def(nb::init<const ObstacleCircle&, bool>(), "Deep copy constructor", "other"_a, "deep_copy"_a = false)
        .def("is_point_inside", nb::overload_cast<double, double>(&ObstacleCircle::is_point_inside), "Check if a point is inside the circle", "x"_a, "y"_a)
        .def("is_point_inside", nb::overload_cast<const models::Coords&>(&ObstacleCircle::is_point_inside), "Check if a point is inside the circle", "dest"_a)
        .def("is_segment_crossing", &ObstacleCircle::is_segment_crossing, "Check if a segment defined by two points crosses the circle", "a"_a, "b"_a)
        .def("nearest_point", &ObstacleCircle::nearest_point, "Find the nearest point on the circle's perimeter to a given point", "p"_a)
        .def_prop_rw("id", &ObstacleCircle::id, &ObstacleCircle::set_id, "Get or set the obstacle id")
        .def_prop_rw("center", &ObstacleCircle::center, &ObstacleCircle::set_center, "Get or set the obstacle center")
        .def_prop_ro("radius", &ObstacleCircle::radius, "Obstacle circumscribed circle radius")
        .def_prop_ro("bounding_box_margin", &ObstacleCircle::bounding_box_margin, "Margin for the bounding box")
        .def_prop_ro("bounding_box_points_number", &ObstacleCircle::bounding_box_points_number, "Obstacle circumscribed circle radius")
        .def_prop_ro("bounding_box", &ObstacleCircle::bounding_box, nb::rv_policy::reference_internal, "The bounding box")
        .def("__repr__", [](ObstacleCircle& obj) {
            std::ostringstream oss;
            oss << obj;
            return oss.str();
        });

    // Bind ObstacleCircleIterator class
    nb::class_<ObstacleCircleIterator>(m, "ObstacleCircleIterator")
        .def("__next__", &ObstacleCircleIterator::next, "Get the next element")  // Python's equivalent of `__next__`
        .def("__iter__", [](ObstacleCircleIterator& self) -> ObstacleCircleIterator& {
            return self;  // An iterator must return itself for `__iter__`
        });

    // Bind ObstacleCircleList class
    nb::class_<ObstacleCircleList>(m, "ObstacleCircleList")
        .def("clear", &ObstacleCircleList::clear, "Clear the list")
        .def("size", &ObstacleCircleList::size, "Get the number of coordinates")
        .def("max_size", &ObstacleCircleList::max_size, "Get the maximum number of coordinates")
        .def("get", &ObstacleCircleList::get, "Get Coords at index", "index"_a)
        .def("__getitem__", &ObstacleCircleList::operator[], "Get Coords at index", "index"_a)
        .def("append", nb::overload_cast<double, double, double, double, double, uint8_t, uint32_t>(&ObstacleCircleList::append), "Append obstacle", "x"_a, "y"_a, "angle"_a, "radius"_a, "bounding_box_margin"_a, "bounding_box_points_number"_a, "id"_a = 0)
        .def("set", nb::overload_cast<std::size_t, double, double, double, double, double, uint8_t, uint32_t>(&ObstacleCircleList::set), "Set coordinates at index", "index"_a, "x"_a, "y"_a, "angle"_a, "radius"_a, "bounding_box_margin"_a, "bounding_box_points_number"_a, "id"_a = 0)
     //    .def("__setitem__", nb::overload_cast<std::size_t, const ObstacleCircle&>(&ObstacleCircleList::set), "Set ObstacleCircle at index", "index"_a, "elem"_a)
        .def("get_index", &ObstacleCircleList::getIndex, "Return index of elem or -1 if not found", "elem"_a)
        .def("__len__", &ObstacleCircleList::size, "Return the length of the list")
        .def("__iter__", [](ObstacleCircleList& self) { return ObstacleCircleIterator(self, 0); }, "Return an iterator object")
        .def("__repr__", [](const ObstacleCircleList& self) {
            std::ostringstream oss;
            oss << "ObstacleCircleList(size=" << self.size() << ", max_size=" << self.max_size() << ")";
            return oss.str();
        })
    ;

    // Bind obstacle_polygon_t struct
    nb::class_<obstacle_polygon_t>(m, "ObstaclePolygonT")
        .def(nb::init<>(), "Default constructor for obstacle_polygon_t")
        .def_rw("id", &obstacle_polygon_t::id, "Obstacle id")
        .def_rw("center", &obstacle_polygon_t::center, "Obstacle center")
        .def_rw("radius", &obstacle_polygon_t::radius, "Obstacle circumscribed polygon radius")
        .def_rw("points", &obstacle_polygon_t::points, "Points defining the polygon")
        .def_rw("bounding_box_margin", &obstacle_polygon_t::bounding_box_margin, "Margin for the bounding box")
        .def_rw("bounding_box_points_number", &obstacle_polygon_t::bounding_box_points_number, "Number of points to define the bounding box")
        .def_rw("bounding_box", &obstacle_polygon_t::bounding_box, "Precomputed bounding box for avoidance")
        .def_rw("length_x", &obstacle_polygon_t::length_x, "Length of the rectangle along the X-axis")
        .def_rw("length_y", &obstacle_polygon_t::length_y, "Length of the rectangle along the Y-axis")
        .def("__repr__", [](const obstacle_polygon_t& obj) {
            std::ostringstream oss;
            oss << obj;
            return oss.str();
        });

    // Bind ObstaclePolygon class
    nb::class_<ObstaclePolygon, Obstacle>(m, "ObstaclePolygon")
        .def(nb::init<const models::CoordsList&, double, obstacle_polygon_t*>(),
             "Constructor with initial values",
             "points"_a, "bounding_box_margin"_a, "data"_a = nullptr)
        .def(nb::init<const ObstaclePolygon&, bool>(), "Deep copy constructor", "other"_a, "deep_copy"_a = false)
        .def("is_point_inside", nb::overload_cast<double, double>(&ObstaclePolygon::is_point_inside), "Check if a point is inside the circle", "x"_a, "y"_a)
        .def("is_point_inside", nb::overload_cast<const models::Coords&>(&ObstaclePolygon::is_point_inside), "Check if a point is inside the circle", "dest"_a)
        .def("is_segment_crossing", &ObstaclePolygon::is_segment_crossing, "Check if a segment defined by two points crosses the polygon", "a"_a, "b"_a)
        .def("nearest_point", &ObstaclePolygon::nearest_point, "Find the nearest point on the polygon's perimeter to a given point", "p"_a)
        .def_prop_rw("id", &ObstaclePolygon::id, &ObstaclePolygon::set_id, "Get or set the obstacle id")
        .def_prop_rw("center", &ObstaclePolygon::center, &ObstaclePolygon::set_center, "Get or set the obstacle center")
        .def_prop_ro("radius", &ObstaclePolygon::radius, "Obstacle circumscribed circle radius")
        .def_prop_ro("bounding_box_margin", &ObstaclePolygon::bounding_box_margin, "Margin for the bounding box")
        .def_prop_ro("bounding_box_points_number", &ObstaclePolygon::bounding_box_points_number, "Obstacle circumscribed circle radius")
        .def_prop_ro("bounding_box", &ObstaclePolygon::bounding_box, nb::rv_policy::reference_internal, "The bounding box")
        .def("__repr__", [](ObstaclePolygon& obj) {
            std::ostringstream oss;
            oss << obj;
            return oss.str();
        });

    // Bind ObstaclePolygonIterator class
    nb::class_<ObstaclePolygonIterator>(m, "ObstaclePolygonIterator")
        .def("__next__", &ObstaclePolygonIterator::next, "Get the next element")  // Python's equivalent of `__next__`
        .def("__iter__", [](ObstaclePolygonIterator& self) -> ObstaclePolygonIterator& {
            return self;  // An iterator must return itself for `__iter__`
        });

    // Bind ObstaclePolygonList class
    nb::class_<ObstaclePolygonList>(m, "ObstaclePolygonList")
        .def("clear", &ObstaclePolygonList::clear, "Clear the list")
        .def("size", &ObstaclePolygonList::size, "Get the number of coordinates")
        .def("max_size", &ObstaclePolygonList::max_size, "Get the maximum number of coordinates")
        .def("get", &ObstaclePolygonList::get, "Get Coords at index", "index"_a)
        .def("__getitem__", &ObstaclePolygonList::operator[], "Get Coords at index", "index"_a)
        .def("append", nb::overload_cast<const models::CoordsList&, double, uint32_t>(&ObstaclePolygonList::append), "Append obstacle", "points"_a, "bounding_box_margin"_a, "id"_a = 0)
        .def("set", nb::overload_cast<std::size_t, const models::CoordsList&, double, uint32_t>(&ObstaclePolygonList::set), "Set coordinates at index", "index"_a, "points"_a, "bounding_box_margin"_a, "id"_a = 0)
        .def("get_index", &ObstaclePolygonList::getIndex, "Return index of elem or -1 if not found", "elem"_a)
        .def("__len__", &ObstaclePolygonList::size, "Return the length of the list")
        .def("__iter__", [](ObstaclePolygonList& self) { return ObstaclePolygonIterator(self, 0); }, "Return an iterator object")
        .def("__repr__", [](const ObstaclePolygonList& self) {
            std::ostringstream oss;
            oss << "ObstaclePolygonList(size=" << self.size() << ", max_size=" << self.max_size() << ")";
            return oss.str();
        })
    ;

    // Bind ObstacleRectangle class
    nb::class_<ObstacleRectangle, ObstaclePolygon>(m, "ObstacleRectangle")
        .def(nb::init<double, double, double, double, double, double, obstacle_polygon_t*>(),
             "Constructor with initial values",
             "x"_a, "y"_a, "angle"_a, "length_x"_a, "length_y"_a, "bounding_box_margin"_a, "data"_a = nullptr)
        .def(nb::init<const ObstacleRectangle&, bool>(), "Deep copy constructor", "other"_a, "deep_copy"_a = false)
        .def("is_point_inside", nb::overload_cast<double, double>(&ObstacleRectangle::is_point_inside), "Check if a point is inside the circle", "x"_a, "y"_a)
        .def("is_point_inside", nb::overload_cast<const models::Coords&>(&ObstacleRectangle::is_point_inside), "Check if a point is inside the circle", "dest"_a)
        .def("is_segment_crossing", &ObstacleRectangle::is_segment_crossing, "Check if a segment defined by two points crosses the rectangle", "a"_a, "b"_a)
        .def("nearest_point", &ObstacleRectangle::nearest_point, "Find the nearest point on the rectangle's perimeter to a given point", "p"_a)
        .def_prop_rw("id", &ObstacleRectangle::id, &ObstacleRectangle::set_id, "Get or set the obstacle id")
        .def_prop_rw("center", &ObstacleRectangle::center, &ObstacleRectangle::set_center, "Get or set the obstacle center")
        .def_prop_ro("radius", &ObstacleRectangle::radius, "Obstacle circumscribed circle radius")
        .def_prop_ro("length_x", &ObstacleRectangle::length_x, "Obstacle circumscribed circle radius")
        .def_prop_ro("length_y", &ObstacleRectangle::length_y, "Obstacle circumscribed circle radius")
        .def_prop_ro("bounding_box_margin", &ObstacleRectangle::bounding_box_margin, "Margin for the bounding box")
        .def_prop_ro("bounding_box_points_number", &ObstacleRectangle::bounding_box_points_number, "Obstacle circumscribed circle radius")
        .def_prop_ro("bounding_box", &ObstacleRectangle::bounding_box, nb::rv_policy::reference_internal, "The bounding box")
        .def("__repr__", [](ObstacleRectangle& obj) {
            std::ostringstream oss;
            oss << obj;
            return oss.str();
        });

    // Bind ObstacleRectangleIterator class
    nb::class_<ObstacleRectangleIterator>(m, "ObstacleRectangleIterator")
        .def("__next__", &ObstacleRectangleIterator::next, "Get the next element")  // Python's equivalent of `__next__`
        .def("__iter__", [](ObstacleRectangleIterator& self) -> ObstacleRectangleIterator& {
            return self;  // An iterator must return itself for `__iter__`
        });

    // Bind ObstacleRectangleList class
    nb::class_<ObstacleRectangleList>(m, "ObstacleRectangleList")
        .def("clear", &ObstacleRectangleList::clear, "Clear the list")
        .def("size", &ObstacleRectangleList::size, "Get the number of coordinates")
        .def("max_size", &ObstacleRectangleList::max_size, "Get the maximum number of coordinates")
        .def("get", &ObstacleRectangleList::get, "Get Coords at index", "index"_a)
        .def("__getitem__", &ObstacleRectangleList::operator[], "Get Coords at index", "index"_a)
        .def("append", nb::overload_cast<double, double, double, double, double, double, uint32_t>(&ObstacleRectangleList::append), "Append obstacle", "x"_a, "y"_a, "angle"_a, "length_x"_a, "length_y"_a, "bounding_box_margin"_a, "id"_a = 0)
        .def("set", nb::overload_cast<std::size_t, double, double, double, double, double, double, uint32_t>(&ObstacleRectangleList::set), "Set coordinates at index", "index"_a, "x"_a, "y"_a, "angle"_a, "length_x"_a, "length_y"_a, "bounding_box_margin"_a, "id"_a = 0)
        .def("get_index", &ObstacleRectangleList::getIndex, "Return index of elem or -1 if not found", "elem"_a)
        .def("__len__", &ObstacleRectangleList::size, "Return the length of the list")
        .def("__iter__", [](ObstacleRectangleList& self) { return ObstacleRectangleIterator(self, 0); }, "Return an iterator object")
        .def("__repr__", [](const ObstacleRectangleList& self) {
            std::ostringstream oss;
            oss << "ObstacleRectangleList(size=" << self.size() << ", max_size=" << self.max_size() << ")";
            return oss.str();
        })
    ;

}

} // namespace obstacles

} // namespace cogip
