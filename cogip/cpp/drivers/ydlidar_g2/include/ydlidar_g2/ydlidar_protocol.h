#pragma once

#include <cstdint>

/// Count the number of elements in a statically allocated array.
#if !defined(_countof)
#define _countof(_Array) (int)(sizeof(_Array) / sizeof(_Array[0]))
#endif

/**
 * @name PI constant
 * @{
 */
#ifndef M_PI
#define M_PI 3.1415926
#endif
 /** @} */

/**@name LIDAR CMD Protocol
 * @brief LiDAR request and response CMD
 * @{
 */
#define LIDAR_CMD_STOP                      0x65
#define LIDAR_CMD_SCAN                      0x60
#define LIDAR_CMD_FORCE_SCAN                0x61
#define LIDAR_CMD_RESET                     0x80
#define LIDAR_CMD_FORCE_STOP                0x00
#define LIDAR_CMD_GET_DEVICE_INFO           0x90
#define LIDAR_CMD_GET_DEVICE_HEALTH         0x92
#define LIDAR_ANS_TYPE_DEVINFO              0x4
#define LIDAR_ANS_TYPE_DEV_HEALTH           0x6
#define LIDAR_CMD_SYNC_BYTE                 0xA5
#define LIDAR_CMDFLAG_HAS_PAYLOAD           0x80
#define LIDAR_ANS_SYNC_BYTE1                0xA5
#define LIDAR_ANS_SYNC_BYTE2                0x5A
#define LIDAR_ANS_TYPE_MEASUREMENT          0x81
#define LIDAR_RESP_MEASUREMENT_SYNCBIT      (0x1<<0)
#define LIDAR_RESP_MEASUREMENT_CHECKBIT     (0x1<<0)
#define LIDAR_RESP_MEASUREMENT_ANGLE_SHIFT  1
#define LIDAR_RESP_MEASUREMENT_ANGLE_SAMPLE_SHIFT 8

#define LIDAR_CMD_SET_AIM_SPEED_ADD_MIC    0x09
#define LIDAR_CMD_SET_AIM_SPEED_DIS_MIC    0x0A
#define LIDAR_CMD_SET_AIM_SPEED_ADD        0x0B
#define LIDAR_CMD_SET_AIM_SPEED_DIS        0x0C
#define LIDAR_CMD_GET_AIM_SPEED            0x0D
#define LIDAR_CMD_SET_SAMPLING_RATE        0xD0
#define LIDAR_CMD_GET_SAMPLING_RATE        0xD1
#define LIDAR_CMD_GET_OFFSET_ANGLE         0x93
/** @} LIDAR CMD Protocol */

/// Maximum number of samples in a packet
#define PACKAGE_SAMPLE_MAX_LENGTH 0x100

/// CT Package Type
typedef enum {
    CT_Normal = 0,     ///< Normal package
    CT_RingStart = 1,  ///< Starting package
    CT_Tail,
} ct_enum_t;

/// Default Node Quality
#define NODE_DEFAULT_QUALITY (10)
/// Starting Node
#define NODE_SYNC 1
/// Normal Node
#define NODE_NOT_SYNC 2
/// Package Header Size
#define PACKAGE_PAID_BYTES 10
/// Package Header
#define PH 0x55AA
#define PH1 0xAA
#define PH2 0x55
#define PH3 0x66

/// Normal Package size
#define TRIANGLE_PACKAGE_DATA_SIZE 40

typedef struct node_info {
    uint8_t sync_flag;
    uint8_t is;
    uint16_t sync_quality;
    uint16_t angle_q6_checkbit;
    uint16_t distance_q2;
    uint64_t stamp;
    uint32_t delay_time;
    uint8_t scan_frequency;
    uint8_t debug_info;
    uint8_t index;
    uint8_t error_package;
} __attribute__((packed)) node_info_t;

/// package node info
typedef struct PackageNode {
    uint8_t PackageSampleQuality; ///< intensity
    uint16_t PackageSampleDistance; ///< range
} __attribute__((packed)) package_node_t;

/// LiDAR Intensity Nodes Package
typedef struct node_package {
    uint16_t  package_head; ///< package header
    uint8_t   package_ct; ///< package ct
    uint8_t   now_package_num; ///< package number
    uint16_t  package_first_sample_angle; ///< first sample angle
    uint16_t  package_last_sample_angle; ///< last sample angle
    uint16_t  checksum; ///< checksum
    package_node_t  package_sample[PACKAGE_SAMPLE_MAX_LENGTH];
} __attribute__((packed)) node_package_t;

/// LiDAR Normal Nodes package
typedef struct node_packages {
    uint16_t  package_head; ///< package header
    uint8_t   package_ct; ///< package ct
    uint8_t   now_package_num; ///< package number
    uint16_t  package_first_sample_angle; ///< first sample angle
    uint16_t  package_last_sample_angle; ///< last sample angle
    uint16_t  checksum; ///< checksum
    uint16_t  packageSampleDistance[PACKAGE_SAMPLE_MAX_LENGTH];
} __attribute__((packed)) node_packages_t;

typedef struct stamp_package {
    uint8_t flag1;
    uint8_t flag2;
    uint8_t cs;
    uint32_t stamp;
    uint8_t reserved;
} __attribute__((packed)) stamp_package_t;
#define SIZE_STAMP_PACKAGE sizeof(stamp_package)

/// LiDAR Device Information
typedef struct device_info {
    uint8_t   model; ///< LiDAR model
    uint16_t  firmware_version; ///< firmware version
    uint8_t   hardware_version; ///< hardare version
    uint8_t   serialnum[16]; ///< serial number
} __attribute__((packed)) device_info_t;

/// LiDAR Health Information
typedef struct device_health_t {
    uint8_t   status; ///< health state
    uint16_t  error_code; ///< error code
} __attribute__((packed)) device_health_t;

/// LiDAR sampling Rate struct
typedef struct sampling_rate {
    uint8_t rate; ///< sample rate
} __attribute__((packed)) sampling_rate_t;

/// LiDAR scan frequency struct
typedef struct scan_frequency {
    uint32_t frequency;	///< scan frequency
} __attribute__((packed)) scan_frequency_t;

/// LiDAR Zero Offset Angle
typedef struct offset_angle {
    int32_t angle;
} __attribute__((packed)) offset_angle_t;

/// LiDAR request command packet
typedef struct cmd_packet {
    uint8_t syncByte;
    uint8_t cmd_flag;
    uint8_t size;
    uint8_t data;
} __attribute__((packed)) cmd_packet_t;

/// LiDAR response Header
typedef struct lidar_ans_header {
    uint8_t  syncByte1;
    uint8_t  syncByte2;
    uint32_t size : 30;
    uint32_t subType : 2;
    uint8_t  type;
} __attribute__((packed)) lidar_ans_header_t;
