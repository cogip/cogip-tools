// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "obstacles_new_example/obstacles_new_example.hpp"

#include <nanobind/nanobind.h>

namespace nb = nanobind;

namespace obstacles_new_example {

NB_MODULE(obstacles_new_example, m) {
    m.def("run", &run, "Demonstrate the obstacles_new library");
}

} // namespace obstacles_new_example
