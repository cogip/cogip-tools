// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "logger/PythonLogger.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/stl/function.h>
#include <nanobind/stl/string.h>

namespace nb = nanobind;
using namespace nb::literals;

namespace cogip {

namespace logger {

NB_MODULE(logger, m) {
    nb::enum_<LogLevel>(m, "LogLevel")
        .value("DEBUG", LogLevel::DEBUG)
        .value("INFO", LogLevel::INFO)
        .value("WARNING", LogLevel::WARNING)
        .value("ERROR", LogLevel::ERROR);

        m.def("set_logger_callback", &set_logger_callback, "Set the Python logger callback");
        m.def("unset_logger_callback", &unset_logger_callback, "Unset the Python logger callback");
}

} // namespace logger

} // namespace cogip
