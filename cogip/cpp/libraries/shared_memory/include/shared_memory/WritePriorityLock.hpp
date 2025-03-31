// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include <semaphore.h>
#include <string>

namespace cogip {

namespace shared_memory {

/// @class WritePriorityLock
/// Manages a write-priority locking mechanism for shared resources.
///
/// This class provides synchronization primitives to manage concurrent access to shared resources,
/// ensuring that writers have priority over readers when required.
class WritePriorityLock {
public:
    /// Constructs a WritePriorityLock instance.
    /// @param name Unique name used for associated semaphores and shared memory.
    /// @param owner Whether this instance owns and initializes the resources.
    explicit WritePriorityLock(const std::string& name, bool owner = false);

    /// Cleans up semaphores and shared memory resources.
    ~WritePriorityLock();

    /// Acquires a read lock, allowing multiple readers concurrently.
    void startReading();

    /// Releases the read lock, decrementing the reader count.
    void finishReading();

    /// Acquires a write lock, blocking all readers and writers.
    void startWriting();

    /// Releases the write lock, allowing other readers or writers to proceed.
    void finishWriting();

    /// Register the the lock will be used to wait the update signal to read updated data.
    void registerConsumer();

    /// Signal to registered consumers that data was updated.
    void postUpdate();

    /// Wait for the updated signal meaning that data was updated.
    void waitUpdate();

    /// Reset counters and semaphores.
    void reset();


private:
    bool owner_;                    ///< Indicates whether this instance owns the resources.
    bool registered_consumer_;      ///< Indicates if the lock is registered as a consumer.
    std::string name_;              ///< Base name used for semaphore and shared memory naming.
    std::string mutex_name_;        ///< Name of the mutex semaphore.
    std::string write_lock_name_;   ///< Name of the write lock semaphore.
    std::string update_name_;       ///< Name of the update semaphore.
    std::string registration_name_; ///< Name of the consumer registration semaphore.
    std::string reader_count_shm_name_;  ///< Name of the shared memory for reader count.
    std::string write_request_shm_name_; ///< Name of the shared memory for write request count.
    std::string consumer_count_shm_name_; ///< Name of the shared memory for consumer count.
    sem_t* sem_mutex_;              ///< Semaphore for synchronizing access to shared memory.
    sem_t* sem_write_lock_;         ///< Semaphore for ensuring write access priority.
    sem_t* sem_update_;             ///< Semaphore for signaling updated data.
    sem_t* sem_register_;           ///< Semaphore for consumer registration.
    int reader_shm_fd_;             ///< File descriptor for shared memory of reader count.
    int write_request_shm_fd_;      ///< File descriptor for shared memory of write request count.
    int consumer_count_shm_fd_;     ///< File descriptor for shared memory of consumer count.
    int* reader_count_;             ///< Shared memory pointer for reader count.
    int* write_request_count_;      ///< Shared memory pointer for writer request count.
    int* consumer_count_;           ///< Shared memory pointer for consumer count.
};

} // namespace shared_memory

} // namespace cogip
