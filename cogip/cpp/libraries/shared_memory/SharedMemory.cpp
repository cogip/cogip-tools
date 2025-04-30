// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "shared_memory/SharedMemory.hpp"

#include <cstring>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdexcept>
#include <iostream>

namespace cogip {

namespace shared_memory {

SharedMemory::SharedMemory(const std::string& name, bool owner):
    name_(name),
    owner_(owner),
    shm_fd_(-1),
    data_(nullptr)
{
    int shm_flags = O_RDWR;
    if (owner) {
        shm_flags |= O_CREAT | O_TRUNC;
    }

    umask(0000); // Allow full permissions (rw-rw-rw-)

    shm_fd_ = shm_open(name_.c_str(), shm_flags, 0666);
    if (shm_fd_ < 0) {
        throw std::runtime_error("Failed to create shared memory segment");
    }

    if (owner_) {
        if (ftruncate(shm_fd_, sizeof(shared_data_t)) < 0) {
            throw std::runtime_error("Failed to set size of shared memory segment");
        }
    }

    data_ = static_cast<shared_data_t*>(mmap(nullptr, sizeof(shared_data_t), PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd_, 0));
    if (data_ == MAP_FAILED) {
        throw std::runtime_error("Failed to map shared memory segment");
    }

    if (owner_) {
        std::memset(data_, 0, sizeof(shared_data_t));
        for (std::size_t i{0}; i < MAX_LIDAR_DATA_COUNT; ++i) {
            data_->lidar_data[i][0] = -1;
            data_->lidar_data[i][1] = -1;
            data_->lidar_data[i][2] = -1;
        }
    }

    for (const auto& [lock, name] : lock2str) {
        locks_.emplace(lock, std::make_unique<WritePriorityLock>(name_ + "_" + name, owner_));
    }
    pose_current_buffer_ = new models::PoseBuffer(&data_->pose_current_buffer);
    pose_order_ = new models::Pose(&data_->pose_order);
    detector_obstacles_ = new models::CircleList(&data_->detector_obstacles);
    monitor_obstacles_ = new models::CircleList(&data_->monitor_obstacles);
    circle_obstacles_ = new obstacles::ObstacleCircleList(&data_->circle_obstacles);
    rectangle_obstacles_ = new obstacles::ObstacleRectangleList(&data_->rectangle_obstacles);

    std::cout << "SharedMemory(\"" << name_ << "\", owner=" << owner_ << ", size=" << sizeof(shared_data_t) << ") created." << std::endl;
}

SharedMemory::~SharedMemory() {
    delete rectangle_obstacles_;
    delete circle_obstacles_;
    delete monitor_obstacles_;
    delete detector_obstacles_;
    delete pose_order_;
    delete pose_current_buffer_;

    if (data_ != nullptr) {
        munmap(data_, sizeof(shared_data_t));
    }
    if (shm_fd_ != -1) {
        close(shm_fd_);
    }
    if (owner_) {
        shm_unlink(name_.c_str());
    }
    std::cout << "SharedMemory(\"" << name_ << "\", owner=" << owner_ << ") deleted." << std::endl;
}

#include <iostream>
WritePriorityLock& SharedMemory::getLock(LockName lock) {
    auto it = locks_.find(lock);
    if (it == locks_.end()) {
        throw std::runtime_error("WritePriorityLock for the given LockName not found.");
    }
    return *(it->second);
}

} // namespace shared_memory

} // namespace cogip
