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
        .value("LidarCoords", LockName::LidarCoords)
        .value("DetectorObstacles", LockName::DetectorObstacles)
        .value("MonitorObstacles", LockName::MonitorObstacles)
        .value("Obstacles", LockName::Obstacles)
        .value("AvoidanceBlocked", LockName::AvoidanceBlocked)
        .value("AvoidancePath", LockName::AvoidancePath)
        .value("SimCameraData", LockName::SimCameraData)
    ;

    nb::class_<WritePriorityLock>(m, "WritePriorityLock")
        .def(nb::init<const std::string&, bool>(), "name"_a, "owner"_a = false,
             "Initialize a WritePriorityLock with a unique semaphore name and ownership flag.")
        .def("start_reading", &WritePriorityLock::startReading, nb::call_guard<nb::gil_scoped_release>(),
             "Acquire a read lock, allowing multiple readers.")
        .def("finish_reading", &WritePriorityLock::finishReading,
             "Release the read lock.")
        .def("start_writing", &WritePriorityLock::startWriting, nb::call_guard<nb::gil_scoped_release>(),
             "Acquire a write lock, blocking all readers and writers.")
        .def("finish_writing", &WritePriorityLock::finishWriting,
             "Release the write lock.")
        .def("register_consumer", &WritePriorityLock::registerConsumer,
             "Register the the lock will be used to wait the update signal to read updated data.")
        .def("post_update", &WritePriorityLock::postUpdate,
             "Signal to registered consumers that data was updated.")
        .def("wait_update", &WritePriorityLock::waitUpdate, "timeout_seconds"_a = -1.0, nb::call_guard<nb::gil_scoped_release>(),
             "Wait for the updated signal meaning that data was updated.")
        .def("reset", &WritePriorityLock::reset,
             "Reset counters and semaphores.")
        .def("set_debug", &WritePriorityLock::setDebug, "debug"_a,
             "Set/unset debug mode.")
     ;

     nb::class_<shared_properties_t>(m, "SharedProperties")
        .def(nb::init<>(), "Default constructor")
        .def_rw("robot_id", &shared_properties_t::robot_id, "Robot ID")
        .def_rw("robot_width", &shared_properties_t::robot_width, "Robot width in mm")
        .def_rw("robot_length", &shared_properties_t::robot_length, "Robot length in mm")
        .def_rw("obstacle_radius", &shared_properties_t::obstacle_radius, "Obstacle radius in mm")
        .def_rw("obstacle_bb_margin", &shared_properties_t::obstacle_bb_margin, "Obstacle bounding box margin in mm")
        .def_rw("obstacle_bb_vertices", &shared_properties_t::obstacle_bb_vertices, "Number of vertices for the obstacle bounding box")
        .def_rw("obstacle_updater_interval", &shared_properties_t::obstacle_updater_interval, "Obstacle updater interval in seconds")
        .def_rw("path_refresh_interval", &shared_properties_t::path_refresh_interval, "Path refresh interval in seconds")
        .def_rw("bypass_detector", &shared_properties_t::bypass_detector, "Bypass detector flag")
        .def_rw("disable_fixed_obstacles", &shared_properties_t::disable_fixed_obstacles, "Disable fixed obstacles flag")
        .def_rw("table", &shared_properties_t::table, "Table ID")
        .def_rw("strategy", &shared_properties_t::strategy, "Strategy ID")
        .def_rw("start_position", &shared_properties_t::start_position, "Start position ID")
        .def_rw("avoidance_strategy", &shared_properties_t::avoidance_strategy, "Avoidance strategy ID")
        .def_rw("goap_depth", &shared_properties_t::goap_depth, "Depth of the GOAP search tree, 0 to disable GOAP")
        .def("__repr__", [](const shared_properties_t& properties) {
           std::ostringstream oss;
           oss << properties;
           return oss.str();
        })
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
        .def(
            "get_table_limits",
            [](SharedMemory &self) -> nb::ndarray<double, nb::numpy, nb::shape<4>> {
                return nb::ndarray<double, nb::numpy, nb::shape<4>>((void *)self.getTableLimits());
            },
            nb::rv_policy::reference_internal,
            "Get the table_limits structure from shared memory ."
        )
        .def(
          "get_lidar_data",
          [](SharedMemory &self) -> nb::ndarray<double, nb::numpy, nb::shape<MAX_LIDAR_DATA_COUNT, 3>> {
              auto &data = self.getLidarData();
              return nb::ndarray<double, nb::numpy, nb::shape<MAX_LIDAR_DATA_COUNT, 3>>((void *)data);
          },
          nb::rv_policy::reference_internal,
          "Get the lidar_data structure from shared memory ."
        )
       .def(
          "get_lidar_coords",
          [](SharedMemory &self) -> nb::ndarray<double, nb::numpy, nb::shape<MAX_LIDAR_DATA_COUNT, 2>> {
                auto &data = self.getLidarCoords();
                return nb::ndarray<double, nb::numpy, nb::shape<MAX_LIDAR_DATA_COUNT, 2>>((void *)data);
          },
          nb::rv_policy::reference_internal,
          "Get the lidar_coords structure from shared memory ."
        )
        .def("get_detector_obstacles", &SharedMemory::getDetectorObstacles, nb::rv_policy::reference_internal,
             "Get CircleList object wrapping the shared memory detector_obstacles structure.")
        .def("get_monitor_obstacles", &SharedMemory::getMonitorObstacles, nb::rv_policy::reference_internal,
             "Get CircleList object wrapping the shared memory monitor_obstacles structure.")
        .def("get_circle_obstacles", &SharedMemory::getCircleObstacles, nb::rv_policy::reference_internal,
             "Get ObstacleCircleList object wrapping the shared memory circle_obstacles structure.")
        .def("get_rectangle_obstacles", &SharedMemory::getRectangleObstacles, nb::rv_policy::reference_internal,
             "Get ObstacleRectangleList object wrapping the shared memory rectangle_obstacles structure.")
        .def("get_properties", &SharedMemory::getProperties, nb::rv_policy::reference_internal,
             "Get the shared properties.")
        .def_prop_rw("avoidance_exiting", &SharedMemory::getAvoidanceExiting, &SharedMemory::setAvoidanceExiting,
             "Get or set the avoidance exiting flag.")
        .def_prop_rw("avoidance_has_new_pose_order", &SharedMemory::getAvoidanceHasNewPoseOrder, &SharedMemory::setAvoidanceHasNewPoseOrder,
             "Get or set the avoidance new pose order available flag.")
        .def_prop_rw("avoidance_has_pose_order", &SharedMemory::getAvoidanceHasPoseOrder, &SharedMemory::setAvoidanceHasPoseOrder,
             "Get or set the avoidance no pose order flag.")
        .def("get_avoidance_pose_order", &SharedMemory::getAvoidancePoseOrder, nb::rv_policy::reference_internal,
             "Get PoseOrder object wrapping the shared memory avoidance_pose_order structure.")
        .def("get_avoidance_new_pose_order", &SharedMemory::getAvoidanceNewPoseOrder, nb::rv_policy::reference_internal,
             "Get PoseOrder object wrapping the shared memory avoidance_pose_order structure.")
        .def("get_avoidance_path", &SharedMemory::getAvoidancePath, nb::rv_policy::reference_internal,
             "Get PoseOrderList object wrapping the shared memory avoidance_path structure.")
        .def("get_sim_camera_data",
             [](SharedMemory &self) -> nb::ndarray<uint8_t, nb::numpy, nb::shape<SIM_CAMERA_HEIGHT, SIM_CAMERA_WIDTH, 4>> {
                 auto &data = self.getSimCameraData();
                 return nb::ndarray<uint8_t, nb::numpy, nb::shape<SIM_CAMERA_HEIGHT, SIM_CAMERA_WIDTH, 4>>((void *)data);
             },
             nb::rv_policy::reference_internal,
             "Get the simulated camera data in RGBA format from shared memory ."
        )
    ;

}

} // namespace shared_memory

} // namespace cogip
