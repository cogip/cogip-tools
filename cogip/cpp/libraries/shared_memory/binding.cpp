// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "shared_memory/SharedMemory.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/map.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/unique_ptr.h>

#include <sstream>

namespace nb = nanobind;
using namespace nb::literals;

namespace cogip {

namespace shared_memory {

NB_MODULE(shared_memory, m) {
    auto models_module = nb::module_::import_("cogip.cpp.libraries.models");
    auto obstacles_module = nb::module_::import_("cogip.cpp.libraries.obstacles");

    nb::class_<shared_data_t>(m, "SharedData")
        .def(nb::init<>())
        .def_rw("pose_current_buffer", &shared_data_t::pose_current_buffer)
        .def_rw("pose_order", &shared_data_t::pose_order)
        .def("__repr__", [](const shared_data_t &s) {
            std::ostringstream oss;
            oss << s;
            return oss.str();
        })
    ;

    nb::enum_<LockName>(m, "LockName")
        .value("PoseCurrent", LockName::PoseCurrent)
        .value("PoseOrder", LockName::PoseOrder)
        .value("LidarData", LockName::LidarData)
        .value("DetectorObstacles", LockName::DetectorObstacles)
        .value("MonitorObstacles", LockName::MonitorObstacles)
        .value("Obstacles", LockName::Obstacles)
    ;

    nb::class_<WritePriorityLock>(m, "WritePriorityLock")
        .def(nb::init<const std::string&, bool>(), "name"_a, "owner"_a = false,
             "Initialize a WritePriorityLock with a unique semaphore name and ownership flag.")
        .def("start_reading", &WritePriorityLock::startReading,
             "Acquire a read lock, allowing multiple readers.")
        .def("finish_reading", &WritePriorityLock::finishReading,
             "Release the read lock.")
        .def("start_writing", &WritePriorityLock::startWriting,
             "Acquire a write lock, blocking all readers and writers.")
        .def("finish_writing", &WritePriorityLock::finishWriting,
             "Release the write lock.")
        .def("register_consumer", &WritePriorityLock::registerConsumer,
             "Register the the lock will be used to wait the update signal to read updated data.")
        .def("post_update", &WritePriorityLock::postUpdate,
             "Signal to registered consumers that data was updated.")
        .def("wait_update", &WritePriorityLock::waitUpdate,
             "Wait for the updated signal meaning that data was updated.")
        .def("reset", &WritePriorityLock::reset,
             "Reset counters and semaphores.")
        .def("set_debug", &WritePriorityLock::setDebug, "debug"_a,
             "Set/unset debug mode.")
     ;

    nb::class_<SharedMemory>(m, "SharedMemory")
        .def(nb::init<const std::string&, bool>(), "name"_a, "owner"_a = false,
             "Initialize a SharedMemory with a unique name and ownership flag.")
        .def("get_lock", &SharedMemory::getLock, "lock"_a, nb::rv_policy::reference_internal,
             "Get a lock for a specific part of the shared memory.")
        .def("get_data", &SharedMemory::getData, nb::rv_policy::reference,
             "Get the shared data.")
        .def("get_pose_current_buffer", &SharedMemory::getPoseCurrentBuffer, nb::rv_policy::reference_internal,
             "Get PoseBuffer object wrapping the shared memory pose_current_buffer structure.")
        .def("get_pose_order", &SharedMemory::getPoseOrder, nb::rv_policy::reference_internal,
             "Get Pose object wrapping the shared memory pose_order structure.")
        .def(
            "get_table_limits",
            [](SharedMemory &self) -> nb::ndarray<float, nb::numpy, nb::shape<4>> {
                return nb::ndarray<float, nb::numpy, nb::shape<4>>((void *)self.getTableLimits());
            },
            nb::rv_policy::reference_internal,
            "Get the table_limits structure from shared memory ."
        )
        .def(
          "get_lidar_data",
          [](SharedMemory &self) -> nb::ndarray<float, nb::numpy, nb::shape<MAX_LIDAR_DATA_COUNT, 3>> {
              auto &data = self.getLidarData();
              return nb::ndarray<float, nb::numpy, nb::shape<MAX_LIDAR_DATA_COUNT, 3>>((void *)data);
          },
          nb::rv_policy::reference_internal,
          "Get the lidar_data structure from shared memory ."
        )
        .def("get_detector_obstacles", &SharedMemory::getDetectorObstacles, nb::rv_policy::reference_internal,
             "Get CircleList object wrapping the shared memory detector_obstacles structure.")
        .def("get_monitor_obstacles", &SharedMemory::getMonitorObstacles, nb::rv_policy::reference_internal,
             "Get CircleList object wrapping the shared memory monitor_obstacles structure.")
        .def("get_circle_obstacles", &SharedMemory::getCircleObstacles, nb::rv_policy::reference_internal,
             "Get ObstacleCircleList object wrapping the shared memory circle_obstacles structure.")
        .def("get_rectangle_obstacles", &SharedMemory::getRectangleObstacles, nb::rv_policy::reference_internal,
             "Get ObstacleRectangleList object wrapping the shared memory rectangle_obstacles structure.")
    ;

}

} // namespace shared_memory

} // namespace cogip
