#pragma once

#include "YDLidarDriver.h"

#include "shared_memory/WritePriorityLock.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>

#include <map>
#include <string>
#include <thread>

namespace nb = nanobind;

/**
 * YDLidar G2 properties:
 * - Baudrate: 230400
 * - SampleRate: 5KHz
 * - Range: 0.28~16m
 * - Frequency: 5~12Hz
 * - Intensity: 10bit
 * - SingleChannel: no
 * - Voltage: 4.8~5.2V"
 */

namespace ydlidar {

constexpr std::size_t MAX_DATA_COUNT = 1024;

#pragma pack(1)

/**
 * @brief The Laser Point struct
 */
typedef struct {
/// lidar angle. unit(degree)
float angle;
/// lidar range. unit(mm)
float range;
/// lidar intensity
float intensity;
} laser_point_t;

#pragma pack()

/**
 * @brief The Laser Scan Data struct
 */
typedef struct {
    /// Array of lidar points
    std::vector<laser_point_t> points;
} laser_scan_t;

class YDLidar {
public:
    /// Constructor with optional external memory pointer
    explicit YDLidar(float (*external_lidar_data)[3] = nullptr);

    /// Constructor accepting a nanobind::ndarray
    explicit YDLidar(nb::ndarray<float, nb::numpy, nb::shape<MAX_DATA_COUNT, 3>> external_lidar_data);

    /// Destructor
    ~YDLidar();

    /// Opens the communication port and asserts the initialization parameters.
    /// @param serial_port_name The serial device system path (e.g., "/dev/ttyUSB0").
    /// @return `true` if the connection is successfully established, `false` otherwise.
    bool connect(const std::string& serial_port_name);

    /**
     * @brief Start the device scanning routine which runs on a separate thread and enable motor.
     * @return true if successfully started, otherwise false.
     */
    bool start();

    /**
     * @brief Get the LiDAR Scan Data. start is successful before doProcessSimple scan data.
     * @param[out] outscan             LiDAR Scan Data
     * @param[out] hardwareError       hardware error status
     * @return true if successfully started, otherwise false.
     */
    bool doProcessSimple(laser_scan_t& outscan);

    /**
     * @brief Stop the device scanning thread and disable motor.
     * @return true if successfully Stoped, otherwise false.
     */
    bool stop();

    /**
     * @brief Disconnect the LiDAR.
     */
    void disconnect();

    /// Set the minimum intensity value to validate data.
    void setMinIntensity(uint8_t min_intensity) { min_intensity_ = min_intensity; }

    /// Set the minimum distance to validate data.
    void setMinDistance(uint16_t min_distance) { min_distance_ = min_distance; }

    /// Set the maximum distance to validate data.
    void setMaxDistance(uint16_t max_distance) { max_distance_ = max_distance; }

    /// Set the data write lock.
    void setDataWriteLock(cogip::shared_memory::WritePriorityLock& lock) {
        data_write_lock_ = &lock;
    };

    /// Set invalid angle range
    void setInvalidAngleRange(uint16_t min_angle, uint16_t max_angle) {
        min_invalid_angle_ = min_angle;
        max_invalid_angle_ = max_angle;
    };

    /// Set scan frequency (in kHz)
    void setScanFrequency(float frequency) {
        scan_frequency_ = frequency;
        refresh_interval_ = int64_t(std::ceil(1000.0 / scan_frequency_));
    };

private:
    /**
     * @brief check LiDAR health state and device information
     * @return true if health status and device information has been obtained with the device.
     * If it's not, false on error
     */
    bool  checkStatus();

    /**
     * @brief check LiDAR scan state
     * @return true if the normal scan runs with the device.
     * If it's not, false on error.
     */
    bool checkHardware();

    /**
     * @brief Get LiDAR Health state
     * @return true if the device is in good health, If it's not
     */
    bool getDeviceHealth();

    /**
     * @brief Get LiDAR Device information
     * @return true if the device information is correct, If it's not
     */
    bool getDeviceInfo();

    /**
     * @brief check LiDAR Scan frequency
     * @return true if successfully checked, otherwise false.
     */
    bool checkScanFrequency();

    /**
     * @brief Calculate real-time sampling frequency
     * @param frequency       LiDAR current Scan Frequency
     * @param count           LiDAR Points
     * @param tim_scan_end    Last Scan Point Time Stamp
     * @param tim_scan_start  First Scan Point Time Stamp
     */
    void resample(int frequency, int count, uint64_t tim_scan_end,
        uint64_t tim_scan_start);

    void updateSharedMemory();

    bool external_data_;      ///< Flag to indicate if memory is externally managed
    float (*lidar_data_)[3];  ///< Pointer to lidar data memory
    cogip::shared_memory::WritePriorityLock* data_write_lock_;
    std::atomic<bool> update_shm_thread_exit_flag_;
    std::thread* update_shm_thread_;
    uint8_t min_intensity_;              ///< LiDAR minimum intensity
    uint16_t min_invalid_angle_;         ///< LiDAR minimum angle
    uint16_t max_invalid_angle_;         ///< LiDAR maximum angle
    uint16_t max_distance_;              ///< LiDAR maximum range
    uint16_t min_distance_;              ///< LiDAR minimum range
    float scan_frequency_;               ///< LiDAR scanning frequency
    int64_t refresh_interval_;           ///< LiDAR shared data refresh interval
    int sample_rate_;                    ///< LiDAR sample rate
    bool    is_scanning_;                ///< LiDAR is Scanning
    float   frequency_offset_;           ///< Fixed Scan Frequency Offset
    ydlidar::YDlidarDriver* lidar_ptr_;  ///< LiDAR Driver Interface pointer
    uint64_t point_time_;                ///< Time interval between two sampling point
    uint64_t last_node_time_;            ///< Latest LiDAR Start Node Time
    node_info_t* global_nodes_;          ///< global nodes buffer
    double last_frequency_;              ///< Latest Scan Frequency
    uint64_t first_node_time_;           ///< Calculate real-time sample rate start time
    uint64_t all_node_;                  ///< Sum of sampling points

    void commonInit();
};

} // namespace ydlidar



