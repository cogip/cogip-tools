#pragma once

#include <cstdint>
#include <string>

namespace nanobind_example {

constexpr size_t NUM_DATA = 8;

class NanobindExample {
public:
    NanobindExample();
    std::string getMessage() const;
    const uint16_t (&getData() const)[NUM_DATA][2] { return data_; };

private:
    uint16_t data_[NUM_DATA][2];
};

} // nanobind namespace
