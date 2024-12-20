#include "nanobind_example/nanobind_example.hpp"

#include <cstdlib>

namespace nanobind_example {

NanobindExample::NanobindExample() {
    for (size_t i = 0; i < NUM_DATA; i++) {
        data_[i][0] = std::rand();
        data_[i][1] = std::rand();
    }
}

std::string NanobindExample::getMessage() const {
    return "Hello from COGIP C++ Nanobind Example class";
}

} // nanobind namespace
