#include "logger_example/logger_example.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>

namespace nb = nanobind;

namespace logger_example {

NB_MODULE(logger_example, m) {
    m.def("emit_logs", &emit_logs, "Emit logs to Python logger");
}

} // namespace logger_example
