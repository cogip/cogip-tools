#include "path/Pose.hpp"

#include <algorithm>

namespace cogip {

namespace path {

Pose::Pose(
    double x, double y, double O,
    double max_speed_ratio_linear, double max_speed_ratio_angular,
    bool allow_reverse, bool bypass_anti_blocking, uint32_t timeout_ms,
    bool bypass_final_orientation
    ) : cogip_defs::Pose(x, y, O), allow_reverse_(allow_reverse),
    bypass_anti_blocking_(bypass_anti_blocking), timeout_ms_(timeout_ms),
    bypass_final_orientation_(bypass_final_orientation)
{
    // Ratios are betwen 0 and 1
    max_speed_ratio_linear_ =  std::min(max_speed_ratio_linear, 1.);
    max_speed_ratio_angular_ = std::min(max_speed_ratio_angular, 1.);
}

} // namespace path

} // namespace cogip
