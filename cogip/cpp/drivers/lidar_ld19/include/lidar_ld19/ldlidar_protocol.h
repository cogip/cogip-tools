#pragma once

#include <cstdint>

namespace ldlidar {

#define PKG_HEADER 0x54
#define DATA_PKG_INFO 0x2C
#define POINT_PER_PACK 12
#define HEALTH_PKG_INFO 0xE0
#define MANUFACT_PKG_INF 0x0F

#define GET_PKG_PCD 1
#define GET_PKG_HEALTH 2
#define GET_PKG_MANUFACT 3
#define GET_PKG_ERROR 0

typedef struct __attribute__((packed)) {
    uint8_t header;
    uint8_t information;
    uint16_t speed;
    uint16_t product_version;
    uint32_t sn_high;
    uint32_t sn_low;
    uint32_t hardware_version;
    uint32_t firmware_version;
    uint8_t crc8;
} LiDARManufactureInfoType;

typedef struct __attribute__((packed)) {
    uint16_t distance;
    uint8_t intensity;
} LidarPointStructType;

typedef struct __attribute__((packed)) {
    uint8_t header;
    uint8_t ver_len;
    uint16_t speed;
    uint16_t start_angle;
    LidarPointStructType point[POINT_PER_PACK];
    uint16_t end_angle;
    uint16_t timestamp;
    uint8_t crc8;
} LiDARMeasureDataType;

typedef struct __attribute__((packed)) {
    uint8_t header;
    uint8_t information;
    uint8_t error_code;
    uint8_t crc8;
} LiDARHealthInfoType;

class LdLidarProtocol {
public:
    /// Constructor.
    LdLidarProtocol();

    /// Destructor
    ~LdLidarProtocol();

    /// Analyzes a single byte of data to identify and process LiDAR data packets.
    /// @param byte Input byte from the serial data stream.
    /// @return One of the following status codes:
    /// - `GET_PKG_PCD`: Point cloud data packet received successfully.
    /// - `GET_PKG_HEALTH`: Health information packet received successfully.
    /// - `GET_PKG_MANUFACT`: Manufacturing information packet received successfully.
    uint8_t analyzeDataPacket(uint8_t byte);

    /// Retrieves the latest point cloud data packet.
    /// @return A reference to the point cloud data structure.
    LiDARMeasureDataType &getPCDPacketData(void);

private:
    LiDARMeasureDataType pcdpkg_data_;
    LiDARHealthInfoType healthpkg_data_;
    LiDARManufactureInfoType manufacinfpkg_data_;
};

uint8_t calCRC8(const uint8_t *data, uint16_t data_len);

} // namespace ldlidar
