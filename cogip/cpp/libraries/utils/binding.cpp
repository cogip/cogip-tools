// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "utils/LidarDataConverter.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>

namespace nb = nanobind;
using namespace nb::literals;

namespace cogip {

namespace utils {

NB_MODULE(utils, m) {
    auto shm_module = nb::module_::import_("cogip.cpp.libraries.shared_memory");

    nb::class_<LidarDataConverter>(m, "LidarDataConverter")
         .def(nb::init<const std::string &>(), "Constructor for LidarDataConverter", "name"_a)
         .def("start", &LidarDataConverter::start, "Start the LidarDataConverter thread")
         .def("stop", &LidarDataConverter::stop, "Stop the LidarDataConverter thread")
         .def("convert", &LidarDataConverter::convert, "Convert lidar data to table coordinates")
         .def("set_pose_current_index", &LidarDataConverter::setPoseCurrentIndex, "Set the current pose index", "index"_a)
         .def("set_table_limits_margin", &LidarDataConverter::setTableLimitsMargin, "Set the table limits margin", "table_limits_margin"_a)
         .def("set_lidar_offset_x", &LidarDataConverter::setLidarOffsetX, "Set the lidar offset on the X axis", "lidar_offset_x"_a)
         .def("set_lidar_offset_y", &LidarDataConverter::setLidarOffsetY, "Set the lidar offset on the Y axis", "lidar_offset_y"_a)
         .def("set_debug", &LidarDataConverter::setDebug, "Set the debug mode", "debug"_a)
    ;
}

} // namespace utils

} // namespace cogip
