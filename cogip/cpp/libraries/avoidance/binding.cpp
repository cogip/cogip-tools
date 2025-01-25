// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level
// directory for more details.

#include "avoidance/Avoidance.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>

#include <sstream>

namespace nb = nanobind;
using namespace nb::literals;

namespace cogip {

namespace avoidance {

NB_MODULE(avoidance, m) {
    auto models_module = nb::module_::import_("cogip.cpp.libraries.models");
    auto obstacles_module = nb::module_::import_("cogip.cpp.libraries.obstacles");

    // Bind Avoidance class
    nb::class_<Avoidance>(m, "Avoidance")
        .def(nb::init<const obstacles::ObstaclePolygon&>(), "Constructor initializing the avoidance system with obstacle borders", "borders"_a)
        .def("is_point_in_obstacles", &Avoidance::is_point_in_obstacles, "Checks if a point is inside any obstacle", "point"_a, "filter"_a = nullptr)
        .def("get_path_size", &Avoidance::get_path_size, "Retrieves the size of the computed avoidance path")
        .def("get_path_pose", &Avoidance::get_path_pose, "Retrieves the pose at a specific index in the computed path", "index"_a)
        .def("avoidance", &Avoidance::avoidance, "Builds the avoidance graph between the start and finish positions", "start"_a, "finish"_a)
        .def("check_recompute", &Avoidance::check_recompute, "Checks whether recomputation of the path is necessary", "start"_a, "stop"_a)
        .def("borders", &Avoidance::borders, nb::rv_policy::reference_internal, "Retrieves the current obstacle borders")
        .def("set_borders", &Avoidance::set_borders, "Updates the obstacle borders with a new polygon", "new_borders"_a)
        .def("add_dynamic_obstacle", &Avoidance::add_dynamic_obstacle, "Adds a dynamic obstacle to the list of obstacles", "obstacle"_a)
        .def("clear_dynamic_obstacles", &Avoidance::clear_dynamic_obstacles, "Clears all dynamic obstacles")
    ;

}

} // namespace obstacles

} // namespace cogip
