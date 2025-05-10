#pragma once

#include "locker.h"
#include "thread.h"
#include "ydlidar_protocol.h"

#include <libserial/SerialPort.h>

#include <atomic>
#include <cstdlib>
#include <map>

using namespace std;

namespace ydlidar {

typedef int32_t result_t;

#define RESULT_OK      0
#define RESULT_TIMEOUT -1
#define RESULT_FAIL    -2

#define IS_OK(x)    ( (x) == RESULT_OK )
#define IS_TIMEOUT(x)  ( (x) == RESULT_TIMEOUT )
#define IS_FAIL(x)  ( (x) == RESULT_FAIL )

enum {
    DEFAULT_TIMEOUT = 2000,    ///< Default timeout.
    MAX_SCAN_NODES = 7200,	   ///< Default Max Scan Count.
    DEFAULT_TIMEOUT_COUNT = 1, //< Default Timeout Count.
};

typedef enum {
    NoError = 0,
    DeviceNotFoundError,
    PermissionError,
    UnsupportedOperationError,
    UnknownError,
    TimeoutError,
    NotOpenError,
    BlockError,
    NotBufferError,
    TrembleError,
    LaserFailureError,
} driver_error_t;

/**
 * Class that provides a lidar interface.
 */
class YDlidarDriver {
public:
    /**
     * A constructor.
     * A more elaborate description of the constructor.
     */
    explicit YDlidarDriver();

    /**
     * A destructor.
     * A more elaborate description of the destructor.
     */
    ~YDlidarDriver();

    /**
     * @brief Connecting Lidar.
     * After the connection if successful, you must use ::disconnect to close
     * @param[in] port_path    serial port
     * @return connection status
     * @retval 0     success
     * @retval < 0   failed
     * @note After the connection if successful, you must use ::disconnect to close
     */
    result_t connect(const char* port_path);

    /**
     * @brief Disconnect the LiDAR.
     */
    void disconnect();

    /**
     * @brief Is the Lidar in the scan
     * @return scanning status
     * @retval true     scanning
     * @retval false    non-scanning
     */
    bool isScanning() const;

    /**
     * @brief Is it connected to the lidar
     * @return connection status
     * @retval true     connected
     * @retval false    Non-connected
     */
    bool isConnected() const;

    /**
     * @brief get Health status
     * @return result status
     * @retval RESULT_OK                         success
     * @retval RESULT_FAILED or RESULT_TIMEOUT   failed
     */
    result_t getHealth(device_health_t& health,
        uint32_t timeout = DEFAULT_TIMEOUT);

    /**
     * @brief get Device information
     * @param[in] info     Device information
     * @param[in] timeout  timeout
     * @return result status
     * @retval RESULT_OK                         success
     * @retval RESULT_FAILED or RESULT_TIMEOUT   failed
     */
    result_t getDeviceInfo(device_info_t& info,
        uint32_t timeout = DEFAULT_TIMEOUT);

    /**
     * @brief Turn on scanning
     * @param[in] force    Scan mode
     * @param[in] timeout  timeout
     * @return result status
     * @retval RESULT_OK       success
     * @retval RESULT_FAILED   failed
     * @note Just turn it on once
     */
    result_t startScan(bool force = false,
        uint32_t timeout = DEFAULT_TIMEOUT);

    /**
     * @brief turn off scanning
     * @return result status
     * @retval RESULT_OK       success
     * @retval RESULT_FAILED   failed
     */
    result_t stop();

    /**
     * @brief Get a circle of laser data
     * @param[in] nodebuffer Laser data
     * @param[in] count      one circle of laser points
     * @param[in] timeout    timeout
     * @return return status
     * @retval RESULT_OK       success
     * @retval RESULT_FAILED   failed
     * @note Before starting, you must start the start the scan successfully with the ::startScan function
     */
    result_t grabScanData(node_info_t* nodebuffer, size_t& count,
        uint32_t timeout = DEFAULT_TIMEOUT);

    /**
     * @brief start motor
     * @return return status
     * @retval RESULT_OK       success
     * @retval RESULT_FAILED   failed
     */
    result_t startMotor();

    /**
     * @brief stop motor
     * @return return status
     * @retval RESULT_OK       success
     * @retval RESULT_FAILED   failed
     */
    result_t stopMotor();

    /**
     * @brief Set and Get Sampling interval.
     * @note Negative correlation between sampling interval and lidar sampling rate.\n
     * sampling interval = 1e9 / sampling rate(/s)\n
     * Set the LiDAR sampling interval to match the LiDAR.
     */
    inline void setPointTime(uint32_t v) {
        point_time_ = v;
    }

    inline uint32_t getPointTime() const {
        return point_time_;
    }

    /**
    * @brief Get lidar scan frequency
    * @param[in] frequency    scanning frequency
    * @param[in] timeout      timeout
    * @return return status
    * @retval RESULT_OK       success
    * @retval RESULT_FAILED   failed
    * @note Non-scan state, perform currect operation.
    */
    result_t getScanFrequency(scan_frequency_t& frequency,
        uint32_t timeout = DEFAULT_TIMEOUT);

    /**
     * @brief Increase the scanning frequency by 1.0 HZ
     * @param[in] frequency    scanning frequency
     * @param[in] timeout      timeout
     * @return return status
     * @retval RESULT_OK       success
     * @retval RESULT_FAILED   failed
     * @note Non-scan state, perform currect operation.
     */
    result_t setScanFrequencyAdd(scan_frequency_t& frequency,
        uint32_t timeout = DEFAULT_TIMEOUT);

    /**
     * @brief Reduce the scanning frequency by 1.0 HZ
     * @param[in] frequency    scanning frequency
     * @param[in] timeout      timeout
     * @return return status
     * @retval RESULT_OK       success
     * @retval RESULT_FAILED   failed
     * @note Non-scan state, perform currect operation.
     */
    result_t setScanFrequencyDis(scan_frequency_t& frequency,
        uint32_t timeout = DEFAULT_TIMEOUT);

    /**
     * @brief Increase the scanning frequency by 0.1 HZ
     * @param[in] frequency    scanning frequency
     * @param[in] timeout      timeout
     * @return return status
     * @retval RESULT_OK       success
     * @retval RESULT_FAILED   failed
     * @note Non-scan state, perform currect operation.
     */
    result_t setScanFrequencyAddMic(scan_frequency_t& frequency,
        uint32_t timeout = DEFAULT_TIMEOUT);

    /**
     * @brief Reduce the scanning frequency by 0.1 HZ
     * @param[in] frequency    scanning frequency
     * @param[in] timeout      timeout
     * @return return status
     * @retval RESULT_OK       success
     * @retval RESULT_FAILED   failed
     * @note Non-scan state, perform currect operation.
     */
    result_t setScanFrequencyDisMic(scan_frequency_t& frequency,
        uint32_t timeout = DEFAULT_TIMEOUT);

    /**
     * @brief Set the lidar sampling frequency
     * @param[in] rate    　　　sampling frequency
     * @param[in] timeout      timeout
     * @return return status
     * @retval RESULT_OK       success
     * @retval RESULT_FAILED   failed
     * @note Non-scan state, perform currect operation.
     */
    result_t setSamplingRate(sampling_rate_t& rate,
        uint32_t timeout = DEFAULT_TIMEOUT);

    /**
     * @brief setDriverError
     * @param er
     */
    virtual void setDriverError(const driver_error_t& er) {
        ScopedLocker l(error_lock_);
        driver_errno_ = er;
    }

    /**
     * @brief getDriverError
     * @return
     */
    driver_error_t getDriverError() {
        ScopedLocker l(error_lock_);
        return driver_errno_;
    }

    /**
     * @brief getDriverErrorText
     * @return
     */
    char const* getDriverErrorText() {
        char const* errorString = "Unknown error";

        switch (getDriverError()) {
        case NoError:
            errorString = ("No error");
            break;

        case DeviceNotFoundError:
            errorString = ("Device is not found");
            break;

        case PermissionError:
            errorString = ("Device is not permission");
            break;

        case UnsupportedOperationError:
            errorString = ("unsupported operation");
            break;

        case NotOpenError:
            errorString = ("Device is not open");
            break;

        case TimeoutError:
            errorString = ("Operation timed out");
            break;

        case BlockError:
            errorString = ("Device Block");
            break;

        case NotBufferError:
            errorString = ("Device Failed");
            break;

        case TrembleError:
            errorString = ("Device Tremble");
            break;

        case LaserFailureError:
            errorString = ("Laser Failure");
            break;

        default:
            // an empty string will be interpreted as "Unknown error"
            break;
        }

        return errorString;
    };

protected:

    /**
    * @brief Data parsing thread
    * @note Before you create a dta parsing thread, you must use the ::startScan function to start the lidar scan successfully.
    */
    result_t createThread();

    /**
    * @brief Automatically reconnect the lidar
    * @param[in] force    scan mode
    * @param[in] timeout  timeout
    * @return return status
    * @retval RESULT_OK       success
    * @retval RESULT_FAILED   failed
    * @note Lidar abnormality automatically reconnects.
    */
    result_t startAutoScan(bool force = false, uint32_t timeout = DEFAULT_TIMEOUT);

    /**
    * @brief stop Scanning state
    * @param timeout  timeout
    * @return status
    * @retval RESULT_OK       success
    * @retval RESULT_FAILED   failed
    */
    result_t stopScan(uint32_t timeout = DEFAULT_TIMEOUT);

    /**
     * @brief check single-channel lidar device information
     * @param recvBuffer  LiDAR Data buffer
     * @param byte        current byte
     * @param recvPos     current received pos
     * @param recvSize    Buffer size
     * @param pos         Device Buffer pos
     * @return status
     * @retval RESULT_OK       success
     * @retval RESULT_FAILED   failed
     */
    result_t checkDeviceInfo(uint8_t* recvBuffer, uint8_t byte, int recvPos,
        int recvSize, int pos);

    /**
     * @brief waiting device information
     * @param timeout timeout
     * @return status
     * @retval RESULT_OK       success
     * @retval RESULT_FAILED   failed
     */
    result_t waitDevicePackage(uint32_t timeout = DEFAULT_TIMEOUT);

    /**
     * @brief parseResponseHeader
     * @param packageBuffer
     * @param timeout
     * @return
     */
    result_t parseResponseHeader(uint8_t* packageBuffer,
        uint32_t timeout = DEFAULT_TIMEOUT);

    /**
     * @brief parseResponseScanData
     * @param packageBuffer
     * @param timeout
     * @return
     */
    result_t parseResponseScanData(uint8_t* packageBuffer,
        uint32_t timeout = DEFAULT_TIMEOUT);
    /**
    * @brief Unpacking
    * @param[in] node lidar point information
    * @param[in] timeout     timeout
    */
    result_t waitPackage(node_info_t* node, uint32_t timeout = DEFAULT_TIMEOUT);

    /**
    * @brief get unpacked data
    * @param[in] nodebuffer laser node
    * @param[in] count      lidar points size
    * @param[in] timeout      timeout
    * @return result status
    * @retval RESULT_OK       success
    * @retval RESULT_TIMEOUT  timeout
    * @retval RESULT_FAILED   failed
    */
    result_t waitScanData(node_info_t* nodebuffer, size_t& count,
        uint32_t timeout = DEFAULT_TIMEOUT);

    /**
     * @brief data parsing thread
     */
    int cacheScanData();

    /**
     * @brief send data to lidar
     * @param[in] cmd 	 command code
     * @param[in] payload      payload
     * @param[in] payloadsize      payloadsize
     * @return result status
     * @retval RESULT_OK       success
     * @retval RESULT_FAILED   failed
     */
    result_t sendCommand(uint8_t cmd, const void* payload = NULL,
        size_t payloadsize = 0);

    /**
     * @brief waiting for package header
     * @param[in] header 	 package header
     * @param[in] timeout      timeout
     * @return return status
     * @retval RESULT_OK       success
     * @retval RESULT_TIMEOUT  timeout
     * @retval RESULT_FAILED   failed
     * @note when timeout = -1, it will block...
     */
    result_t waitResponseHeader(lidar_ans_header_t* header,
        uint32_t timeout = DEFAULT_TIMEOUT);

    /**
     * @brief Waiting for the specified size data from the lidar
     * @param[in] data_count 	 wait max data size
     * @param[in] timeout    	 timeout
     * @param[in] returned_size   really data size
     * @return return status
     * @retval RESULT_OK       success
     * @retval RESULT_TIMEOUT  wait timeout
     * @retval RESULT_FAILED   failed
     * @note when timeout = -1, it will block...
     */
    result_t waitForData(size_t data_count, uint32_t timeout = DEFAULT_TIMEOUT,
        size_t* returned_size = NULL);

    /**
     * @brief get data from serial
     * @param[in] data 	 data
     * @param[in] size    date size
     * @return return status
     * @retval RESULT_OK       success
     * @retval RESULT_FAILED   failed
     */
    result_t getData(uint8_t* data, size_t size);

    /**
     * @brief send data to serial
     * @param[in] data 	 data
     * @param[in] size    data size
     * @return return status
     * @retval RESULT_OK       success
     * @retval RESULT_FAILED   failed
     */
    result_t sendData(const uint8_t* data, size_t size);


    /**
     * @brief disable Data scan channel
     */
    void disableDataGrabbing();

    /*!
        * @brief set DTR
        */
    void setDTR();

    /**
     * @brief clear DTR \n
     */
    void clearDTR();

    /**
     * @brief flushSerial
     */
    void flushSerial();

    /**
     * @brief CheckLaserStatus
     */
    void CheckLaserStatus();

    /**
     * @brief checkBlockStatus
     */
    void checkBlockStatus(uint8_t currentByte);

    /**
     * @brief calculateCheckSum
     * @param node
     */
    void calculateCheckSum(node_info_t* node);

    /**
     * @brief calculatePackageCT
     */
    void calculatePackageCT();

    /**
     * @brief parseNodeDebugFromBuffer
     */
    void parseNodeDebugFromBuffer(node_info_t* node);

    /**
     * @brief parseNodeFromBuffer
     */
    void parseNodeFromBuffer(node_info_t* node);

private:
    /// LiDAR Scanning state
    bool is_scanning_ = false;
    /// LiDAR connected state
    bool is_connected_ = false;
    /// Scan Data Event
    Event data_event_;
    /// Data Locker
    Locker lock_;
    /// Parse Data thread
    Thread thread_;
    /// command locker
    Locker cmd_lock_;
    /// driver error locker
    Locker error_lock_;
    /// LiDAR intensity bit
    int intensity_bit_;
    uint32_t point_time_;
    /// LiDAR Point pointer
    node_info_t* scan_node_buf_;
    /// LiDAR scan count
    size_t scan_node_count_;
    /// package sample index
    uint16_t package_sample_index_;
    /// number of last error
    driver_error_t driver_errno_;
    /// invalid node count
    int invalid_node_count_;
    /// package sample bytes
    int package_sample_bytes;
    /// serial port
    LibSerial::SerialPort* serial_;
    /// has intensity protocol package
    node_package_t package_;
    float interval_sample_angle_;
    float interval_sample_angle_last_package_;
    /// First sample angle
    uint16_t first_sample_angle_;
    /// last sample angle
    uint16_t last_sample_angle_;
    /// checksum
    uint16_t check_sum_;
    /// scan frequency
    uint8_t scan_frequency_;
    uint16_t checksum_cal_;
    uint16_t sample_num_and_ct_cal_;
    uint16_t last_sample_angle_cal_;
    bool checksum_result_;
    uint16_t val_u8_to_u16_;
    uint8_t package_ct_;
    uint8_t now_package_num;
    uint8_t package_sample_num_;
    uint8_t* global_recv_buffer_;
    bool has_device_header_;
    uint8_t last_device_byte_;
    int async_recv_pos_;
    uint16_t async_size_;
    device_info_t info_;
    device_health_t health_;
    lidar_ans_header_t header_;
    uint8_t* header_buffer_;
    uint8_t* info_buffer_;
    uint8_t* health_buffer_;
    bool get_device_info_success_;
    int package_index;
    bool has_package_error;
    uint8_t block_rev_size;
    uint32_t data_pos_ = 0;
    uint64_t stamp_ = 0;
};

} // namespace ydlidar
