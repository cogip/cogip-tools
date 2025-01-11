#pragma once

#include <cstdint>
#include <vector>

#define ANGLE_TO_RADIAN(angle) ((angle) * 3141.59 / 180000)

// Lidar error code definition
#define LIDAR_NO_ERROR 0x00
#define LIDAR_ERROR_BLOCKING 0x01
#define LIDAR_ERROR_OCCLUSION 0x02
#define LIDAR_ERROR_BLOCKING_AND_OCCLUSION 0x03
// End Lidar error code definition

namespace ldlidar {

enum class LidarStatus {
    NORMAL,
    ERROR,
    DATA_TIME_OUT,
    DATA_WAIT,
    STOP,
};

struct PointData {
    /// Polar coordinate representation
    float angle;       ///< Angle ranges from 0 to 359 degrees
    uint16_t distance; ///< Distance is measured in millimeters
    uint8_t intensity; ///< Intensity is between 0 and 255
    uint64_t stamp;    ///< System time when first range was measured in nanoseconds

    // Cartesian coordinate representation
    PointData(float angle, uint16_t distance, uint8_t intensity, uint64_t stamp = 0) {
        this->angle = angle;
        this->distance = distance;
        this->intensity = intensity;
        this->stamp = stamp;
    }
    PointData() {}
};

using Points2D = std::vector<PointData>;

} // namespace ldlidar
