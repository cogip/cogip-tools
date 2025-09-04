// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_utils
/// @{
/// @file
/// @brief       LidarDataConverter class declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "shared_memory/SharedMemory.hpp"
#include <thread>

namespace cogip {

namespace utils {

class LidarDataConverter {
public:
    LidarDataConverter(const std::string& name);
    ~LidarDataConverter();

    /// Start converting lidar data to table coordinates.
    void start();

    /// Stop converting lidar data to table coordinates.
    void stop();

    /// Convert lidar data to table coordinates.
    void convert();

    /// Set current pose index.
    void setPoseCurrentIndex(std::size_t index) {
        pose_current_index_ = index;
    }

    /// Set the table limits margin.
    void setTableLimitsMargin(double table_limits_margin) {
        table_limits_margin_ = table_limits_margin;
    }

    /// Set the lidar offset on X axis.
    void setLidarOffsetX(double lidar_offset_x) {
        lidar_offset_x_ = lidar_offset_x;
    }

    /// Set the lidar offset on Y axis.
    void setLidarOffsetY(double lidar_offset_y) {
        lidar_offset_y_ = lidar_offset_y;
    }

    /// Set the debug mode.
    void setDebug(bool debug) {
        debug_ = debug;
    }

private:
    shared_memory::SharedMemory shared_memory_;                   ///< Shared memory instance
    double (*lidar_data_)[3];                                     ///< Pointer to lidar data memory
    double (*lidar_coords_)[2];                                   ///< Pointer to lidar coords memory
    cogip::shared_memory::WritePriorityLock data_read_lock_;      ///< Lock for reading lidar data
    cogip::shared_memory::WritePriorityLock coords_write_lock_;   ///< Lock for writing lidar coordinates
    models::PoseBuffer* pose_current_buffer_;                     ///< Pointer to the current pose buffer
    std::size_t pose_current_index_;                              ///< Index of the current pose
    double* table_limits_;                                        ///< Pointer to table limits
    double table_limits_margin_;                                  ///< Margin for table limits
    double lidar_offset_x_;                                       ///< Lidar offset on X axis
    double lidar_offset_y_;                                       ///< Lidar offset on Y axis
    bool running_;                                                ///< Flag to indicate if the converter is running
    std::thread thread_;                                          ///< Thread for the converter
    bool debug_;                                                  ///< Flag to enable debug mode
};

} // namespace utils

} // namespace cogip

/// @}
