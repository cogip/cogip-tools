// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "models/CoordsList.hpp"
#include "models/CircleList.hpp"
#include "models/Pose.hpp"
#include "models/PoseBuffer.hpp"
#include "models/PoseOrderList.hpp"
#include "models/binding.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>

#include <sstream>

namespace nb = nanobind;
using namespace nb::literals;

namespace cogip {

namespace models {

using CoordsIterator = NbSharedArrayIterator<Coords, CoordsList>;
using CircleIterator = NbSharedArrayIterator<Circle, CircleList>;
using PoseOrderIterator = NbSharedArrayIterator<PoseOrder, PoseOrderList>;

NB_MODULE(models, m) {

    m.doc() = "models module for Python bindings";

    // Bind MotionDirection enum
    nb::enum_<MotionDirection>(m, "MotionDirection", "Motion direction mode for path navigation")
        .value("bidirectional", MotionDirection::bidirectional, "Robot can move forward or backward (choose optimal)")
        .value("forward_only", MotionDirection::forward_only, "Force forward motion only")
        .value("backward_only", MotionDirection::backward_only, "Force backward motion only")
        .export_values();

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

    // Bind pose_buffer_t structure
    nb::class_<pose_buffer_t>(m, "PoseBufferT")
        .def_rw("head", &pose_buffer_t::head, "Next write pose")
        .def_rw("tail", &pose_buffer_t::tail, "Oldest pose")
        .def("__repr__", [](const pose_buffer_t& buffer) {
            std::ostringstream oss;
            oss << buffer;
            return oss.str();
        })
    ;

    // Bind PoseBuffer class
    nb::class_<PoseBuffer>(m, "PoseBuffer")
        .def(nb::init<pose_buffer_t*>(), "Constructor", "data"_a = nullptr)
        .def_prop_ro("head", &PoseBuffer::head, "Next write pose")
        .def_prop_ro("tail", &PoseBuffer::tail, "Oldest pose")
        .def("push", &PoseBuffer::push, "Get last pose pushed in the buffer", "x"_a, "y"_a, "angle"_a)
        .def_prop_ro("last", &PoseBuffer::last, "Get last pose pushed in the buffer")
        .def("get", &PoseBuffer::get, "Get the N-th position from head (0 is the most recent)", "n"_a)
        .def("__repr__", [](const PoseBuffer &buffer) {
            std::ostringstream oss;
            oss << buffer;
            return oss.str();
        })
    ;

    // Bind pose_order_t structure
    nb::class_<pose_order_t>(m, "PoseOrderT")
        .def_rw("x", &pose_order_t::x, "X-coordinate of the pose")
        .def_rw("y", &pose_order_t::y, "Y-coordinate of the pose")
        .def_rw("angle", &pose_order_t::angle, "Orientation angle of the pose in degrees")
        .def_rw("max_speed_linear", &pose_order_t::max_speed_linear, "Maximum linear speed for the pose (in percent of the robot max speed)")
        .def_rw("max_speed_angular", &pose_order_t::max_speed_angular, "Maximum angular speed for the pose (in percent of the robot max speed)")
        .def_rw("motion_direction", &pose_order_t::motion_direction, "Motion direction mode (bidirectional, forward_only, or backward_only)")
        .def_rw("bypass_anti_blocking", &pose_order_t::bypass_anti_blocking, "True if the pose bypasses anti-blocking, false otherwise")
        .def_rw("bypass_final_orientation", &pose_order_t::bypass_final_orientation, "True if the pose bypasses final orientation, false otherwise")
        .def_rw("timeout_ms", &pose_order_t::timeout_ms, "Timeout in milliseconds for the pose to be reached")
        .def_rw("is_intermediate", &pose_order_t::is_intermediate, "True if the pose is an intermediate pose, false if it is a final pose")
        .def("__repr__", [](const pose_order_t& order) {
            std::ostringstream oss;
            oss << order;
            return oss.str();
        })
    ;

    // Bind PoseOrder class
    nb::class_<PoseOrder>(m, "PoseOrder")
        .def(
            nb::init<double, double, double, std::uint8_t, std::uint8_t, MotionDirection, bool, bool, std::uint32_t, bool, pose_order_t*>(),
            "Constructor with initial values",
            "x"_a = 0.0,
            "y"_a = 0.0,
            "angle"_a = 0.0,
            "max_speed_linear"_a = 100,
            "max_speed_angular"_a = 100,
            "motion_direction"_a = MotionDirection::bidirectional,
            "bypass_anti_blocking"_a = false,
            "bypass_final_orientation"_a = false,
            "timeout_ms"_a = 0,
            "is_intermediate"_a = false,
            "data"_a = nullptr
        )
        .def(nb::init<const PoseOrder&, bool>(), "Copy constructor", "other"_a, "deep_copy"_a = false)
        .def("__assign__", [](PoseOrder &self, const PoseOrder &other) -> PoseOrder& { return self = other; }, "Assignment operator")
        .def_prop_rw("x", &PoseOrder::x, &PoseOrder::set_x, "Get or set the X coordinate")
        .def_prop_rw("y", &PoseOrder::y, &PoseOrder::set_y, "Get or set the Y coordinate")
        .def_prop_rw("angle", &PoseOrder::angle, &PoseOrder::set_angle, "Get or set the orientation angle")
        .def_prop_rw("max_speed_linear", &PoseOrder::max_speed_linear, &PoseOrder::set_max_speed_linear, "Get or set the maximum linear speed (in percent of the robot max speed)")
        .def_prop_rw("max_speed_angular", &PoseOrder::max_speed_angular, &PoseOrder::set_max_speed_angular, "Get or set the maximum angular speed (in percent of the robot max speed)")
        .def_prop_rw("motion_direction", &PoseOrder::motion_direction, &PoseOrder::set_motion_direction, "Get or set the motion direction mode")
        .def_prop_rw("bypass_anti_blocking", &PoseOrder::bypass_anti_blocking, &PoseOrder::set_bypass_anti_blocking, "Get or set if anti-blocking is bypassed")
        .def_prop_rw("bypass_final_orientation", &PoseOrder::bypass_final_orientation, &PoseOrder::set_bypass_final_orientation, "Get or set if final orientation is bypassed")
        .def_prop_rw("timeout_ms", &PoseOrder::timeout_ms, &PoseOrder::set_timeout_ms, "Get or set the timeout in milliseconds for the pose to be reached")
        .def_prop_rw("is_intermediate", &PoseOrder::is_intermediate, &PoseOrder::set_is_intermediate, "Get or set if the pose is intermediate")
        .def("__repr__", [](const PoseOrder& order) {
            std::ostringstream oss;
            oss << order;
            return oss.str();
        })
    ;

    // Bind pose_order_list_t structure
    nb::class_<pose_order_list_t>(m, "PoseOrderListT")
        .def("__repr__", [](const pose_order_list_t& list) {
            std::ostringstream oss;
            oss << list;
            return oss.str();
        })
    ;

    // Bind PoseOrderIterator class
    nb::class_<PoseOrderIterator>(m, "PoseOrderArrayIterator")
        .def("__next__", &PoseOrderIterator::next, "Get the next element")  // Python's equivalent of `__next__`
        .def("__iter__", [](PoseOrderIterator& self) -> PoseOrderIterator& {
            return self;  // An iterator must return itself for `__iter__`
        });

    // Bind PoseOrderList class
    nb::class_<PoseOrderList>(m, "PoseOrderList")
        .def(nb::init<>(), "Default constructor")
        .def("clear", &PoseOrderList::clear, "Clear the list")
        .def("size", &PoseOrderList::size, "Get the number of pose orders")
        .def("max_size", &PoseOrderList::max_size, "Get the maximum number of pose orders")
        .def("get", &PoseOrderList::get, "Get PoseOrder at index", "index"_a)
        .def("__getitem__", &PoseOrderList::operator[], "Get PoseOrder at index", "index"_a)
        .def("append", nb::overload_cast<double, double, double, std::uint8_t, std::uint8_t, MotionDirection, bool, bool, std::uint32_t, bool>(&PoseOrderList::append), "Append PoseOrder with initial values",
            "x"_a = 0.0,
            "y"_a = 0.0,
            "angle"_a = 0.0,
            "max_speed_linear"_a = 100,
            "max_speed_angular"_a = 100,
            "motion_direction"_a = MotionDirection::bidirectional,
            "bypass_anti_blocking"_a = false,
            "bypass_final_orientation"_a = false,
            "timeout_ms"_a = 0,
            "is_intermediate"_a = false
        )
        .def("append", nb::overload_cast<const PoseOrder&>(&PoseOrderList::append), "Append PoseOrder object", "pose_order"_a)
        .def("set", nb::overload_cast<std::size_t, double, double, double, std::uint8_t, std::uint8_t, MotionDirection, bool, bool, std::uint32_t, bool>(&PoseOrderList::set), "Set PoseOrder at index",
            "index"_a,
            "x"_a = 0.0,
            "y"_a = 0.0,
            "angle"_a = 0.0,
            "max_speed_linear"_a = 100,
            "max_speed_angular"_a = 100,
            "motion_direction"_a = MotionDirection::bidirectional,
            "bypass_anti_blocking"_a = false,
            "bypass_final_orientation"_a = false,
            "timeout_ms"_a = 0,
            "is_intermediate"_a = false
        )
        .def("set", nb::overload_cast<std::size_t, const PoseOrder&>(&PoseOrderList::set), "Set PoseOrder at index", "index"_a, "pose_order"_a)
        .def("__setitem__", nb::overload_cast<std::size_t, const PoseOrder&>(&PoseOrderList::set), "Set PoseOrder at index", "index"_a, "pose_order"_a)
        .def("__len__", &PoseOrderList::size, "Return the length of the list")
        .def("__iter__", [](PoseOrderList& self) { return PoseOrderIterator(self, 0); }, "Return an iterator object")
        .def("__repr__", [](const PoseOrderList& self) {
            std::ostringstream oss;
            oss << "PoseOrderList(size=" << self.size() << ", max_size=" << self.max_size() << ")";
            return oss.str();
        })
    ;

    // Bind circle_t structure
    nb::class_<circle_t>(m, "CircleT")
        .def_rw("x", &circle_t::x, "X coordinate")
        .def_rw("y", &circle_t::y, "Y coordinate")
        .def_rw("radius", &circle_t::radius, "Radius")
    ;

    // Bind Circle class
    nb::class_<Circle, Coords>(m, "Circle")
        .def(nb::init<double, double, double, circle_t*>(),
            "Constructor",
            "x"_a = 0.0,
            "y"_a = 0.0,
            "radius"_a = 0.0,
            "data"_a = nullptr
        )
        .def(nb::init<const Circle&, bool>(), "Copy constructor", "other"_a, "deep_copy"_a = false)
        .def("__assign__", [](Circle &self, const Circle &other) -> Circle& { return self = other; }, "Assignment operator")
        .def_prop_rw("x", &Circle::x, &Circle::set_x, "Get or set the X coordinate")
        .def_prop_rw("y", &Circle::y, &Circle::set_y, "Get or set the Y coordinate")
        .def_prop_rw("coords", &Circle::coords, &Circle::set_coords, "Get/set coordinates to/from a Coords object")
        .def_prop_rw("radius", &Circle::radius, &Circle::set_radius, "Get or set the radius")
        .def("__eq__", [](const Circle &self, const Circle &other) { return self == other; }, "Equality operator for Circle")
        .def(
            "__repr__",
            [](const Circle& circle) {
                std::ostringstream oss;
                oss << circle;
                return oss.str();
            }
        )
    ;

    // Bind circle_list_t structure
    nb::class_<circle_list_t>(m, "CircleListT")
        .def("__repr__", [](const circle_list_t& list) {
            std::ostringstream oss;
            oss << list;
            return oss.str();
        })
    ;

    // Bind CircleIterator class
    nb::class_<CircleIterator>(m, "CircleArrayIterator")
        .def("__next__", &CircleIterator::next, "Get the next element")  // Python's equivalent of `__next__`
        .def("__iter__", [](CircleIterator& self) -> CircleIterator& {
            return self;  // An iterator must return itself for `__iter__`
        })
    ;

    // Bind CircleList class
    nb::class_<CircleList>(m, "CircleList")
        .def(nb::init<circle_list_t*>(), "Constructor with existing data", "circle_list"_a = nullptr)
        .def("clear", &CircleList::clear, "Clear the list")
        .def("size", &CircleList::size, "Get the number of circles")
        .def("max_size", &CircleList::max_size, "Get the maximum number of circles")
        .def("get", &CircleList::get, "Get Circle at index", "index"_a)
        .def("__getitem__", &CircleList::operator[], "Get Circle at index", "index"_a)
        .def("append", nb::overload_cast<double, double, double>(&CircleList::append), "Append circle", "x"_a, "y"_a, "radius"_a = 0.0)
        .def("append", nb::overload_cast<const Circle&>(&CircleList::append), "Append Circle", "circle"_a)
        .def("set", nb::overload_cast<std::size_t, double, double, double>(&CircleList::set), "Set circle at index", "index"_a, "x"_a, "y"_a, "radius"_a = 0.0)
        .def("set", nb::overload_cast<std::size_t, const Circle&>(&CircleList::set), "Set Circle at index", "index"_a, "circle"_a)
        .def("__setitem__", nb::overload_cast<std::size_t, const Circle&>(&CircleList::set), "Set Circle at index", "index"_a, "circle"_a)
        .def("get_index", &CircleList::getIndex, "Return index of elem or -1 if not found", "elem"_a)
        .def("__len__", &CircleList::size, "Return the length of the list")
        .def("__iter__", [](CircleList& self) { return CircleIterator(self, 0); }, "Return an iterator object")
        .def("__repr__", [](const CircleList& self) {
            std::ostringstream oss;
            oss << "CircleList(size=" << self.size() << ", max_size=" << self.max_size() << ")";
            return oss.str();
        })
    ;
}

} // namespace models

} // namespace cogip
