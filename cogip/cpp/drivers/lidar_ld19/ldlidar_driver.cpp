#include "lidar_ld19/ldlidar_driver.h"
#include "lidar_ld19/ldlidar_protocol.h"

#include <libserial/SerialPortConstants.h>

#include <unistd.h>
#include <iostream>
#include <algorithm>
#include <map>
#include <numeric>

namespace ldlidar {

constexpr uint16_t max_distance = 3000;
constexpr uint8_t min_intensity = 150;

uint64_t getSystemTimeStamp() {
    std::chrono::time_point<std::chrono::system_clock, std::chrono::nanoseconds> tp =
        std::chrono::time_point_cast<std::chrono::nanoseconds>(std::chrono::system_clock::now());
    auto tmp = std::chrono::duration_cast<std::chrono::nanoseconds>(tp.time_since_epoch());
    return ((uint64_t)tmp.count());
}

bool LDLidarDriver::is_ok_ = false;

LDLidarDriver::LDLidarDriver(uint16_t (*external_lidar_data)[2]):
    lidar_data_(external_lidar_data),
    external_data_(external_lidar_data != nullptr)
{
    if (!external_data_) {
        // Allocate memory if external pointer is not provided
        lidar_data_ = new uint16_t[NUM_ANGLES][2]();
    }

    commonInit();
}

LDLidarDriver::LDLidarDriver(nb::ndarray<uint16_t, nb::numpy, nb::shape<NUM_ANGLES, 2>> external_lidar_points):
    lidar_data_(reinterpret_cast<uint16_t(*)[2]>(external_lidar_points.data())),
    external_data_(true)
{
    if (!lidar_data_) {
        throw std::runtime_error("Failed to initialize from external NumPy array.");
    }

    commonInit();
}

void LDLidarDriver::commonInit() {
    is_start_flag_ = false;
    is_connect_flag_ = false;
    lidar_measure_freq_ = 4500;
    lidar_status_ = LidarStatus::NORMAL;
    lidar_error_code_ = LIDAR_NO_ERROR;
    is_frame_ready_ = false;
    data_write_lock_ = nullptr;
    timestamp_ = 0;
    speed_ = 0;
    is_poweron_comm_normal_ = false;
    last_pkg_timestamp_ = 0;

    last_pubdata_times_ = std::chrono::steady_clock::now();
    comm_serial_ = new LibSerial::SerialPort();
    protocol_handle_ = new LdLidarProtocol();
};

LDLidarDriver::~LDLidarDriver() {
    if (protocol_handle_ != nullptr) {
        delete protocol_handle_;
    }

    if (comm_serial_ != nullptr) {
        delete comm_serial_;
    }

    if (!external_data_) {
        // Deallocate memory only if it was internally allocated
        delete[] lidar_data_;
    }
}

bool LDLidarDriver::connect(const std::string &serial_port_name, LibSerial::BaudRate serial_baudrate) {
    if (is_connect_flag_) {
        return true;
    }

    if (serial_port_name.empty()) {
        std::cerr << "Input <serial_port_name> is empty." << std::endl;
        return false;
    }

    clearStatus();

    comm_serial_->Open(serial_port_name);
    if (!comm_serial_->IsOpen()) {
        std::cerr << "Serial is not opened: " << serial_port_name << std::endl;
        return false;
    }
    comm_serial_->SetBaudRate(serial_baudrate);

    is_connect_flag_ = true;
    rx_thread_exit_flag_ = false;
    rx_thread_ = new std::thread(&LDLidarDriver::rxThreadProc, this);

    setLidarDriverStatus(true);

    return true;
}

bool LDLidarDriver::disconnect() {
    if (!is_connect_flag_) {
        return true;
    }

    rx_thread_exit_flag_ = true;

    setLidarDriverStatus(false);

    is_connect_flag_ = false;
    if ((rx_thread_ != nullptr) && rx_thread_->joinable()) {
        rx_thread_->join();
        delete rx_thread_;
        rx_thread_ = nullptr;
    }

    comm_serial_->Close();

    return true;
}

void LDLidarDriver::rxThreadProc() {
    std::string rx_buf;
    while (!rx_thread_exit_flag_.load()) {
        comm_serial_->Read(rx_buf, MAX_ACK_BUF_LEN);
        commReadCallback(rx_buf.c_str(), MAX_ACK_BUF_LEN);
   }
}

bool LDLidarDriver::waitLidarComm(int64_t timeout) {
    auto last_time = std::chrono::steady_clock::now();

    bool is_recvflag = false;
    do {
        if (getLidarPowerOnCommStatus()) {
            is_recvflag = true;
        }
        usleep(1000);
    } while (!is_recvflag && (std::chrono::duration_cast<std::chrono::milliseconds>(
                                    std::chrono::steady_clock::now() - last_time)
                                    .count() < timeout));

    if (is_recvflag) {
        setLidarDriverStatus(true);
        return true;
    }
    else {
        setLidarDriverStatus(false);
        return false;
    }
}

bool LDLidarDriver::getLidarScanFreq(double &spin_hz) const {
    if (!is_start_flag_) {
        return false;
    }
    spin_hz = getSpeed();
    return true;
}

uint8_t LDLidarDriver::getLidarErrorCode() const {
    if (!is_start_flag_) {
        return LIDAR_NO_ERROR;
    }

    uint8_t errcode = getLidarErrorCode();
    return errcode;
}

bool LDLidarDriver::start() {
    if (is_start_flag_) {
        return true;
    }

    if (!is_connect_flag_) {
        return false;
    }

    is_start_flag_ = true;

    last_pubdata_times_ = std::chrono::steady_clock::now();

    setLidarDriverStatus(true);

    return true;
}

bool LDLidarDriver::stop() {
    if (!is_start_flag_) {
        return true;
    }

    setLidarDriverStatus(false);

    is_start_flag_ = false;

    return true;
}


bool LDLidarDriver::parse(const uint8_t *data, long len) {
    for (int i = 0; i < len; i++) {
        uint8_t ret = protocol_handle_->analyzeDataPacket(data[i]);
        if (ret == GET_PKG_PCD) {
            LiDARMeasureDataType datapkg = protocol_handle_->getPCDPacketData();
            is_poweron_comm_normal_ = true;
            speed_ = datapkg.speed;
            timestamp_ = datapkg.timestamp;
            // parse a package is success
            double diff = (datapkg.end_angle / 100 - datapkg.start_angle / 100 + 360) % 360;
            if (diff <= ((double)datapkg.speed * POINT_PER_PACK / lidar_measure_freq_ * 1.5)) {
                if (0 == last_pkg_timestamp_) {
                    last_pkg_timestamp_ = getSystemTimeStamp();
                }
                else {
                    uint64_t current_pack_stamp = getSystemTimeStamp();
                    int pkg_point_number = POINT_PER_PACK;
                    double pack_stamp_point_step =
                        static_cast<double>(current_pack_stamp - last_pkg_timestamp_) / static_cast<double>(pkg_point_number - 1);
                    uint32_t diff = ((uint32_t)datapkg.end_angle + 36000 - (uint32_t)datapkg.start_angle) % 36000;
                    float step = diff / (POINT_PER_PACK - 1) / 100.0;
                    float start = (double)datapkg.start_angle / 100.0;
                    PointData data;
                    for (int i = 0; i < POINT_PER_PACK; i++) {
                        data.distance = datapkg.point[i].distance;
                        data.angle = start + i * step;
                        if (data.angle >= 360.0) {
                            data.angle -= 360.0;
                        }
                        data.intensity = datapkg.point[i].intensity;
                        data.stamp = static_cast<uint64_t>(last_pkg_timestamp_ + (pack_stamp_point_step * i));
                        tmp_lidar_scan_data_vec_.push_back(PointData(data.angle, data.distance, data.intensity, data.stamp));
                    }
                    last_pkg_timestamp_ = current_pack_stamp; // update last pkg timestamp
                }
            }
        }
    }

    return true;
}

bool LDLidarDriver::assemblePacket() {
    float last_angle = 0;
    Points2D data;
    int count = 0;

    if (speed_ <= 0) {
        tmp_lidar_scan_data_vec_.erase(tmp_lidar_scan_data_vec_.begin(), tmp_lidar_scan_data_vec_.end());
        return false;
    }

    for (auto n : tmp_lidar_scan_data_vec_) {
        // Wait for enough data, need enough data to show a circle enough data has been obtained.
        if ((n.angle < 20.0) && (last_angle > 340.0)) {
            if ((count * getSpeed()) > (lidar_measure_freq_ * 1.4)) {
                if (count >= (int)tmp_lidar_scan_data_vec_.size()) {
                    tmp_lidar_scan_data_vec_.clear();
                }
                else {
                    tmp_lidar_scan_data_vec_.erase(
                        tmp_lidar_scan_data_vec_.begin(),
                        tmp_lidar_scan_data_vec_.begin() + count
                    );
                }
                return false;
            }
            data.insert(data.begin(), tmp_lidar_scan_data_vec_.begin(), tmp_lidar_scan_data_vec_.begin() + count);

            std::sort(data.begin(), data.end(), [](PointData a, PointData b) { return a.stamp < b.stamp; });
            if (data.size() > 0) {
                setLaserScanData(data);
                setFrameReady();

                if (count >= (int)tmp_lidar_scan_data_vec_.size()) {
                    tmp_lidar_scan_data_vec_.clear();
                }
                else {
                    tmp_lidar_scan_data_vec_.erase(tmp_lidar_scan_data_vec_.begin(), tmp_lidar_scan_data_vec_.begin() + count);
                }
                return true;
            }
        }
        count++;

        if ((count * getSpeed()) > (lidar_measure_freq_ * 2)) {
            if (count >= (int)tmp_lidar_scan_data_vec_.size()) {
                tmp_lidar_scan_data_vec_.clear();
            }
            else {
                tmp_lidar_scan_data_vec_.erase(tmp_lidar_scan_data_vec_.begin(), tmp_lidar_scan_data_vec_.begin() + count);
            }
            return false;
        }

        last_angle = n.angle;
    }

    return false;
}

void LDLidarDriver::commReadCallback(const char *byte, size_t len) {
    if (parse((uint8_t *)byte, len)) {
        assemblePacket();
    }
}

bool LDLidarDriver::getLidarPowerOnCommStatus() {
    if (is_poweron_comm_normal_) {
        is_poweron_comm_normal_ = false;
        return true;
    }
    else {
        return false;
    }
}

bool LDLidarDriver::isFrameReady() {
    std::lock_guard<std::mutex> lg(mutex_lock1_);
    return is_frame_ready_;
}

void LDLidarDriver::resetFrameReady() {
    std::lock_guard<std::mutex> lg(mutex_lock1_);
    is_frame_ready_ = false;
}

void LDLidarDriver::setFrameReady() {
    std::lock_guard<std::mutex> lg(mutex_lock1_);
    is_frame_ready_ = true;
}

void LDLidarDriver::setLaserScanData(Points2D &src) {
    std::lock_guard<std::mutex> lg(mutex_lock2_);
    std::array<uint16_t, NUM_ANGLES> result_distances;
    std::array<uint8_t, NUM_ANGLES> result_intensities;
    std::array<std::vector<uint16_t>, NUM_ANGLES> tmp_distances;
    std::array<std::vector<uint8_t>, NUM_ANGLES> tmp_intensities;

    // Build a list of points for each integer degree
    for (const auto &point: src) {
        if (point.intensity < min_intensity) {
            continue;
        }
        size_t angle = (static_cast<size_t>(point.angle) + NUM_ANGLES) % NUM_ANGLES;
        tmp_distances[angle].push_back(point.distance);
        tmp_intensities[angle].push_back(point.intensity);
    }

    // Compute mean of points list for each degree.
    if (data_write_lock_ != nullptr) {
        data_write_lock_->startWriting();
    }

    if (! filter_enabled_) {
    for (size_t angle = 0; angle < NUM_ANGLES; angle++) {
        const auto &distances = tmp_distances[angle];
        const auto &intensities = tmp_intensities[angle];
        size_t size = distances.size();
        if (size > 0) {
            lidar_data_[angle][0] = std::accumulate(distances.begin(), distances.end(), 0) / size;
            lidar_data_[angle][1] = std::accumulate(intensities.begin(), intensities.end(), 0) / size;
        }
        else {
            lidar_data_[angle][0] = max_distance;  // Mark as invalid
            lidar_data_[angle][1] = 0;  // Mark as invalid
        }
    }

    if (data_write_lock_ != nullptr) {
        data_write_lock_->finishWriting();
        data_write_lock_->postUpdate();
    }
}

} // namespace ldlidar
