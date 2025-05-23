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
    sem_update_(nullptr),
    sem_register_(nullptr),
    reader_shm_fd_(-1),
    write_request_shm_fd_(-1),
    consumer_count_shm_fd_(-1),
    reader_count_(nullptr),
    write_request_count_(nullptr),
    consumer_count_(nullptr),
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

    // Open or create the update semaphore
    if (owner) {
        sem_update_ = sem_open(update_name_.c_str(), O_CREAT | O_RDWR | O_TRUNC, 0666, 1);
    }
    else {
        sem_update_ = sem_open(update_name_.c_str(), O_RDWR);
    }
    if (sem_update_ == SEM_FAILED) {
        throw std::runtime_error("Failed to open update semaphore");
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
        if (ftruncate(consumer_count_shm_fd_, sizeof(int)) < 0) {
            throw std::runtime_error("Failed to truncate shared memory for consumer count");
        }
    }
    consumer_count_ = static_cast<int*>(mmap(NULL, sizeof(int), PROT_READ | PROT_WRITE, MAP_SHARED, consumer_count_shm_fd_, 0));
    if (consumer_count_ == MAP_FAILED) {
        throw std::runtime_error("Failed to map shared memory for consumer count");
    }
    if (owner_) {
        reset();
    }

}

WritePriorityLock::~WritePriorityLock() {
    if (registered_consumer_) {
        sem_wait(sem_register_);
        (*consumer_count_)--;
        sem_post(sem_register_);
    }
    if (consumer_count_ != nullptr) {
        munmap(consumer_count_, sizeof(int));
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
    if (sem_update_ != nullptr) {
        sem_close(sem_update_);
    }
    if (sem_write_lock_ != nullptr) {
        sem_close(sem_write_lock_);
    }
    if (sem_mutex_) {
        sem_close(sem_mutex_);
    }
    if (owner_) {
        sem_unlink(registration_name_.c_str());
        sem_unlink(update_name_.c_str());
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
    registered_consumer_ = true;
    sem_wait(sem_register_);
    (*consumer_count_)++;
    sem_post(sem_register_);
}

void WritePriorityLock::postUpdate() {
    if (debug_) {
        int value;
        sem_getvalue(sem_update_, &value);
        std::cout << name_ << " postUpdate: count= " << *consumer_count_ << " sem_update_=" << value << std::endl;
    }
    for (int i = 0; i < *consumer_count_; ++i) {
        sem_post(sem_update_);
    }
}

void WritePriorityLock::waitUpdate() {
    if (debug_) {
        int value;
        sem_getvalue(sem_update_, &value);
        std::cout << name_ << " waitUpdate: count=" << *consumer_count_ << " sem_update_=" << value << std::endl;
    }
    sem_wait(sem_update_);
    if (debug_) std::cout << name_ << " waitUpdate: end" << std::endl;
}

void WritePriorityLock::reset() {
    if (debug_) std::cout << name_ << " reset: enter" << std::endl;
    *reader_count_ = 0;
    *write_request_count_ = 0;
    registered_consumer_ = false;
    *consumer_count_ = 0;

    sem_init(sem_mutex_, 1, 1);
    sem_init(sem_write_lock_, 1, 1);
    sem_init(sem_update_, 1, 0);
    sem_init(sem_register_, 1, 1);
    if (debug_) std::cout << name_ << " reset: end" << std::endl;
}

} // namespace shared_memory

} // namespace cogip
