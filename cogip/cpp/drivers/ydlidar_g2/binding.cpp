#include "ydlidar_g2/YDLidar.h"

#include <libserial/SerialPortConstants.h>

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>

namespace nb = nanobind;
using namespace nb::literals;

namespace ydlidar {

NB_MODULE(ydlidar_g2, m) {
    auto shared_memory_module = nb::module_::import_("cogip.cpp.libraries.shared_memory");

    nb::class_<YDLidar>(m, "YDLidar")
        .def(nb::init<>(), "Constructor that internally manages memory")
        .def(nb::init<nb::ndarray<float, nb::numpy, nb::shape<MAX_DATA_COUNT, 3>>>(),
            "Constructor accepting nanobind::ndarray",
            "external_lidar_data"_a
        )
        .def("connect", &YDLidar::connect)
        .def("start", &YDLidar::start)
        .def("stop", &YDLidar::stop)
        .def("disconnect", &YDLidar::disconnect)
        .def("set_data_write_lock", &YDLidar::setDataWriteLock, "Set the data write lock", "lock"_a)
        .def("set_min_intensity", &YDLidar::setMinIntensity, "Set the minimum intensity value to validate data", "min_intensity"_a)
        .def("set_min_distance", &YDLidar::setMinDistance, "Set the minimum distance to validate data", "min_distance"_a)
        .def("set_max_distance", &YDLidar::setMaxDistance, "Set the maximum distance to validate data", "max_distance"_a)
        .def("set_invalid_angle_range", &YDLidar::setInvalidAngleRange, "Set the invalid angle range", "min_angle"_a, "max_angle"_a)
        .def("set_scan_frequency", &YDLidar::setScanFrequency, "Set the scan frequency (in kHz)", "frequency"_a)
    ;
}

} // namespace ydlidar
