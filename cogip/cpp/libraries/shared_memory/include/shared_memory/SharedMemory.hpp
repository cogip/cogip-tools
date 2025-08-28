// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "shared_memory/shared_data.hpp"
#include "shared_memory/WritePriorityLock.hpp"

#include "models/CircleList.hpp"
#include "models/PoseBuffer.hpp"
#include "models/PoseOrderList.hpp"
#include "obstacles/ObstacleCircleList.hpp"
#include "obstacles/ObstacleRectangleList.hpp"

#include <memory>
#include <string>

namespace cogip {

namespace shared_memory {

/// @class SharedMemory
/// Manages shared memory and associated locks for inter-process communication.
///
/// Provides mechanisms to access and manage shared memory segments and write-priority locks,
/// enabling safe concurrent access between processes.
class SharedMemory {
public:
    /// Constructs a SharedMemory instance.
    /// @param name Unique name of the shared memory segment.
    /// @param owner Whether this instance is the owner of the shared memory.
    SharedMemory(const std::string& name, bool owner = false);

    /// Cleans up shared memory and associated resources.
    ~SharedMemory();

    /// Copying is disallowed to maintain unique ownership of shared memory.
    SharedMemory(const SharedMemory&) = delete;             ///< Deleted copy constructor.
    SharedMemory& operator=(const SharedMemory&) = delete;  ///< Deleted copy assignment.

    /// Moving is allowed to transfer ownership of shared memory.
    SharedMemory(SharedMemory&&) = default;                 ///< Defaulted move constructor.
    SharedMemory& operator=(SharedMemory&&) = default;      ///< Defaulted move assignment.

    /// Retrieves a write-priority lock for the specified lock name.
    /// @param lock Name of the lock to retrieve.
    /// @returns Reference to the `WritePriorityLock` associated with the specified name.
    WritePriorityLock& getLock(LockName lock);

    /// Retrieves a pointer to the shared memory data structure.
    shared_data_t* getData() { return data_; }

    /// Retrieves a pointer to the PoseBuffer object wrapping the shared memory pose_current_buffer structure.
    models::PoseBuffer* getPoseCurrentBuffer() { return pose_current_buffer_; }


    /// Retrieves a pointer to the Coords object wrapping the shared memory table_limits array.
    double (&getTableLimits())[4] { return data_->table_limits; }

    /// Retrieves a pointer to the shared memory lidar_data structure.
    double (&getLidarData())[MAX_LIDAR_DATA_COUNT][3] { return data_->lidar_data; }

    /// Retrieves a pointer to the shared memory lidar_coords structure.
    double (&getLidarCoords())[MAX_LIDAR_DATA_COUNT][2] { return data_->lidar_coords; }

    /// Retrieves a pointer to the shared memory detector_obstacles structure.
    models::CircleList* getDetectorObstacles() { return detector_obstacles_; }

    /// Retrieves a pointer to the shared memory monitor_obstacles structure.
    models::CircleList* getMonitorObstacles() { return monitor_obstacles_; }

    /// Retrieves a pointer to the shared memory circle_obstacles structure.
    obstacles::ObstacleCircleList* getCircleObstacles() { return circle_obstacles_; }

    /// Retrieves a pointer to the shared memory rectangle_obstacles structure.
    obstacles::ObstacleRectangleList* getRectangleObstacles() { return rectangle_obstacles_; }

    /// Retrieves a reference to the shared properties structure.
    shared_properties_t& getProperties() { return data_->properties; }

    /// Gets the avoidance exiting flag
    bool getAvoidanceExiting() const { return data_->avoidance_exiting; }

    /// Sets the avoidance exiting flag.
    void setAvoidanceExiting(bool exiting) { data_->avoidance_exiting = exiting; }

    /// Gets the avoidance new pose order available flag.
    bool getAvoidanceHasNewPoseOrder() const { return data_->avoidance_has_new_pose_order; }

    /// Sets the avoidance new pose order available flag.
    void setAvoidanceHasNewPoseOrder(bool available) { data_->avoidance_has_new_pose_order = available; }

    /// Gets the avoidance no pose order flag.
    bool getAvoidanceHasPoseOrder() const { return data_->avoidance_has_pose_order; }

    /// Sets the avoidance no pose order flag.
    void setAvoidanceHasPoseOrder(bool no_pose_order) { data_->avoidance_has_pose_order = no_pose_order; }

    /// Retrieves a pointer to the shared memory avoidance_new_pose_order structure.
    models::PoseOrder* getAvoidanceNewPoseOrder() { return avoidance_new_pose_order_; }

    /// Retrieves a pointer to the shared memory avoidance_pose_order structure.
    models::PoseOrder* getAvoidancePoseOrder() { return avoidance_pose_order_; }

    /// Retrieves a pointer to the shared memory avoidance_path structure.
    models::PoseOrderList* getAvoidancePath() { return avoidance_path_; }

private:
    std::string name_;     ///< Unique name of the shared memory segment.
    bool owner_;           ///< Indicates whether this instance owns the shared memory.
    int shm_fd_;           ///< File descriptor for the shared memory.
    shared_data_t* data_;  ///< Pointer to the shared memory data structure.
    std::map<LockName, std::shared_ptr<WritePriorityLock>> locks_;  ///< Map of locks for synchronization.
    models::PoseBuffer* pose_current_buffer_;  ///< Pointer to the PoseBuffer object wrapping the shared memory pose_current_buffer structure.
    models::CircleList* detector_obstacles_;  ///< Pointer to the CircleList object wrapping the shared memory detector_obstacles structure.
    models::CircleList* monitor_obstacles_;  ///< Pointer to the CircleList object wrapping the shared memory monitor_obstacles structure.
    obstacles::ObstacleCircleList* circle_obstacles_;  ///< Pointer to the ObstacleCircleList object wrapping the shared memory circle_obstacles structure.
    obstacles::ObstacleRectangleList* rectangle_obstacles_;  ///< Pointer to the ObstacleRectangleList object wrapping the shared memory rectangle_obstacles structure.
    models::PoseOrder* avoidance_new_pose_order_;  ///< Pointer to the PoseOrder object for the new pose order in avoidance.
    models::PoseOrder* avoidance_pose_order_;  ///< Pointer to the PoseOrder object for the current pose order in avoidance.
    models::PoseOrderList* avoidance_path_;  ///< Pointer to the PoseOrderList object for the avoidance path.
};

} // namespace shared_memory

} // namespace cogip
