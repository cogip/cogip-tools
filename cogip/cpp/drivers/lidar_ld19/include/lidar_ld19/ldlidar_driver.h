#pragma once

#include "lidar_ld19/ldlidar_datatype.h"
#include "lidar_ld19/ldlidar_protocol.h"
#include "shared_memory/WritePriorityLock.hpp"

#include <libserial/SerialPort.h>

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>

#include <atomic>
#include <chrono>
#include <functional>
#include <mutex>
#include <thread>

namespace nb = nanobind;

namespace ldlidar {

constexpr size_t MAX_ACK_BUF_LEN = 512;
constexpr size_t NUM_ANGLES = 360;

uint64_t getSystemTimeStamp();

class LDLidarDriver {
public:
    /// Constructor with optional external memory pointer
    explicit LDLidarDriver(uint16_t (*external_lidar_data)[2] = nullptr);

    /// Constructor accepting a nanobind::ndarray
    explicit LDLidarDriver(nb::ndarray<uint16_t, nb::numpy, nb::shape<NUM_ANGLES, 2>> external_lidar_data);

    ~LDLidarDriver();

    /// Gets the running status of the LiDAR driver.
    /// @return `true` if the driver is running, `false` otherwise.
    static bool ok() { return is_ok_; }

    /// Sets the running status of the LiDAR driver.
    /// @param status The new running status to set.
    static void setLidarDriverStatus(bool status) { is_ok_ = status; }

    /// Opens the communication port and asserts the initialization parameters.
    /// @param serial_port_name The serial device system path (e.g., "/dev/ttyUSB0").
    /// @param serial_baudrate The baud rate for serial communication, in bits per second. Default is 230400.
    /// @return `true` if the connection is successfully established, `false` otherwise.
    bool connect(
        const std::string &serial_port_name,
        LibSerial::BaudRate serial_baudrate = LibSerial::BaudRate::BAUD_230400
    );

    /// Closes the communication port.
    /// @return `true` if the disconnection is successful, `false` otherwise.
    bool disconnect();

    /// Checks if the communication channel is operational after powering on the LiDAR.
    /// @param timeout The wait timeout in milliseconds.
    /// @return `true` if the communication connection is successful within the timeout; `false` otherwise.
    bool waitLidarComm(int64_t timeout);

    /// Retrieves the LiDAR's scan frequency.
    /// @param spin_hz [output] The LiDAR scan frequency in Hz.
    /// @return `true` if the scan frequency is successfully retrieved, `false` otherwise.
    bool getLidarScanFreq(double &spin_hz) const;

    /// Retrieves the error code when the LiDAR is in an error state.
    /// @return The error code from the LiDAR.
    uint8_t getLidarErrorCode() const;

    /// Starts the LiDAR driver node.
    /// @return `true` if the driver starts successfully, `false` otherwise.
    bool start();

    /// Stops the LiDAR driver node.
    /// @return `true` if the driver stops successfully, `false` otherwise.
    bool stop();

    /// Function executed in a thread to read and process data from serial port.
    void rxThreadProc();

    /// Function executed after reading data on serial port.
    void commReadCallback(const char *byte, size_t len);

    /// Get pointer to internal lidar points
    const uint16_t (&getLidarData() const)[2] { return *lidar_data_; }

    /// Get Lidar spin speed (Hz)
    double getSpeed() const { return (speed_ / 360.0); };

    LidarStatus getLidarStatus() { return lidar_status_; };

    uint8_t getLidarErrorCode() { return lidar_error_code_; };

    bool getLidarPowerOnCommStatus();

    void clearStatus() {
        is_frame_ready_ = false;
        is_poweron_comm_normal_ = false;
        lidar_status_ = LidarStatus::NORMAL;
        lidar_error_code_ = LIDAR_NO_ERROR;
        last_pkg_timestamp_ = 0;
        tmp_lidar_scan_data_vec_.clear();
    }

    /// Set the data write lock.
    void setDataWriteLock(cogip::shared_memory::WritePriorityLock &lock) {
        data_write_lock_ = &lock;
    }
    }

protected:
    bool is_start_flag_;
    bool is_connect_flag_;

private:
    static bool is_ok_;
    LibSerial::SerialPort *comm_serial_;
    std::chrono::_V2::steady_clock::time_point last_pubdata_times_;
    std::atomic<bool> rx_thread_exit_flag_;
    std::thread *rx_thread_;
    int lidar_measure_freq_;
    LidarStatus lidar_status_;
    uint8_t lidar_error_code_;
    bool is_frame_ready_;
    bool is_noise_filter_;
    cogip::shared_memory::WritePriorityLock *data_write_lock_;
    uint16_t timestamp_;
    double speed_;
    bool is_poweron_comm_normal_;
    uint64_t last_pkg_timestamp_;
    LdLidarProtocol *protocol_handle_;
    Points2D tmp_lidar_scan_data_vec_;
    uint16_t (*lidar_data_)[2];  ///< Pointer to lidar data memory
    bool external_data_;           ///< Flag to indicate if memory is externally managed
    std::mutex mutex_lock1_;
    std::mutex mutex_lock2_;

    void commonInit();

    bool parse(const uint8_t *data, long len);

    // Combine standard data into data frames and calibrate.
    bool assemblePacket();

    // Get Lidar data frame ready flag.
    bool isFrameReady();

    /// Reset frame ready flag.
    void resetFrameReady();

    // Set frame ready flag.
    void setFrameReady();

    void setLaserScanData(Points2D &src);
};

} // namespace ldlidar
