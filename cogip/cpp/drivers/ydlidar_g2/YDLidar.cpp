#include "ydlidar_g2/timer.h"
#include "ydlidar_g2/YDLidar.h"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <functional>
#include <iostream>
#include <map>
#include <numeric>

using namespace std;

namespace ydlidar {

YDLidar::YDLidar(float (*external_lidar_data)[3]) :
    lidar_data_(external_lidar_data),
    external_data_(external_lidar_data != nullptr) {
    if (!external_data_) {
        // Allocate memory if external pointer is not provided
        lidar_data_ = new float[MAX_DATA_COUNT][3]();
    }

    commonInit();
}

YDLidar::YDLidar(nb::ndarray<float, nb::numpy, nb::shape<MAX_DATA_COUNT, 3>> external_lidar_raw_points) :
    lidar_data_(reinterpret_cast<float(*)[3]>(external_lidar_raw_points.data())),
    external_data_(true) {
    if (!lidar_data_) {
        throw std::runtime_error("Failed to initialize from external NumPy array.");
    }

    commonInit();
}

void YDLidar::commonInit() {
    lidar_ptr_ = nullptr;
    data_write_lock_ = nullptr;
    min_intensity_ = 0;
    min_distance_ = 0;
    max_distance_ = std::numeric_limits<uint16_t>::max();
    min_invalid_angle_ = 0;
    max_invalid_angle_ = 0;
    sample_rate_ = 5;
    scan_frequency_ = 12;
    refresh_interval_ = int64_t(std::ceil(1000.0 / scan_frequency_));
    is_scanning_ = false;
    frequency_offset_ = 0.4f;
    point_time_ = static_cast<int>(1e9 / 5000);
    global_nodes_ = new node_info_t[MAX_SCAN_NODES];
    first_node_time_ = getCurrentTime();
    last_node_time_ = getCurrentTime();
    last_frequency_ = 0;
    all_node_ = 0;
};

YDLidar::~YDLidar() {
    disconnect();

    if (global_nodes_) {
        delete[] global_nodes_;
        global_nodes_ = NULL;
    }

    if (!external_data_) {
        // Deallocate memory only if it was internally allocated
        delete[] lidar_data_;
    }
    lidar_data_ = nullptr;
    data_write_lock_ = nullptr;
}

bool YDLidar::connect(const std::string& serial_port_name) {
    if (!lidar_ptr_) {
        std::cout << "[YDLidar] Initializing" << std::endl;

        // Create the driver instance
        lidar_ptr_ = new ydlidar::YDlidarDriver();

        if (!lidar_ptr_) {
            std::cerr << "[YDLidar] Error: create driver failed" << std::endl;
            return false;
        }

        std::cout << "[YDLidar] Initialization succeeded" << std::endl;
    }

    result_t op_result = lidar_ptr_->connect(serial_port_name.c_str());

    if (!lidar_ptr_->isConnected()) {
        std::cout << "[YDLidar] Error: Lidar is not connected" << std::endl;
        return false;
    }

    if (!IS_OK(op_result)) {
        std::cerr << "[YDLidar] Error: cannot bind to the specified serial port [" << serial_port_name << "]" << std::endl;
        return false;
    }

    std::cout << "[YDLidar] Lidar successfully connected" << std::endl;

    if (!checkStatus()) {
        std::cerr << "[YDLidar] Error initializing YDLIDAR check status under [" << serial_port_name << "]." << std::endl;
        return false;
    }

    update_shm_thread_exit_flag_ = false;
    update_shm_thread_ = new std::thread(&YDLidar::updateSharedMemory, this);

    std::cout << "[YDLidar] Init success" << std::endl;

    return true;
}

bool YDLidar::start() {
    if (is_scanning_ && lidar_ptr_->isScanning()) {
        return true;
    }

    result_t op_result = lidar_ptr_->startScan();

    if (!IS_OK(op_result)) {
        op_result = lidar_ptr_->startScan();

        if (!IS_OK(op_result)) {
            lidar_ptr_->stop();
            std::cerr << "[YDLidar] Failed to start scan mode: " << op_result << std::endl;
            is_scanning_ = false;
            return false;
        }
    }

    std::cout << "[YDLidar] Succeeded to start scan mode" << std::endl;
    std::cout << "[YDLidar] Current Sampling Rate: " << sample_rate_ << "K" << std::endl;

    last_frequency_ = 0;
    first_node_time_ = getCurrentTime();
    all_node_ = 0;
    point_time_ = lidar_ptr_->getPointTime();
    is_scanning_ = true;
    std::cout << "[YDLidar] Lidar is scanning" << std::endl;
    return true;
}

bool YDLidar::doProcessSimple(laser_scan_t& outscan) {
    if (!checkHardware()) {
        delay(200 / scan_frequency_);
        all_node_ = 0;
        first_node_time_ = getCurrentTime();
        return false;
    }

    size_t count = MAX_SCAN_NODES;

    // Wait scan data:
    uint64_t tim_scan_start = getCurrentTime();
    uint64_t startTs = tim_scan_start;
    result_t op_result = lidar_ptr_->grabScanData(global_nodes_, count);
    uint64_t tim_scan_end = getCurrentTime();
    uint64_t endTs = tim_scan_end;
    uint64_t sys_scan_time = tim_scan_end - tim_scan_start;
    outscan.points.clear();

    // Fill in scan data:
    if (IS_OK(op_result)) {
        int offsetSize = 0;

        uint64_t scan_time = point_time_ * (count - 1 + offsetSize);
        int timeDiff = static_cast<int>(sys_scan_time - scan_time);

        bool HighPayLoad = false;

        if (global_nodes_[0].stamp > 0 &&
            global_nodes_[0].stamp < tim_scan_start) {
            tim_scan_end = global_nodes_[0].stamp;
            HighPayLoad = true;
        }

        tim_scan_end -= point_time_;
        tim_scan_end -= global_nodes_[0].delay_time;
        tim_scan_start = tim_scan_end - scan_time;

        if (!HighPayLoad && tim_scan_start < startTs) {
            tim_scan_start = startTs;
            tim_scan_end = tim_scan_start + scan_time;
        }

        if ((last_node_time_ + point_time_) >= tim_scan_start &&
            (last_node_time_ + point_time_) < endTs - scan_time) {
            tim_scan_start = last_node_time_ + point_time_;
            tim_scan_end = tim_scan_start + scan_time;
        }

        if (all_node_ == 0 && abs(timeDiff) < 10 * 1e6) {
            first_node_time_ = tim_scan_start;
            all_node_ += (count + offsetSize);
        }
        else if (all_node_ != 0) {
            all_node_ += (count + offsetSize);
        }

        last_node_time_ = tim_scan_end;

        int all_node_count = count;

        float scanfrequency = 0.0;

        float range = 0.0;
        float intensity = 0.0;
        float angle = 0.0;

        for (int i = 0; i < count; i++) {
            const node_info_t& node = global_nodes_[i];

            // Get angle
            angle = static_cast<float>(
                (global_nodes_[i].angle_q6_checkbit >> LIDAR_RESP_MEASUREMENT_ANGLE_SHIFT) / 64.0f
                );

            // Counter clockwise
            angle = 360 - angle;

            // Get range
            range = static_cast<float>(global_nodes_[i].distance_q2 / 4.f);

            // Get intensity
            intensity = static_cast<float>(global_nodes_[i].sync_quality);
            // Original range is on 10 bits, so from 0 to 1023.
            // Convert it in the range from 0 to 255.
            intensity = intensity / 4.0;

            if (
                (angle <= min_invalid_angle_ || angle >= max_invalid_angle_) &&
                (range >= min_distance_ && range <= max_distance_) &&
                (intensity >= min_intensity_)
                ) {
                laser_point_t point;
                point.angle = angle;
                point.range = range;
                point.intensity = intensity;

                outscan.points.push_back(point);
            }

            if (global_nodes_[i].scan_frequency != 0) {
                scanfrequency = global_nodes_[i].scan_frequency / 10.0;
            }

        }

        // resample sample rate
        resample(scanfrequency, count, tim_scan_end, tim_scan_start);
        return true;
    }
    else {
        if (lidar_ptr_->getDriverError() != NoError) {
            std::cerr << "[YDLidar] Error: " << lidar_ptr_->getDriverErrorText() << std::endl;
        }

        all_node_ = 0;
        first_node_time_ = tim_scan_start;
    }

    return false;
}

void YDLidar::updateSharedMemory() {
    laser_scan_t scan;

    while (!update_shm_thread_exit_flag_.load()) {
        auto loop_start_time = std::chrono::steady_clock::now();

        doProcessSimple(scan);
        if (data_write_lock_ != nullptr) {
            data_write_lock_->startWriting();
        }
        size_t index = 0;
        for (auto point : scan.points) {
            lidar_data_[index][0] = point.angle;
            lidar_data_[index][1] = point.range;
            lidar_data_[index][2] = point.intensity;
            index++;
        }
        lidar_data_[index][0] = -1;
        lidar_data_[index][1] = -1;
        lidar_data_[index][2] = -1;
        if (data_write_lock_ != nullptr) {
            data_write_lock_->finishWriting();
            data_write_lock_->postUpdate();
        }
        auto loop_end_time = std::chrono::steady_clock::now();
        auto elapsed_time = std::chrono::duration_cast<std::chrono::milliseconds>(loop_end_time - loop_start_time);
        if (elapsed_time < std::chrono::milliseconds(refresh_interval_)) {
            std::this_thread::sleep_for(std::chrono::milliseconds(refresh_interval_) - elapsed_time);
        }
        else {
            std::cout << "[YDLidar] SHM update took too long: " << elapsed_time.count() << "ms (interval=" << refresh_interval_ << ")" << std::endl;
        }
    }
}

bool YDLidar::stop() {
    if (lidar_ptr_) {
        lidar_ptr_->stop();
    }

    if (is_scanning_) {
        std::cout << "[YDLidar] Scanning has stopped" << std::endl;
    }

    is_scanning_ = false;
    return true;
}

void YDLidar::disconnect() {
    update_shm_thread_exit_flag_ = true;

    if ((update_shm_thread_ != nullptr) && update_shm_thread_->joinable()) {
        update_shm_thread_->join();
        delete update_shm_thread_;
        update_shm_thread_ = nullptr;
    }

    if (lidar_ptr_) {
        lidar_ptr_->disconnect();
        delete lidar_ptr_;
        lidar_ptr_ = nullptr;
    }

    is_scanning_ = false;
}

void YDLidar::resample(int frequency, int count, uint64_t tim_scan_end,
    uint64_t tim_scan_start) {
    if (frequency > 3 && frequency <= 15.7 &&
        (frequency - last_frequency_) < 0.05) {
        int sample = static_cast<int>((frequency * count + 500) / 1000);

        if (sample != sample_rate_) {
        }
    }

    last_frequency_ = frequency;
    int realSampleRate = 0;

    if (all_node_ != 0) {
        realSampleRate = 1e9 * all_node_ / (tim_scan_end - first_node_time_);
        int RateDiff = std::abs(static_cast<int>(realSampleRate - sample_rate_ * 1000));

        if (RateDiff > 1000 ||
            (static_cast<int64_t>(tim_scan_end - first_node_time_) > 10 * 1e9 &&
                RateDiff > 30)) {
            all_node_ = 0;
            first_node_time_ = tim_scan_start;
        }
    }
}


bool YDLidar::getDeviceHealth() {
    if (!lidar_ptr_) {
        return false;
    }

    lidar_ptr_->stop();

    result_t op_result;
    device_health_t health_info;
    memset(&health_info, 0, sizeof(device_health_t));
    op_result = lidar_ptr_->getHealth(health_info,
        DEFAULT_TIMEOUT / 2);

    if (IS_OK(op_result)) {
        std::cout << "[YDLidar] Lidar running correctly. The health status: "
                  << ((int)health_info.status == 0 ? "good" : "bad") << std::endl;

        if (health_info.status == 2) {
            std::cerr << "[YDLidar] Error: internal error detected. Please reboot the device to retry." << std::endl;
            return false;
        }
        else {
            return true;
        }
    }
    else {
        std::cerr << "[YDLidar] Error: cannot retrieve YDLidar health code: " << op_result << std::endl;
        return false;
    }
}

/**
 * @brief print LiDAR version information
 * @param info      LiDAR Device information
 * @param port      LiDAR serial port or IP Address
 * @param baudrate  LiDAR serial baudrate or network port
 * @return true if Device information is valid, otherwise false
 */
inline bool printVersionInfo(const device_info_t& info) {
    if (info.firmware_version == 0 &&
        info.hardware_version == 0) {
        return false;
    }

    uint8_t Major = (uint8_t)(info.firmware_version >> 8);
    uint8_t Minor = (uint8_t)(info.firmware_version & 0xff);
    std::cout << "[YDLidar] Connection established:\n"
              << "  - Firmware version: " << (unsigned int)Major << "." << (unsigned int)Minor << "\n"
              << "  - Hardware version: " << (unsigned int)info.hardware_version << "\n"
              << "  - Model: G2B\n"
              << "  - Serial: ";

    for (int i = 0; i < 16; i++) {
        std::cout << std::hex << (info.serialnum[i] & 0xff) << std::dec;
    }

    std::cout << std::endl;
    return true;
}

bool YDLidar::getDeviceInfo() {
    if (!lidar_ptr_) {
        return false;
    }

    bool ret = false;
    device_info_t devinfo;
    memset(&devinfo, 0, sizeof(device_info_t));

    result_t op_result = lidar_ptr_->getDeviceInfo(devinfo, DEFAULT_TIMEOUT / 2);
    if (!IS_OK(op_result)) {
        std::cerr << "[YDLidar] Error: fail to get device information" << std::endl;
        return false;
    }

    frequency_offset_ = 0.4;

    std::string serial_number;
    ret = true;

    printVersionInfo(devinfo);

    point_time_ = 1e9 / 5000;
    lidar_ptr_->setPointTime(point_time_);

    checkScanFrequency();

    return ret;
}

/**
 * @brief Whether the scanning frequency is supported
 * @param frequency scanning frequency
 * @return true if supported, otherwise false.
 */
inline bool isSupportedScanFrequency(double frequency) {
    bool ret = false;

    if (5 <= frequency && frequency <= 16) {
        ret = true;
    }

    return ret;
}


bool YDLidar::checkScanFrequency() {
    float frequency = 7.4f;
    scan_frequency_t scan_frequency;
    float hz = 0.f;
    result_t ans = RESULT_FAIL;

    if (isSupportedScanFrequency(scan_frequency_)) {
        scan_frequency_ += frequency_offset_;
        ans = lidar_ptr_->getScanFrequency(scan_frequency);

        if (IS_OK(ans)) {
            frequency = scan_frequency.frequency / 100.f;
            hz = scan_frequency_ - frequency;

            if (hz > 0) {
                while (hz > 0.95) {
                    lidar_ptr_->setScanFrequencyAdd(scan_frequency);
                    hz = hz - 1.0;
                }

                while (hz > 0.09) {
                    lidar_ptr_->setScanFrequencyAddMic(scan_frequency);
                    hz = hz - 0.1;
                }

                frequency = scan_frequency.frequency / 100.0f;
            }
            else {
                while (hz < -0.95) {
                    lidar_ptr_->setScanFrequencyDis(scan_frequency);
                    hz = hz + 1.0;
                }

                while (hz < -0.09) {
                    lidar_ptr_->setScanFrequencyDisMic(scan_frequency);
                    hz = hz + 0.1;
                }

                frequency = scan_frequency.frequency / 100.0f;
            }
        }
    }
    else {
        scan_frequency_ += frequency_offset_;
        std::cerr << "[YDLidar] Error: current scan frequency[" << scan_frequency_ - frequency_offset_ << "] is out of range." << std::endl;
    }

    ans = lidar_ptr_->getScanFrequency(scan_frequency);

    if (IS_OK(ans)) {
        frequency = scan_frequency.frequency / 100.0f;
        scan_frequency_ = frequency;
    }

    scan_frequency_ -= frequency_offset_;
    std::cout << "[YDLidar] Current Scan Frequency: " << scan_frequency_ << "Hz" << std::endl;
    return true;
}

bool YDLidar::checkStatus() {
    getDeviceHealth();
    getDeviceInfo();
    return true;
}

bool YDLidar::checkHardware() {
    if (!lidar_ptr_) {
        return false;
    }

    if (is_scanning_ && lidar_ptr_->isScanning()) {
        return true;
    }

    return false;
}

} // namespace ydlidar