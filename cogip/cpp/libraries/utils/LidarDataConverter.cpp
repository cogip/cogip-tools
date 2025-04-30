#include "utils/LidarDataConverter.hpp"

#include <iostream>

namespace cogip {

namespace utils {

LidarDataConverter::LidarDataConverter(const std::string& name):
    shared_memory_(shared_memory::SharedMemory(name, false)),
    lidar_data_(shared_memory_.getData()->lidar_data),
    lidar_coords_(shared_memory_.getData()->lidar_coords),
    data_read_lock_(shared_memory_.getLock(shared_memory::LockName::LidarData)),
    coords_write_lock_(shared_memory_.getLock(shared_memory::LockName::LidarCoords)),
    pose_current_buffer_(shared_memory_.getPoseCurrentBuffer()),
    pose_current_index_(0),
    table_limits_(shared_memory_.getTableLimits()),
    table_limits_margin_(0.0f),
    lidar_offset_x_(0.0f),
    lidar_offset_y_(0.0f),
    running_(false),
    debug_(false)
{
    data_read_lock_.registerConsumer();
}

LidarDataConverter::~LidarDataConverter()
{
    stop();
}

void LidarDataConverter::start()
{
    if (debug_) std::cout << "LidarDataConverter: starting..." << std::endl;
    if (running_) {
        return; // Already running
    }

    running_ = true;
    thread_ = std::thread([this]() {
        while (running_) {
            convert(); // Call the convert function
        }
    });
}

void LidarDataConverter::stop()
{
    if (debug_) std::cout << "LidarDataConverter: stopping..." << std::endl;
    if (!running_) {
        return; // Already stopped
    }
    if (debug_) std::cout << "LidarDataConverter: stopping thread..." << std::endl;
    running_ = false;
    if (thread_.joinable()) {
        if (debug_) std::cout << "LidarDataConverter: joining thread..." << std::endl;
        data_read_lock_.postUpdate(); // Notify the thread to stop waiting for data
        thread_.join(); // Wait for the thread to finish
    }
    if (debug_) std::cout << "LidarDataConverter: thread stopped" << std::endl;
}

void LidarDataConverter::convert()
{
    if (debug_) std::cout << "LidarDataConverter: waiting for data..." << std::endl;
    data_read_lock_.waitUpdate();
    if (debug_) std::cout << "LidarDataConverter: data updated" << std::endl;

    // Convert points to global coordinates based on lidar position
    cogip::models::Pose pose_current = pose_current_buffer_->get(pose_current_index_);
    double pose_current_x = pose_current.x();
    double pose_current_y = pose_current.y();
    double pose_current_angle = pose_current.angle();

    std::size_t index = 0;
    std::size_t count = 0;

    if (debug_) std::cout << "LidarDataConverter: locking write lock..." << std::endl;
    coords_write_lock_.startWriting();
    if (debug_) std::cout << "LidarDataConverter: write lock locked" << std::endl;

    // Iterate over the entire Lidar data
    while (true) {
        if (lidar_data_[index][0] < 0) {
            break;
        }
        double angle = lidar_data_[index][0];
        double distance = lidar_data_[index][1];
        double intensity = lidar_data_[index][2];

        // Convert Lidar-relative polar to Cartesian
        double angle_rad = DEG2RAD(angle);
        double lidar_relative_x = distance * std::cos(angle_rad);
        double lidar_relative_y = distance * std::sin(angle_rad);

        // Translate point from lidar-centric to robot-centric coordinates
        double robot_relative_x = lidar_relative_x + lidar_offset_x_;
        double robot_relative_y = lidar_relative_y + lidar_offset_y_;

        // Convert robot angle to radians
        double robot_angle_rad = DEG2RAD(pose_current_angle);

        // Apply rotation based on robot's angle
        double global_x = pose_current_x + (
            robot_relative_x * std::cos(robot_angle_rad) - robot_relative_y * std::sin(robot_angle_rad)
        );
        double global_y = pose_current_y + (
            robot_relative_x * std::sin(robot_angle_rad) + robot_relative_y * std::cos(robot_angle_rad)
        );

        // Filter points near the borders or outside the table
        if ((table_limits_[0] + table_limits_margin_ < global_x &&
            global_x < table_limits_[1] - table_limits_margin_) &&
            (table_limits_[2] + table_limits_margin_ < global_y &&
            global_y < table_limits_[3] - table_limits_margin_)
        ) {
            lidar_coords_[count][0] = global_x;
            lidar_coords_[count][1] = global_y;
            count++;
        }
        index++;
    }
    lidar_coords_[count][0] = -1.0;  // Mark as end of data
    lidar_coords_[count][1] = -1.0;
    lidar_coords_[count][2] = -1.0;

    if (debug_) std::cout << "LidarDataConverter: unlock write lock" << std::endl;
    coords_write_lock_.finishWriting();
    if (debug_) std::cout << "LidarDataConverter: converted " << count << " points to table coordinates." << std::endl;
    coords_write_lock_.postUpdate();
}

} // namespace utils

} // namespace cogip
