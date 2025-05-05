#include "ydlidar_g2/timer.h"
#include "ydlidar_g2/YDLidarDriver.h"

#include <chrono>
#include <cmath>
#include <cstring>
#include <iostream>
#include <thread>

namespace ydlidar {

YDlidarDriver::YDlidarDriver() {
    intensity_bit_ = 10;
    scan_node_buf_ = new node_info_t[MAX_SCAN_NODES];
    scan_node_count_ = 0;
    package_sample_index_ = 0;
    serial_ = nullptr;
    is_scanning_ = false;
    is_connected_ = false;
    driver_errno_ = NoError;
    invalid_node_count_ = 0;
    point_time_ = 1e9 / 5000;
    scan_frequency_ = 0;
    has_device_header_ = false;
    package_sample_bytes = 3;
    interval_sample_angle_ = 0.0;
    first_sample_angle_ = 0;
    last_sample_angle_ = 0;
    check_sum_ = 0;
    checksum_cal_ = 0;
    sample_num_and_ct_cal_ = 0;
    last_sample_angle_cal_ = 0;
    checksum_result_ = true;
    val_u8_to_u16_ = 0;
    package_ct_ = CT_Normal;
    now_package_num = 0;
    package_sample_num_ = 0;
    last_device_byte_ = 0x00;
    async_recv_pos_ = 0;
    async_size_ = 0;
    header_buffer_ = reinterpret_cast<uint8_t*>(&header_);
    info_buffer_ = reinterpret_cast<uint8_t*>(&info_);
    health_buffer_ = reinterpret_cast<uint8_t*>(&health_);
    global_recv_buffer_ = new uint8_t[sizeof(node_packages_t)];
    package_index = 0;
    has_package_error = false;

    get_device_info_success_ = false;
    interval_sample_angle_last_package_ = 0.0;
    block_rev_size = 0;
}

YDlidarDriver::~YDlidarDriver() {
    {
        is_scanning_ = false;
    }

    thread_.join();
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    ScopedLocker lck(cmd_lock_);

    if (serial_) {
        if (serial_->IsOpen()) {
            serial_->FlushInputBuffer();
            serial_->Close();
        }
    }

    if (serial_) {
        delete serial_;
        serial_ = NULL;
    }

    if (global_recv_buffer_) {
        delete[] global_recv_buffer_;
        global_recv_buffer_ = NULL;
    }

    if (scan_node_buf_) {
        delete[] scan_node_buf_;
        scan_node_buf_ = NULL;
    }
}


result_t YDlidarDriver::connect(const char* port_path) {
    ScopedLocker lck(cmd_lock_);

    if (!serial_) {
        serial_ = new LibSerial::SerialPort(
            port_path,
            LibSerial::BaudRate::BAUD_230400
        );

        is_connected_ = true;
    }

    stopScan();
    std::this_thread::sleep_for(std::chrono::milliseconds(1100));
    clearDTR();

    return RESULT_OK;
}

void YDlidarDriver::setDTR() {
    if (!is_connected_) {
        return;
    }

    if (serial_) {
        serial_->SetDTR(true);
    }

}

void YDlidarDriver::clearDTR() {
    if (!is_connected_) {
        return;
    }

    if (serial_) {
        serial_->SetDTR(false);
    }
}
void YDlidarDriver::flushSerial() {
    if (!is_connected_) {
        return;
    }

    serial_->FlushIOBuffers();

    std::this_thread::sleep_for(std::chrono::milliseconds(20));
}


void YDlidarDriver::disconnect() {
    if (!is_connected_) {
        return;
    }

    stop();
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    ScopedLocker l(cmd_lock_);

    if (serial_) {
        if (serial_->IsOpen()) {
            serial_->Close();
        }
    }

    is_connected_ = false;

}


void YDlidarDriver::disableDataGrabbing() {
    {
        if (is_scanning_) {
            is_scanning_ = false;
            data_event_.set();
        }
    }
    thread_.join();
}

bool YDlidarDriver::isScanning() const {
    return is_scanning_;
}

bool YDlidarDriver::isConnected() const {
    return is_connected_;
}

result_t YDlidarDriver::sendCommand(uint8_t cmd, const void* payload,
    size_t payloadsize) {
    uint8_t pkt_header[10];
    cmd_packet_t* header = reinterpret_cast<cmd_packet_t*>(pkt_header);
    uint8_t checksum = 0;

    if (!is_connected_) {
        return RESULT_FAIL;
    }

    if (payloadsize && payload) {
        cmd |= LIDAR_CMDFLAG_HAS_PAYLOAD;
    }

    header->syncByte = LIDAR_CMD_SYNC_BYTE;
    header->cmd_flag = cmd;
    sendData(pkt_header, 2);

    if ((cmd & LIDAR_CMDFLAG_HAS_PAYLOAD) && payloadsize && payload) {
        checksum ^= LIDAR_CMD_SYNC_BYTE;
        checksum ^= cmd;
        checksum ^= (payloadsize & 0xFF);

        for (size_t pos = 0; pos < payloadsize; ++pos) {
            checksum ^= ((uint8_t*)payload)[pos];
        }

        uint8_t sizebyte = (uint8_t)(payloadsize);
        sendData(&sizebyte, 1);

        sendData((const uint8_t*)payload, sizebyte);

        sendData(&checksum, 1);
    }

    return RESULT_OK;
}

result_t YDlidarDriver::sendData(const uint8_t* data, size_t size) {
    if (!is_connected_) {
        return RESULT_FAIL;
    }

    if (data == NULL || size == 0) {
        return RESULT_FAIL;
    }

    for (size_t i = 0; i < size; i++) {
        serial_->WriteByte(data[i]);
    }

    return RESULT_OK;
}

result_t YDlidarDriver::getData(uint8_t* data, size_t size) {
    if (!is_connected_) {
        return RESULT_FAIL;
    }

    static LibSerial::DataBuffer buffer(1024);

    try {
        serial_->Read(buffer, size, DEFAULT_TIMEOUT);
    }
    catch (const LibSerial::ReadTimeout& e) {
        return RESULT_FAIL;
    }

    for (size_t i = 0; i < size; i++) {
        data[i] = buffer[i];
    }

    return RESULT_OK;
}

result_t YDlidarDriver::waitResponseHeader(lidar_ans_header_t* header,
    uint32_t timeout) {
    int  recvPos = 0;
    uint32_t startTs = getHDTimer();
    uint8_t  recvBuffer[sizeof(lidar_ans_header_t)];
    uint8_t* header_buffer_ = reinterpret_cast<uint8_t*>(header);
    uint32_t waitTime = 0;
    has_device_header_ = false;
    last_device_byte_ = 0x00;

    while ((waitTime = getHDTimer() - startTs) <= timeout) {
        size_t remainSize = sizeof(lidar_ans_header_t) - recvPos;
        size_t recvSize = 0;
        result_t ans = waitForData(remainSize, timeout - waitTime, &recvSize);

        if (!IS_OK(ans)) {
            return ans;
        }

        if (recvSize > remainSize) {
            recvSize = remainSize;
        }

        ans = getData(recvBuffer, recvSize);

        if (IS_FAIL(ans)) {
            return RESULT_FAIL;
        }

        for (size_t pos = 0; pos < recvSize; ++pos) {
            uint8_t currentByte = recvBuffer[pos];

            switch (recvPos) {
            case 0:
                if (currentByte != LIDAR_ANS_SYNC_BYTE1) {
                    if (last_device_byte_ == (PH & 0xFF) && currentByte == (PH >> 8)) {
                        has_device_header_ = true;
                    }

                    last_device_byte_ = currentByte;
                    continue;
                }

                break;

            case 1:
                if (currentByte != LIDAR_ANS_SYNC_BYTE2) {
                    last_device_byte_ = currentByte;
                    recvPos = 0;
                    continue;
                }

                break;
            }

            header_buffer_[recvPos++] = currentByte;
            last_device_byte_ = currentByte;

            if (recvPos == sizeof(lidar_ans_header_t)) {
                return RESULT_OK;
            }
        }
    }

    return RESULT_FAIL;
}

result_t YDlidarDriver::waitForData(size_t data_count, uint32_t timeout, size_t* returned_size) {
    size_t length = 0;

    if (returned_size == nullptr) {
        returned_size = &length;
    }

    auto start_time = std::chrono::steady_clock::now();

    while (true) {
        // Check if data is available
        size_t available_bytes = serial_->GetNumberOfBytesAvailable();
        if (available_bytes >= data_count) {
            *returned_size = available_bytes;
            return RESULT_OK;
        }

        // Check if the timeout has been reached
        auto current_time = std::chrono::steady_clock::now();
        auto elapsed_time = std::chrono::duration_cast<std::chrono::milliseconds>(current_time - start_time).count();
        if (elapsed_time >= timeout) {
            *returned_size = available_bytes;
            return RESULT_TIMEOUT;
        }

        // Sleep for a short period before checking again
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

void YDlidarDriver::CheckLaserStatus() {
    if (invalid_node_count_ < 2) {
        if (driver_errno_ == NoError) {
            setDriverError(LaserFailureError);
        }
    }
    else {
        if (driver_errno_ == LaserFailureError) {
            setDriverError(NoError);
        }
    }

    invalid_node_count_ = 0;
}

int YDlidarDriver::cacheScanData() {
    node_info_t      local_buf[128];
    size_t         count = 128;
    node_info_t      local_scan[MAX_SCAN_NODES];
    size_t         scan_count = 0;
    result_t       ans = RESULT_FAIL;
    memset(local_scan, 0, sizeof(local_scan));

    flushSerial();
    waitScanData(local_buf, count);

    int timeout_count = 0;
    bool m_last_frame_valid = false;

    while (is_scanning_) {
        count = 128;
        ans = waitScanData(local_buf, count, DEFAULT_TIMEOUT / 2);
        if (!IS_OK(ans)) {
            if (IS_FAIL(ans) || timeout_count > DEFAULT_TIMEOUT_COUNT) {
                std::cerr << "[YDLidarDriver] Exit scanning thread" << std::endl;
                is_scanning_ = false;
                return RESULT_FAIL;
            }
            else {
                timeout_count++;
                local_scan[0].sync_flag = NODE_NOT_SYNC;

                if (driver_errno_ == NoError) {
                    setDriverError(TimeoutError);
                }

                std::cerr << "[YDLidarDriver] Timeout count: " << timeout_count << std::endl;
            }
        }
        else {
            timeout_count = 0;
            m_last_frame_valid = true;
        }

        for (size_t pos = 0; pos < count; ++pos) {
            if (local_buf[pos].sync_flag & LIDAR_RESP_MEASUREMENT_SYNCBIT) {
                if (local_scan[0].sync_flag & LIDAR_RESP_MEASUREMENT_SYNCBIT) {
                    lock_.lock(); // timeout lock, wait resource copy
                    local_scan[0].delay_time = local_buf[pos].delay_time;
                    memcpy(scan_node_buf_, local_scan, scan_count * sizeof(node_info_t));
                    scan_node_count_ = scan_count;
                    data_event_.set();
                    lock_.unlock();
                }

                scan_count = 0;
            }

            local_scan[scan_count++] = local_buf[pos];

            if (scan_count == _countof(local_scan)) {
                scan_count -= 1;
            }
        }
    }

    is_scanning_ = false;

    return RESULT_OK;
}

result_t YDlidarDriver::checkDeviceInfo(uint8_t* recvBuffer, uint8_t byte,
    int recvPos, int recvSize, int pos) {
    if (async_recv_pos_ == sizeof(lidar_ans_header_t)) {
        if ((((pos < recvSize - 1) && byte == LIDAR_ANS_SYNC_BYTE1) ||
            (last_device_byte_ == LIDAR_ANS_SYNC_BYTE1 && byte == LIDAR_ANS_SYNC_BYTE2)) &&
            recvPos == 0) {
            if ((last_device_byte_ == LIDAR_ANS_SYNC_BYTE1 &&
                byte == LIDAR_ANS_SYNC_BYTE2)) {
                async_recv_pos_ = 0;
                async_size_ = 0;
                header_buffer_[async_recv_pos_] = last_device_byte_;
                async_recv_pos_++;
                header_buffer_[async_recv_pos_] = byte;
                async_recv_pos_++;
                last_device_byte_ = byte;
                return RESULT_OK;
            }
            else {
                if (pos < recvSize - 1) {
                    if (recvBuffer[pos + 1] == LIDAR_ANS_SYNC_BYTE2) {
                        async_recv_pos_ = 0;
                        async_size_ = 0;
                        header_buffer_[async_recv_pos_] = byte;
                        async_recv_pos_++;
                        last_device_byte_ = byte;
                        return RESULT_OK;
                    }
                }

            }

        }

        last_device_byte_ = byte;

        if (header_.type == LIDAR_ANS_TYPE_DEVINFO ||
            header_.type == LIDAR_ANS_TYPE_DEV_HEALTH) {
            if (header_.size < 1) {
                async_recv_pos_ = 0;
                async_size_ = 0;
            }
            else {

                if (header_.type == LIDAR_ANS_TYPE_DEV_HEALTH) {
                    if (async_size_ < sizeof(health_)) {
                        health_buffer_[async_size_] = byte;
                        async_size_++;

                        if (async_size_ == sizeof(health_)) {
                            async_recv_pos_ = 0;
                            async_size_ = 0;
                            last_device_byte_ = byte;
                            return RESULT_OK;
                        }

                    }
                    else {
                        async_recv_pos_ = 0;
                        async_size_ = 0;
                    }

                }
                else {

                    if (async_size_ < sizeof(info_)) {
                        info_buffer_[async_size_] = byte;
                        async_size_++;

                        if (async_size_ == sizeof(info_)) {
                            async_recv_pos_ = 0;
                            async_size_ = 0;
                            get_device_info_success_ = true;

                            last_device_byte_ = byte;
                            return RESULT_OK;
                        }

                    }
                    else {
                        async_recv_pos_ = 0;
                        async_size_ = 0;
                    }
                }
            }
        }
        else if (header_.type == LIDAR_ANS_TYPE_MEASUREMENT) {
            async_recv_pos_ = 0;
            async_size_ = 0;

        }

    }
    else {

        switch (async_recv_pos_) {
        case 0:
            if (byte == LIDAR_ANS_SYNC_BYTE1 && recvPos == 0) {
                header_buffer_[async_recv_pos_] = byte;
                last_device_byte_ = byte;
                async_recv_pos_++;
            }

            break;

        case 1:
            if (byte == LIDAR_ANS_SYNC_BYTE2 && recvPos == 0) {
                header_buffer_[async_recv_pos_] = byte;
                async_recv_pos_++;
                last_device_byte_ = byte;
                return RESULT_OK;
            }
            else {
                async_recv_pos_ = 0;
            }

            break;

        default:
            break;
        }

        if (async_recv_pos_ >= 2) {
            if (((pos < recvSize - 1 && byte == LIDAR_ANS_SYNC_BYTE1) ||
                (last_device_byte_ == LIDAR_ANS_SYNC_BYTE1 && byte == LIDAR_ANS_SYNC_BYTE2)) &&
                recvPos == 0) {
                if ((last_device_byte_ == LIDAR_ANS_SYNC_BYTE1 &&
                    byte == LIDAR_ANS_SYNC_BYTE2)) {
                    async_recv_pos_ = 0;
                    async_size_ = 0;
                    header_buffer_[async_recv_pos_] = last_device_byte_;
                    async_recv_pos_++;
                }
                else {
                    if (pos < recvSize - 2) {
                        if (recvBuffer[pos + 1] == LIDAR_ANS_SYNC_BYTE2) {
                            async_recv_pos_ = 0;
                        }
                    }
                }
            }

            header_buffer_[async_recv_pos_] = byte;
            async_recv_pos_++;
            last_device_byte_ = byte;
            return RESULT_OK;
        }
    }

    return RESULT_FAIL;

}

result_t YDlidarDriver::waitDevicePackage(uint32_t timeout) {
    int recvPos = 0;
    async_recv_pos_ = 0;
    uint32_t startTs = getHDTimer();
    uint32_t waitTime = 0;
    result_t ans = RESULT_FAIL;

    while ((waitTime = getHDTimer() - startTs) <= timeout) {
        size_t remainSize = PACKAGE_PAID_BYTES - recvPos;
        size_t recvSize = 0;
        result_t ans = waitForData(remainSize, timeout - waitTime, &recvSize);

        if (!IS_OK(ans)) {
            return ans;
        }

        ans = RESULT_FAIL;

        if (recvSize > remainSize) {
            recvSize = remainSize;
        }

        getData(global_recv_buffer_, recvSize);

        for (size_t pos = 0; pos < recvSize; ++pos) {
            uint8_t currentByte = global_recv_buffer_[pos];

            if (checkDeviceInfo(global_recv_buffer_, currentByte, recvPos, recvSize,
                pos) == RESULT_OK) {
                continue;
            }
        }

        if (get_device_info_success_) {
            ans = RESULT_OK;
            break;
        }
    }

    flushSerial();
    return ans;
}

void YDlidarDriver::checkBlockStatus(uint8_t currentByte) {
    switch (block_rev_size) {
    case 0:
        if (currentByte == LIDAR_ANS_SYNC_BYTE1) {
            block_rev_size++;
        }

        break;

    case 1:
        if (currentByte == LIDAR_ANS_SYNC_BYTE2) {
            setDriverError(BlockError);
            block_rev_size = 0;
        }

        break;

    default:
        break;
    }
}

result_t YDlidarDriver::parseResponseHeader(
    uint8_t* packageBuffer,
    uint32_t timeout) {
    int recvPos = 0;
    uint32_t startTs = getHDTimer();
    uint32_t waitTime = 0;
    block_rev_size = 0;
    package_sample_num_ = 0;
    uint8_t package_type = 0;
    result_t ans = RESULT_TIMEOUT;

    while ((waitTime = getHDTimer() - startTs) <= timeout) {
        size_t remainSize = PACKAGE_PAID_BYTES - recvPos;
        size_t recvSize = 0;
        ans = waitForData(remainSize, timeout - waitTime, &recvSize);

        if (!IS_OK(ans))
            return ans;

        if (recvSize > remainSize)
            recvSize = remainSize;

        getData(global_recv_buffer_, recvSize);

        for (size_t pos = 0; pos < recvSize; ++pos) {
            uint8_t currentByte = global_recv_buffer_[pos];

            switch (recvPos) {
            case 0:
                if (currentByte != PH1) {
                    checkBlockStatus(currentByte);
                    continue;
                }
                break;

            case 1:
            {
                checksum_cal_ = PH;
                if (currentByte == PH2) {
                    if (driver_errno_ == BlockError) {
                        setDriverError(NoError);
                    }
                }
                else if (currentByte == PH3) {
                    recvPos = 0;
                    size_t lastPos = pos - 1;
                    int remainSize = SIZE_STAMP_PACKAGE - (recvSize - pos + 1);
                    if (remainSize > 0) {
                        size_t lastSize = recvSize;
                        ans = waitForData(remainSize, timeout - waitTime, &recvSize);
                        if (!IS_OK(ans))
                            return ans;
                        if (recvSize > remainSize)
                            recvSize = remainSize;
                        getData(&global_recv_buffer_[lastSize], recvSize);
                        recvSize += lastSize;
                        pos = PACKAGE_PAID_BYTES;
                    }
                    else {
                        pos += 6;
                    }

                    uint8_t csc = 0;
                    uint8_t csr = 0;
                    for (int i = 0; i < SIZE_STAMP_PACKAGE; ++i) {
                        if (i == 2)
                            csr = global_recv_buffer_[lastPos + i];
                        else
                            csc ^= global_recv_buffer_[lastPos + i];
                    }
                    if (csc != csr) {
                        std::cerr << "Stamp checksum error c[0x" << std::hex << static_cast<int>(csc)
                                  << "] != r[0x" << static_cast<int>(csr) << "]" << std::endl;
                    }
                    else {
                        stamp_package_t sp;
                        memcpy(&sp, &global_recv_buffer_[lastPos], SIZE_STAMP_PACKAGE);
                        stamp_ = uint64_t(sp.stamp) * 1000000;
                    }

                    continue;
                }
                else {
                    has_package_error = true;
                    recvPos = 0;
                    continue;
                }
                break;
            }
            case 2:
                sample_num_and_ct_cal_ = currentByte;
                package_type = currentByte & 0x01;

                if ((package_type == CT_Normal) ||
                    (package_type == CT_RingStart)) {
                    if (package_type == CT_RingStart) {
                        scan_frequency_ = (currentByte & 0xFE) >> 1;
                    }
                }
                else {
                    has_package_error = true;
                    recvPos = 0;
                    continue;
                }
                break;

            case 3:
                sample_num_and_ct_cal_ += (currentByte * 0x100);
                package_sample_num_ = currentByte;
                break;

            case 4:
                if (currentByte & LIDAR_RESP_MEASUREMENT_CHECKBIT) {
                    first_sample_angle_ = currentByte;
                }
                else {
                    has_package_error = true;
                    recvPos = 0;
                    continue;
                }
                break;

            case 5:
                first_sample_angle_ += currentByte * 0x100;
                checksum_cal_ ^= first_sample_angle_;
                first_sample_angle_ = first_sample_angle_ >> 1;
                break;

            case 6:
                if (currentByte & LIDAR_RESP_MEASUREMENT_CHECKBIT) {
                    last_sample_angle_ = currentByte;
                }
                else {
                    has_package_error = true;
                    recvPos = 0;
                    continue;
                }

                break;

            case 7:
                last_sample_angle_ = currentByte * 0x100 + last_sample_angle_;
                last_sample_angle_cal_ = last_sample_angle_;
                last_sample_angle_ = last_sample_angle_ >> 1;

                if (package_sample_num_ == 1) {
                    interval_sample_angle_ = 0;
                }
                else {
                    if (last_sample_angle_ < first_sample_angle_) {
                        if ((first_sample_angle_ > 270 * 64) && (last_sample_angle_ < 90 * 64)) {
                            interval_sample_angle_ = (float)((360 * 64 + last_sample_angle_ -
                                first_sample_angle_) /
                                ((
                                    package_sample_num_ - 1) *
                                    1.0));
                            interval_sample_angle_last_package_ = interval_sample_angle_;
                        }
                        else {
                            interval_sample_angle_ = interval_sample_angle_last_package_;
                        }
                    }
                    else {
                        interval_sample_angle_ = (float)((last_sample_angle_ - first_sample_angle_) / ((
                            package_sample_num_ - 1) *
                            1.0));
                        interval_sample_angle_last_package_ = interval_sample_angle_;
                    }
                }

                break;

            case 8:
                check_sum_ = currentByte;
                break;

            case 9:
                check_sum_ += (currentByte * 0x100);
                break;
            }

            packageBuffer[recvPos++] = currentByte;
        }

        if (recvPos == PACKAGE_PAID_BYTES) {
            ans = RESULT_OK;
            break;
        }

        ans = RESULT_TIMEOUT;
    }

    return ans;
}

result_t YDlidarDriver::parseResponseScanData(
    uint8_t* packageBuffer,
    uint32_t timeout) {
    int recvPos = 0;
    uint32_t startTs = getHDTimer();
    uint32_t waitTime = 0;
    result_t ans = RESULT_TIMEOUT;

    while ((waitTime = getHDTimer() - startTs) <= timeout) {
        size_t remainSize = package_sample_num_ * package_sample_bytes - recvPos;
        size_t recvSize = 0;
        ans = waitForData(remainSize, timeout - waitTime, &recvSize);

        if (!IS_OK(ans))
            return ans;

        if (recvSize > remainSize)
            recvSize = remainSize;

        getData(global_recv_buffer_, recvSize);

        for (size_t pos = 0; pos < recvSize; ++pos) {
            if (recvPos % 3 == 2) {
                val_u8_to_u16_ += global_recv_buffer_[pos] * 0x100;
                checksum_cal_ ^= val_u8_to_u16_;
            }
            else if (recvPos % 3 == 1) {
                val_u8_to_u16_ = global_recv_buffer_[pos];
            }
            else {
                checksum_cal_ ^= global_recv_buffer_[pos];
            }

            packageBuffer[PACKAGE_PAID_BYTES + recvPos] = global_recv_buffer_[pos];
            recvPos++;
        }

        if (package_sample_num_ * package_sample_bytes == recvPos) {
            ans = RESULT_OK;
            break;
        }
    }

    if (package_sample_num_ * package_sample_bytes != recvPos) {
        return RESULT_FAIL;
    }

    return ans;
}

result_t YDlidarDriver::waitPackage(node_info_t* node, uint32_t timeout) {
    node->index = 255;
    node->scan_frequency = 0;
    node->error_package = 0;
    node->debug_info = 0xff;

    if (package_sample_index_ == 0) {
        uint8_t* packageBuffer = (uint8_t*)&package_.package_head;
        result_t ans = parseResponseHeader(packageBuffer, timeout);
        if (!IS_OK(ans)) {
            return ans;
        }

        ans = parseResponseScanData(packageBuffer, timeout);
        if (!IS_OK(ans)) {
            return ans;
        }

        calculateCheckSum(node);
        calculatePackageCT();
    }

    parseNodeDebugFromBuffer(node);
    parseNodeFromBuffer(node);
    return RESULT_OK;
}

void YDlidarDriver::calculateCheckSum(node_info_t* node) {
    checksum_cal_ ^= sample_num_and_ct_cal_;
    checksum_cal_ ^= last_sample_angle_cal_;

    if (checksum_cal_ != check_sum_) {
        checksum_result_ = false;
        has_package_error = true;
        node->error_package = 1;
    }
    else {
        checksum_result_ = true;
    }
}

void YDlidarDriver::calculatePackageCT() {
    package_ct_ = package_.package_ct;
    now_package_num = package_.now_package_num;
}

void YDlidarDriver::parseNodeDebugFromBuffer(node_info_t* node) {
    if ((package_ct_ & 0x01) == CT_Normal) {
        node->sync_flag = NODE_NOT_SYNC;
        node->debug_info = 0xff;

        if (!has_package_error) {
            if (package_sample_index_ == 0) {
                package_index++;
                node->debug_info = (package_ct_ >> 1);
                node->index = package_index;
            }
        }
        else {
            node->error_package = 1;
            node->index = 255;
            package_index = 0xff;
        }
    }
    else {
        node->sync_flag = NODE_SYNC;
        package_index = 0;

        if (checksum_result_) {
            has_package_error = false;
            node->index = package_index;
            node->debug_info = (package_ct_ >> 1);
            node->scan_frequency = scan_frequency_;
        }
    }
}

void YDlidarDriver::parseNodeFromBuffer(node_info_t* node) {
    int32_t AngleCorrectForDistance = 0;
    node->sync_quality = NODE_DEFAULT_QUALITY;
    node->delay_time = 0;
    node->stamp = stamp_ ? stamp_ : getCurrentTime();
    node->scan_frequency = scan_frequency_;
    node->is = 0;

    if (checksum_result_) {
        node->sync_quality = ((uint16_t)((package_.package_sample[package_sample_index_].PackageSampleDistance & 0x03) <<
            LIDAR_RESP_MEASUREMENT_ANGLE_SAMPLE_SHIFT) |
            (package_.package_sample[package_sample_index_].PackageSampleQuality));

        node->distance_q2 =
            package_.package_sample[package_sample_index_].PackageSampleDistance & 0xfffc;
        node->is = package_.package_sample[package_sample_index_].PackageSampleDistance & 0x0003;

        if (node->distance_q2 != 0) {
            AngleCorrectForDistance = (int32_t)(((atan(((21.8 * (155.3 - (node->distance_q2 / 4.0))) / 155.3) / (node->distance_q2 / 4.0))) * 180.0 / 3.1415) * 64.0);
            invalid_node_count_++;
        }
        else {
            AngleCorrectForDistance = 0;
        }

        float sampleAngle = interval_sample_angle_ * package_sample_index_;

        if ((first_sample_angle_ + sampleAngle +
            AngleCorrectForDistance) < 0) {
            node->angle_q6_checkbit = (((uint16_t)(first_sample_angle_ + sampleAngle +
                AngleCorrectForDistance + 23040)) << LIDAR_RESP_MEASUREMENT_ANGLE_SHIFT) +
                LIDAR_RESP_MEASUREMENT_CHECKBIT;
        }
        else {
            if ((first_sample_angle_ + sampleAngle + AngleCorrectForDistance) > 23040) {
                node->angle_q6_checkbit = (((uint16_t)(first_sample_angle_ + sampleAngle +
                    AngleCorrectForDistance - 23040)) << LIDAR_RESP_MEASUREMENT_ANGLE_SHIFT) +
                    LIDAR_RESP_MEASUREMENT_CHECKBIT;
            }
            else {
                node->angle_q6_checkbit = (((uint16_t)(first_sample_angle_ + sampleAngle +
                    AngleCorrectForDistance)) << LIDAR_RESP_MEASUREMENT_ANGLE_SHIFT) +
                    LIDAR_RESP_MEASUREMENT_CHECKBIT;
            }
        }
    }
    else {
        node->sync_flag = NODE_NOT_SYNC;
        node->sync_quality = NODE_DEFAULT_QUALITY;
        node->angle_q6_checkbit = LIDAR_RESP_MEASUREMENT_CHECKBIT;
        node->distance_q2 = 0;
        node->scan_frequency = 0;
    }

    package_sample_index_++;

    if (package_sample_index_ >= now_package_num) {
        package_sample_index_ = 0;
        checksum_result_ = false;
    }
}

result_t YDlidarDriver::waitScanData(
    node_info_t* nodebuffer,
    size_t& count,
    uint32_t timeout) {
    if (!is_connected_) {
        count = 0;
        return RESULT_FAIL;
    }

    size_t     recvNodeCount = 0;
    uint32_t   startTs = getHDTimer();
    uint32_t   waitTime = 0;
    result_t   ans = RESULT_FAIL;

    while ((waitTime = getHDTimer() - startTs) <= timeout &&
        recvNodeCount < count) {
        node_info_t node;
        ans = waitPackage(&node, timeout - waitTime);

        if (!IS_OK(ans)) {
            count = recvNodeCount;
            return ans;
        }

        nodebuffer[recvNodeCount++] = node;

        if (node.sync_flag & LIDAR_RESP_MEASUREMENT_SYNCBIT) {
            size_t size = serial_->GetNumberOfBytesAvailable();
            uint64_t delayTime = 0;
            if (size > PACKAGE_PAID_BYTES) {
                size_t packageNum = 0;
                size_t Number = 0;
                size_t PackageSize = TRIANGLE_PACKAGE_DATA_SIZE;
                packageNum = size / PackageSize;
                Number = size % PackageSize;
                delayTime = packageNum * (PackageSize - PACKAGE_PAID_BYTES) * point_time_ / 2;

                if (Number > PACKAGE_PAID_BYTES) {
                    delayTime += point_time_ * ((Number - PACKAGE_PAID_BYTES) / 2);
                }
            }
            nodebuffer[recvNodeCount - 1].delay_time = delayTime;

            count = recvNodeCount;
            CheckLaserStatus();
            return RESULT_OK;
        }

        if (recvNodeCount == count) {
            return RESULT_OK;
        }
    }

    count = recvNodeCount;
    return RESULT_FAIL;
}

result_t YDlidarDriver::grabScanData(node_info_t* nodebuffer, size_t& count,
    uint32_t timeout) {
    switch (data_event_.wait(timeout)) {
    case Event::EVENT_TIMEOUT:
        count = 0;
        return RESULT_TIMEOUT;

    case Event::EVENT_OK:
    {
        if (scan_node_count_ == 0) {
            return RESULT_FAIL;
        }

        ScopedLocker l(lock_);
        size_t size_to_copy = min(count, scan_node_count_);
        memcpy(nodebuffer, scan_node_buf_, size_to_copy * sizeof(node_info_t));
        count = size_to_copy;
        scan_node_count_ = 0;
    }
    return RESULT_OK;

    default:
        count = 0;
        return RESULT_FAIL;
    }

}

result_t YDlidarDriver::getHealth(device_health_t& health, uint32_t timeout) {
    result_t ans;

    if (!is_connected_) {
        return RESULT_FAIL;
    }

    disableDataGrabbing();
    flushSerial();
    {
        ScopedLocker l(lock_);

        if ((ans = sendCommand(LIDAR_CMD_GET_DEVICE_HEALTH)) != RESULT_OK) {
            return ans;
        }

        lidar_ans_header_t response_header;

        if ((ans = waitResponseHeader(&response_header, timeout)) != RESULT_OK) {
            return ans;
        }

        if (response_header.type != LIDAR_ANS_TYPE_DEV_HEALTH) {
            return RESULT_FAIL;
        }

        if (response_header.size < sizeof(device_health_t)) {
            return RESULT_FAIL;
        }

        if (waitForData(response_header.size, timeout) != RESULT_OK) {
            return RESULT_FAIL;
        }

        getData(reinterpret_cast<uint8_t*>(&health), sizeof(health));
    }
    return RESULT_OK;
}

result_t YDlidarDriver::getDeviceInfo(device_info_t& info, uint32_t timeout) {
    result_t  ans;

    if (!is_connected_) {
        return RESULT_FAIL;
    }

    flushSerial();
    {
        ScopedLocker l(lock_);

        if ((ans = sendCommand(LIDAR_CMD_GET_DEVICE_INFO)) != RESULT_OK) {
            return ans;
        }

        lidar_ans_header_t response_header;

        if ((ans = waitResponseHeader(&response_header, timeout)) != RESULT_OK) {
            return ans;
        }

        if (response_header.type != LIDAR_ANS_TYPE_DEVINFO) {
            return RESULT_FAIL;
        }

        if (response_header.size < sizeof(device_info_t)) {
            return RESULT_FAIL;
        }

        if (waitForData(response_header.size, timeout) != RESULT_OK) {
            return RESULT_FAIL;
        }

        getData(reinterpret_cast<uint8_t*>(&info), sizeof(info));
    }

    return RESULT_OK;
}

result_t YDlidarDriver::startScan(bool force, uint32_t timeout) {
    result_t ans;

    if (!is_connected_) {
        return RESULT_FAIL;
    }

    if (is_scanning_) {
        return RESULT_OK;
    }

    stop();
    flushSerial();
    std::this_thread::sleep_for(std::chrono::milliseconds(30));
    {
        ScopedLocker l(lock_);

        if ((ans = sendCommand(force ? LIDAR_CMD_FORCE_SCAN : LIDAR_CMD_SCAN)) !=
            RESULT_OK) {
            return ans;
        }

        lidar_ans_header_t response_header;

        if ((ans = waitResponseHeader(&response_header, timeout)) != RESULT_OK) {
            return ans;
        }
        if (response_header.type != LIDAR_ANS_TYPE_MEASUREMENT) {
            return RESULT_FAIL;
        }

        if (response_header.size < 5) {
            return RESULT_FAIL;
        }

        ans = createThread();
    }

    startMotor();

    return ans;
}

result_t YDlidarDriver::stopScan(uint32_t timeout) {
    if (!is_connected_) {
        return RESULT_FAIL;
    }

    ScopedLocker l(lock_);
    sendCommand(LIDAR_CMD_FORCE_STOP);
    std::this_thread::sleep_for(std::chrono::milliseconds(5));
    sendCommand(LIDAR_CMD_STOP);
    std::this_thread::sleep_for(std::chrono::milliseconds(5));
    return RESULT_OK;
}

result_t YDlidarDriver::createThread() {
    thread_ = CLASS_THREAD(YDlidarDriver, cacheScanData);

    if (thread_.getHandle() == 0) {
        is_scanning_ = false;
        return RESULT_FAIL;
    }

    is_scanning_ = true;
    return RESULT_OK;
}


result_t YDlidarDriver::startAutoScan(bool force, uint32_t timeout) {
    result_t ans;

    if (!is_connected_) {
        return RESULT_FAIL;
    }

    flushSerial();
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    {

        ScopedLocker l(lock_);

        if ((ans = sendCommand(force ? LIDAR_CMD_FORCE_SCAN : LIDAR_CMD_SCAN)) !=
            RESULT_OK) {
            return ans;
        }

        lidar_ans_header_t response_header;

        if ((ans = waitResponseHeader(&response_header, timeout)) != RESULT_OK) {
            return ans;
        }

        if (response_header.type != LIDAR_ANS_TYPE_MEASUREMENT) {
            return RESULT_FAIL;
        }

        if (response_header.size < 5) {
            return RESULT_FAIL;
        }

    }

    startMotor();

    return RESULT_OK;
}

result_t YDlidarDriver::stop() {
    disableDataGrabbing();
    stopScan();
    stopMotor();

    return RESULT_OK;
}

result_t YDlidarDriver::startMotor() {
    ScopedLocker l(lock_);

    setDTR();
    std::this_thread::sleep_for(std::chrono::milliseconds(500));

    return RESULT_OK;
}

result_t YDlidarDriver::stopMotor() {
    ScopedLocker l(lock_);

    clearDTR();
    std::this_thread::sleep_for(std::chrono::milliseconds(500));

    return RESULT_OK;
}

result_t YDlidarDriver::getScanFrequency(scan_frequency_t& frequency,
    uint32_t timeout) {
    result_t  ans;

    if (!is_connected_) {
        return RESULT_FAIL;
    }

    disableDataGrabbing();
    flushSerial();
    {
        ScopedLocker l(lock_);

        if ((ans = sendCommand(LIDAR_CMD_GET_AIM_SPEED)) != RESULT_OK) {
            return ans;
        }

        lidar_ans_header_t response_header;

        if ((ans = waitResponseHeader(&response_header, timeout)) != RESULT_OK) {
            return ans;
        }

        if (response_header.type != LIDAR_ANS_TYPE_DEVINFO) {
            return RESULT_FAIL;
        }

        if (response_header.size != sizeof(frequency)) {
            return RESULT_FAIL;
        }

        if (waitForData(response_header.size, timeout) != RESULT_OK) {
            return RESULT_FAIL;
        }

        getData(reinterpret_cast<uint8_t*>(&frequency), sizeof(frequency));
    }
    return RESULT_OK;
}

result_t YDlidarDriver::setScanFrequencyAdd(scan_frequency_t& frequency,
    uint32_t timeout) {
    result_t  ans;

    if (!is_connected_) {
        return RESULT_FAIL;
    }

    disableDataGrabbing();
    flushSerial();
    {
        ScopedLocker l(lock_);

        if ((ans = sendCommand(LIDAR_CMD_SET_AIM_SPEED_ADD)) != RESULT_OK) {
            return ans;
        }

        lidar_ans_header_t response_header;

        if ((ans = waitResponseHeader(&response_header, timeout)) != RESULT_OK) {
            return ans;
        }

        if (response_header.type != LIDAR_ANS_TYPE_DEVINFO) {
            return RESULT_FAIL;
        }

        if (response_header.size != sizeof(frequency)) {
            return RESULT_FAIL;
        }

        if (waitForData(response_header.size, timeout) != RESULT_OK) {
            return RESULT_FAIL;
        }

        getData(reinterpret_cast<uint8_t*>(&frequency), sizeof(frequency));
    }
    return RESULT_OK;
}

result_t YDlidarDriver::setScanFrequencyDis(scan_frequency_t& frequency,
    uint32_t timeout) {
    result_t  ans;

    if (!is_connected_) {
        return RESULT_FAIL;
    }

    disableDataGrabbing();
    flushSerial();
    {
        ScopedLocker l(lock_);

        if ((ans = sendCommand(LIDAR_CMD_SET_AIM_SPEED_DIS)) != RESULT_OK) {
            return ans;
        }

        lidar_ans_header_t response_header;

        if ((ans = waitResponseHeader(&response_header, timeout)) != RESULT_OK) {
            return ans;
        }

        if (response_header.type != LIDAR_ANS_TYPE_DEVINFO) {
            return RESULT_FAIL;
        }

        if (response_header.size != sizeof(frequency)) {
            return RESULT_FAIL;
        }

        if (waitForData(response_header.size, timeout) != RESULT_OK) {
            return RESULT_FAIL;
        }

        getData(reinterpret_cast<uint8_t*>(&frequency), sizeof(frequency));
    }
    return RESULT_OK;
}

result_t YDlidarDriver::setScanFrequencyAddMic(scan_frequency_t& frequency,
    uint32_t timeout) {
    result_t  ans;

    if (!is_connected_) {
        return RESULT_FAIL;
    }

    disableDataGrabbing();
    flushSerial();
    {
        ScopedLocker l(lock_);

        if ((ans = sendCommand(LIDAR_CMD_SET_AIM_SPEED_ADD_MIC)) != RESULT_OK) {
            return ans;
        }

        lidar_ans_header_t response_header;

        if ((ans = waitResponseHeader(&response_header, timeout)) != RESULT_OK) {
            return ans;
        }

        if (response_header.type != LIDAR_ANS_TYPE_DEVINFO) {
            return RESULT_FAIL;
        }

        if (response_header.size != sizeof(frequency)) {
            return RESULT_FAIL;
        }

        if (waitForData(response_header.size, timeout) != RESULT_OK) {
            return RESULT_FAIL;
        }

        getData(reinterpret_cast<uint8_t*>(&frequency), sizeof(frequency));
    }
    return RESULT_OK;
}

result_t YDlidarDriver::setScanFrequencyDisMic(scan_frequency_t& frequency,
    uint32_t timeout) {
    result_t  ans;

    if (!is_connected_) {
        return RESULT_FAIL;
    }

    disableDataGrabbing();
    flushSerial();
    {
        ScopedLocker l(lock_);

        if ((ans = sendCommand(LIDAR_CMD_SET_AIM_SPEED_DIS_MIC)) != RESULT_OK) {
            return ans;
        }

        lidar_ans_header_t response_header;

        if ((ans = waitResponseHeader(&response_header, timeout)) != RESULT_OK) {
            return ans;
        }

        if (response_header.type != LIDAR_ANS_TYPE_DEVINFO) {
            return RESULT_FAIL;
        }

        if (response_header.size != sizeof(frequency)) {
            return RESULT_FAIL;
        }

        if (waitForData(response_header.size, timeout) != RESULT_OK) {
            return RESULT_FAIL;
        }

        getData(reinterpret_cast<uint8_t*>(&frequency), sizeof(frequency));
    }
    return RESULT_OK;
}

result_t YDlidarDriver::setSamplingRate(sampling_rate_t& rate, uint32_t timeout) {
    result_t  ans;

    if (!is_connected_) {
        return RESULT_FAIL;
    }

    disableDataGrabbing();
    flushSerial();
    {
        ScopedLocker l(lock_);

        if ((ans = sendCommand(LIDAR_CMD_SET_SAMPLING_RATE)) != RESULT_OK) {
            return ans;
        }

        lidar_ans_header_t response_header;

        if ((ans = waitResponseHeader(&response_header, timeout)) != RESULT_OK) {
            return ans;
        }

        if (response_header.type != LIDAR_ANS_TYPE_DEVINFO) {
            return RESULT_FAIL;
        }

        if (response_header.size != sizeof(rate)) {
            return RESULT_FAIL;
        }

        if (waitForData(response_header.size, timeout) != RESULT_OK) {
            return RESULT_FAIL;
        }

        getData(reinterpret_cast<uint8_t*>(&rate), sizeof(rate));
    }
    return RESULT_OK;
}

} // namespace ydlidar

