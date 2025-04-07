#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/bind_vector.h>

#include <libserial/SerialPortConstants.h>

#include "lidar_ld19/ldlidar_driver.h"

namespace nb = nanobind;
using namespace nb::literals;

namespace ldlidar {

NB_MODULE(lidar_ld19, m) {
    auto models_module = nb::module_::import_("cogip.cpp.libraries.models");
    auto shared_memory_module = nb::module_::import_("cogip.cpp.libraries.shared_memory");

    nb::enum_<LibSerial::BaudRate>(m, "BaudRate")
        .value("BAUD_230400", LibSerial::BaudRate::BAUD_230400);

    nb::enum_<LidarStatus>(m, "LidarStatus")
        .value("NORMAL", LidarStatus::NORMAL)
        .value("ERROR", LidarStatus::ERROR)
        .value("DATA_TIME_OUT", LidarStatus::DATA_TIME_OUT)
        .value("DATA_WAIT", LidarStatus::DATA_WAIT)
        .value("STOP", LidarStatus::STOP);

    nb::class_<LDLidarDriver>(m, "LDLidarDriver")
        .def(nb::init<>(), "Constructor that internally manages memory")
        .def(nb::init<nb::ndarray<float, nb::numpy, nb::shape<MAX_DATA_COUNT, 3>>>(),
             "Constructor accepting nanobind::ndarray",
             "external_lidar_data"_a
        )
        .def("connect", &LDLidarDriver::connect)
        .def("disconnect", &LDLidarDriver::disconnect)
        .def("wait_lidar_comm", &LDLidarDriver::waitLidarComm)
        .def("start", &LDLidarDriver::start)
        .def("stop", &LDLidarDriver::stop)
        .def("ok", &LDLidarDriver::ok)
        .def(
            "get_lidar_scan_freq",
            [](LDLidarDriver& self) {
                double result = 0.0;
                bool success = self.getLidarScanFreq(result);
                return std::make_pair(success, result);
            }
        )
        .def(
            "get_lidar_data",
            [](const LDLidarDriver &self) -> nb::ndarray<float, nb::numpy, nb::shape<MAX_DATA_COUNT, 3>> {
                const auto &points = self.getLidarData();
                return nb::ndarray<float, nb::numpy, nb::shape<MAX_DATA_COUNT, 3>>((void *)points);
            },
            nb::rv_policy::reference_internal
        )
        .def("set_data_write_lock", &LDLidarDriver::setDataWriteLock, "Set the data write lock", "lock"_a)
        .def("set_min_intensity", &LDLidarDriver::setMinIntensity, "Set the minimum intensity value to validate data", "min_intensity"_a)
        .def("set_min_distance", &LDLidarDriver::setMinDistance, "Set the minimum distance to validate data", "min_distance"_a)
        .def("set_max_distance", &LDLidarDriver::setMaxDistance, "Set the maximum distance to validate data", "max_distance"_a)
        .def("set_invalid_angle_range", &LDLidarDriver::setInvalidAngleRange, "Set the invalid angle range", "min_angle"_a, "max_angle"_a)
    ;
}

} // namespace ldlidar
