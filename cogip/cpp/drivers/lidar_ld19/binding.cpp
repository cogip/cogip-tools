#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/bind_vector.h>

#include <libserial/SerialPortConstants.h>

#include "lidar_ld19/ldlidar_driver.h"

namespace nb = nanobind;

namespace ldlidar {

NB_MODULE(lidar_ld19, m) {
    nb::enum_<LibSerial::BaudRate>(m, "BaudRate")
        .value("BAUD_230400", LibSerial::BaudRate::BAUD_230400);

    nb::enum_<LidarStatus>(m, "LidarStatus")
        .value("NORMAL", LidarStatus::NORMAL)
        .value("ERROR", LidarStatus::ERROR)
        .value("DATA_TIME_OUT", LidarStatus::DATA_TIME_OUT)
        .value("DATA_WAIT", LidarStatus::DATA_WAIT)
        .value("STOP", LidarStatus::STOP);

    nb::class_<LDLidarDriver>(m, "LDLidarDriver")
        .def(nb::init<>())
        .def("connect", &LDLidarDriver::connect)
        .def("disconnect", &LDLidarDriver::disconnect)
        .def("waitLidarComm", &LDLidarDriver::waitLidarComm)
        .def("start", &LDLidarDriver::start)
        .def("stop", &LDLidarDriver::stop)
        .def("ok", &LDLidarDriver::ok)
        .def(
            "getLidarScanFreq",
            [](LDLidarDriver& self) {
                double result = 0.0;
                bool success = self.getLidarScanFreq(result);
                return std::make_pair(success, result);
            }
        )
        .def(
            "getLidarPoints", [](const LDLidarDriver &self) -> nb::ndarray<uint16_t, nb::numpy, nb::shape<NUM_ANGLES, 2>> {
                const auto &points = self.getLidarPoints();
                return nb::ndarray<uint16_t, nb::numpy, nb::shape<NUM_ANGLES, 2>>((void *)points);
            },
            nb::rv_policy::reference_internal
        );

    nb::class_<PointData>(m, "PointData")
        .def(nb::init<>())
        .def(nb::init<float, uint16_t, uint8_t, uint64_t>(),
             nb::arg("angle"), nb::arg("distance"), nb::arg("intensity"),
             nb::arg("stamp") = 0)
        .def_rw("angle", &PointData::angle)
        .def_rw("distance", &PointData::distance)
        .def_rw("intensity", &PointData::intensity)
        .def_rw("stamp", &PointData::stamp)
        .def("__repr__", [](const PointData &p) {
            return "<PointData(angle=" + std::to_string(p.angle) +
                   ", distance=" + std::to_string(p.distance) +
                   ", intensity=" + std::to_string(p.intensity) +
                   ", stamp=" + std::to_string(p.stamp) +
                   ")>";
        });

    nb::bind_vector<Points2D>(m, "Points2D");
}

} // namespace ldlidar
