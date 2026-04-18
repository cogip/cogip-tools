// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "shared_memory/WritePriorityLock.hpp"

#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdexcept>
#include <iostream>
#include <time.h>
#include <signal.h>
#include <errno.h>

namespace cogip {

namespace shared_memory {

WritePriorityLock::WritePriorityLock(const std::string& name, bool owner):
    owner_(owner),
    registered_consumer_(false),
    name_(name),
    mutex_name_("/" + name_ + "_mutex"),
    write_lock_name_("/" + name_ + "_write_lock"),
    update_name_("/" + name_ + "_update"),
    registration_name_("/" + name_ + "_registration"),
    reader_count_shm_name_("/" + name_ + "_reader_count"),
    write_request_shm_name_("/" + name_ + "_write_request"),
    consumer_count_shm_name_("/" + name_ + "_consumer_count"),
    sem_mutex_(nullptr),
    sem_write_lock_(nullptr),
    my_update_sem_(nullptr),
    sem_register_(nullptr),
    reader_shm_fd_(-1),
    write_request_shm_fd_(-1),
    consumer_count_shm_fd_(-1),
    reader_count_(nullptr),
    write_request_count_(nullptr),
    consumer_pids_(nullptr),
    debug_(false)
{
    int shm_flags = O_RDWR;
    if (owner) {
        shm_flags |= O_CREAT | O_TRUNC;
    }

    umask(0000); // Allow full permissions (rw-rw-rw-)

    // Open or create the mutex semaphore
    if (owner) {
        sem_mutex_ = sem_open(mutex_name_.c_str(), O_CREAT | O_RDWR | O_TRUNC, 0666, 1);
    }
    else {
        sem_mutex_ = sem_open(mutex_name_.c_str(), O_RDWR);
    }
    if (sem_mutex_ == SEM_FAILED) {
        throw std::runtime_error("Failed to open mutex semaphore");
    }

    // Open or create the write lock semaphore
    if (owner) {
        sem_write_lock_ = sem_open(write_lock_name_.c_str(), O_CREAT | O_RDWR | O_TRUNC, 0666, 1);
    }
    else {
        sem_write_lock_ = sem_open(write_lock_name_.c_str(), O_RDWR);
    }
    if (sem_write_lock_ == SEM_FAILED) {
        throw std::runtime_error("Failed to open write lock semaphore");
    }

    // Open or create the register semaphore
    if (owner) {
        sem_register_ = sem_open(registration_name_.c_str(), O_CREAT | O_RDWR | O_TRUNC, 0666, 1);
    }
    else {
        sem_register_ = sem_open(registration_name_.c_str(), O_RDWR);
    }
    if (sem_register_ == SEM_FAILED) {
        throw std::runtime_error("Failed to open registration semaphore");
    }

    // Shared memory for reader count
    reader_shm_fd_ = shm_open(reader_count_shm_name_.c_str(), shm_flags, 0666);
    if (reader_shm_fd_ < 0) {
        throw std::runtime_error("Failed to open shared memory for reader count");
    }
    if (owner_) {
        if (ftruncate(reader_shm_fd_, sizeof(int)) < 0) {
            throw std::runtime_error("Failed to truncate shared memory for reader count");
        }
    }
    reader_count_ = static_cast<int*>(mmap(NULL, sizeof(int), PROT_READ | PROT_WRITE, MAP_SHARED, reader_shm_fd_, 0));
    if (reader_count_ == MAP_FAILED) {
        throw std::runtime_error("Failed to map shared memory for reader count");
    }

    // Shared memory for write request count
    write_request_shm_fd_ = shm_open(write_request_shm_name_.c_str(), shm_flags, 0666);
    if (write_request_shm_fd_ < 0) {
        throw std::runtime_error("Failed to open shared memory for write request count");
    }
    if (owner_) {
        if (ftruncate(write_request_shm_fd_, sizeof(int)) < 0) {
            throw std::runtime_error("Failed to truncate shared memory for write request count");
        }
    }
    write_request_count_ = static_cast<int*>(mmap(NULL, sizeof(int), PROT_READ | PROT_WRITE, MAP_SHARED, write_request_shm_fd_, 0));
    if (write_request_count_ == MAP_FAILED) {
        throw std::runtime_error("Failed to map shared memory for write request count");
    }
    // Shared memory for consumer count
    consumer_count_shm_fd_ = shm_open(consumer_count_shm_name_.c_str(), shm_flags, 0666);
    if (consumer_count_shm_fd_ < 0) {
        throw std::runtime_error("Failed to open shared memory for consumer count");
    }
    if (owner_) {
        if (ftruncate(consumer_count_shm_fd_, MAX_CONSUMERS * sizeof(pid_t)) < 0) {
            throw std::runtime_error("Failed to truncate shared memory for consumer count");
        }
    }
    consumer_pids_ = static_cast<pid_t*>(mmap(NULL, MAX_CONSUMERS * sizeof(pid_t), PROT_READ | PROT_WRITE, MAP_SHARED, consumer_count_shm_fd_, 0));
    if (consumer_pids_ == MAP_FAILED) {
        throw std::runtime_error("Failed to map shared memory for consumer count");
    }
    if (owner_) {
        reset();
    }

}

WritePriorityLock::~WritePriorityLock() {
    if (registered_consumer_) {
        sem_wait(sem_register_);
        pid_t current_pid = getpid();
        for (int i = 0; i < MAX_CONSUMERS; ++i) {
            if (consumer_pids_[i] == current_pid) {
                consumer_pids_[i] = 0;
                break;
            }
        }
        sem_post(sem_register_);

        if (my_update_sem_ != nullptr) {
            sem_close(my_update_sem_);
            sem_unlink(my_update_sem_name_.c_str());
        }
    }

    // Close cached semaphores
    for (auto& pair : update_sems_cache_) {
        if (pair.second != nullptr) {
            sem_close(pair.second);
        }
    }
    update_sems_cache_.clear();

    if (consumer_pids_ != nullptr) {
        munmap(consumer_pids_, MAX_CONSUMERS * sizeof(pid_t));
    }
    if (write_request_count_ != nullptr) {
        munmap(write_request_count_, sizeof(int));
    }
    if (reader_count_ != nullptr) {
        munmap(reader_count_, sizeof(int));
    }
    if (consumer_count_shm_fd_ != -1) {
        close(consumer_count_shm_fd_);
    }
    if (write_request_shm_fd_ != -1) {
        close(write_request_shm_fd_);
    }
    if (reader_shm_fd_ != -1) {
        close(reader_shm_fd_);
    }
    if (sem_register_ != nullptr) {
        sem_close(sem_register_);
    }
    if (sem_write_lock_ != nullptr) {
        sem_close(sem_write_lock_);
    }
    if (sem_mutex_) {
        sem_close(sem_mutex_);
    }
    if (owner_) {
        sem_unlink(registration_name_.c_str());
        sem_unlink(mutex_name_.c_str());
        sem_unlink(write_lock_name_.c_str());
        shm_unlink(reader_count_shm_name_.c_str());
        shm_unlink(write_request_shm_name_.c_str());
        shm_unlink(consumer_count_shm_name_.c_str());
    }
}

void WritePriorityLock::startReading() {
    if (debug_) std::cout << name_ << " startReading: enter, lock sem_mutex_ (write_request_count_=" << *write_request_count_ << ")" << std::endl;
    sem_wait(sem_mutex_);
    while (*write_request_count_ > 0) {  // Wait if there are pending writers
        sem_post(sem_mutex_);
        usleep(100);  // Small delay to avoid busy waiting
        sem_wait(sem_mutex_);
    }
    (*reader_count_)++;
    if (*reader_count_ == 1) {
        if (debug_) std::cout << name_ << " startReading: lock sem_write_lock_ (reader_count_=" << *reader_count_ << ")" << std::endl;
        sem_wait(sem_write_lock_);  // First reader locks the writer
    }
    if (debug_) std::cout << name_ << " startReading: unlock sem_mutex_" << std::endl;
    sem_post(sem_mutex_);
    if (debug_) std::cout << name_ << " startReading: end" << std::endl;
}

void WritePriorityLock::finishReading() {
    if (debug_) std::cout << name_ << " finishReading: enter (reader_count_=" << *reader_count_ << ")" << std::endl;
    sem_wait(sem_mutex_);
    (*reader_count_)--;
    if (*reader_count_ == 0) {
        if (debug_) std::cout << name_ << " finishReading: unlock sem_write_lock_" << std::endl;
        sem_post(sem_write_lock_);  // Last reader unlocks the writer
    }
    if (debug_) std::cout << name_ << " finishReading: unlock sem_mutex_" << std::endl;
    sem_post(sem_mutex_);
    if (debug_) std::cout << name_ << " finishReading: end" << std::endl;
}

void WritePriorityLock::startWriting() {
    if (debug_) std::cout << name_ << " startWriting: enter, lock sem_mutex_ (write_request_count_=" << *write_request_count_ << ")" << std::endl;
    sem_wait(sem_mutex_);
    (*write_request_count_)++;
    if (debug_) std::cout << name_ << " startWriting: unlock sem_mutex_" << std::endl;
    sem_post(sem_mutex_);
    if (debug_) std::cout << name_ << " startWriting: lock sem_write_lock_" << std::endl;
    sem_wait(sem_write_lock_);  // Wait for exclusive write access
    if (debug_) std::cout << name_ << " startWriting: end" << std::endl;
}

void WritePriorityLock::finishWriting() {
    if (debug_) std::cout << name_ << " finishWriting: enter, lock sem_mutex_ (write_request_count_=" << *write_request_count_ << ")" << std::endl;
    sem_wait(sem_mutex_);
    (*write_request_count_)--;
    if (debug_) std::cout << name_ << " finishWriting: unlock sem_mutex_" << *write_request_count_ << std::endl;
    sem_post(sem_mutex_);
    if (debug_) std::cout << name_ << " finishWriting: unlock sem_write_lock_" << std::endl;
    sem_post(sem_write_lock_);  // Release exclusive write access
    if (debug_) std::cout << name_ << " finishWriting: end" << std::endl;
}

void WritePriorityLock::registerConsumer() {
    sem_wait(sem_register_);
    pid_t current_pid = getpid();
    int empty_slot = -1;

    for (int i = 0; i < MAX_CONSUMERS; ++i) {
        pid_t pid = consumer_pids_[i];
        if (pid != 0) {
            // Check if process still exists
            if (kill(pid, 0) == -1 && errno == ESRCH) {
                // Process is dead, clean up
                consumer_pids_[i] = 0;
                std::string dead_sem_name = "/" + name_ + "_update_" + std::to_string(pid);
                sem_unlink(dead_sem_name.c_str());
                if (empty_slot == -1) empty_slot = i;
            } else if (pid == current_pid) {
                // Already registered
                empty_slot = i;
            }
        } else if (empty_slot == -1) {
            empty_slot = i;
        }
    }

    if (empty_slot != -1) {
        consumer_pids_[empty_slot] = current_pid;
    } else {
        sem_post(sem_register_);
        throw std::runtime_error("Maximum number of consumers reached");
    }
    sem_post(sem_register_);

    my_update_sem_name_ = "/" + name_ + "_update_" + std::to_string(current_pid);
    my_update_sem_ = sem_open(my_update_sem_name_.c_str(), O_CREAT, 0666, 0);
    if (my_update_sem_ == SEM_FAILED) {
        throw std::runtime_error("Failed to open specific update semaphore");
    }

    registered_consumer_ = true;
}

void WritePriorityLock::postUpdate() {
    if (debug_) {
        std::cout << name_ << " postUpdate: start" << std::endl;
    }

    for (int i = 0; i < MAX_CONSUMERS; ++i) {
        pid_t pid = consumer_pids_[i];
        if (pid != 0) {
            sem_t* target_sem = nullptr;
            auto it = update_sems_cache_.find(pid);
            if (it != update_sems_cache_.end()) {
                target_sem = it->second;
            } else {
                std::string target_sem_name = "/" + name_ + "_update_" + std::to_string(pid);
                target_sem = sem_open(target_sem_name.c_str(), O_RDWR);
                if (target_sem != SEM_FAILED) {
                    update_sems_cache_[pid] = target_sem;
                } else {
                    target_sem = nullptr; // could be unlinked or not created yet
                }
            }

            if (target_sem != nullptr) {
                sem_post(target_sem);
                if (debug_) {
                    int value;
                    sem_getvalue(target_sem, &value);
                    std::cout << name_ << " postUpdate: pid=" << pid << " sem_update_=" << value << std::endl;
                }
            }
        }
    }

    if (debug_) {
        std::cout << name_ << " postUpdate: end" << std::endl;
    }
}

bool WritePriorityLock::waitUpdate(double timeout_seconds) {
    if (my_update_sem_ == nullptr) {
        throw std::runtime_error("waitUpdate called but consumer is not registered");
    }

    if (debug_) {
        int value;
        sem_getvalue(my_update_sem_, &value);
        std::cout << name_ << " waitUpdate: pid=" << getpid() << " sem_update_=" << value << std::endl;
    }

    if (timeout_seconds < 0) {
        sem_wait(my_update_sem_);
        if (debug_) std::cout << name_ << " waitUpdate: end" << std::endl;
        return true;
    } else {
        struct timespec ts;
        if (clock_gettime(CLOCK_REALTIME, &ts) == -1) {
            return false;
        }

        long seconds = (long)timeout_seconds;
        long nanoseconds = (long)((timeout_seconds - seconds) * 1e9);

        ts.tv_sec += seconds;
        ts.tv_nsec += nanoseconds;
        if (ts.tv_nsec >= 1000000000) {
            ts.tv_sec += 1;
            ts.tv_nsec -= 1000000000;
        }

        if (sem_timedwait(my_update_sem_, &ts) == -1) {
            return false;
        }
        if (debug_) std::cout << name_ << " waitUpdate: end" << std::endl;
        return true;
    }
}

void WritePriorityLock::reset() {
    if (debug_) std::cout << name_ << " reset: enter" << std::endl;
    *reader_count_ = 0;
    *write_request_count_ = 0;
    registered_consumer_ = false;
    for (int i = 0; i < MAX_CONSUMERS; ++i) {
        consumer_pids_[i] = 0;
    }

    sem_init(sem_mutex_, 1, 1);
    sem_init(sem_write_lock_, 1, 1);
    sem_init(sem_register_, 1, 1);
    if (debug_) std::cout << name_ << " reset: end" << std::endl;
}

} // namespace shared_memory

} // namespace cogip
