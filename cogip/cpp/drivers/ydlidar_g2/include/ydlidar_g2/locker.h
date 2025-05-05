#pragma once

#include <cassert>
#include <cerrno>
#include <cstdio>
#include <iostream>
#include <pthread.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/stat.h>

namespace ydlidar {

class Locker {
public:
    enum LOCK_STATUS {
        LOCK_OK = 0,
        LOCK_TIMEOUT = -1,
        LOCK_FAILED = -2
    };

    Locker() {
        init();
    }

    ~Locker() {
        release();
    }

    Locker::LOCK_STATUS lock(unsigned long timeout = 0xFFFFFFFF) {
        if (timeout == 0xFFFFFFFF) {
            if (pthread_mutex_lock(&lock_) == 0) {
                return LOCK_OK;
            }
        }

        else if (timeout == 0) {
            if (pthread_mutex_trylock(&lock_) == 0) {
                return LOCK_OK;
            }
        }

        else {
            timespec wait_time;
            timeval now;
            gettimeofday(&now, NULL);

            wait_time.tv_sec = timeout / 1000 + now.tv_sec;
            wait_time.tv_nsec = (timeout % 1000) * 1000000 + now.tv_usec * 1000;

            if (wait_time.tv_nsec >= 1000000000) {
                ++wait_time.tv_sec;
                wait_time.tv_nsec -= 1000000000;
            }

            switch (pthread_mutex_timedlock(&lock_, &wait_time)) {
            case 0:
                return LOCK_OK;

            case ETIMEDOUT:
                return LOCK_TIMEOUT;
            }

        }

        return LOCK_FAILED;
    }


    void unlock() {
        pthread_mutex_unlock(&lock_);
    }

    pthread_mutex_t* getLockHandle() {
        return &lock_;
    }



protected:
    void init() {
        pthread_mutex_init(&lock_, NULL);
    }

    void release() {
        unlock();
        pthread_mutex_destroy(&lock_);
    }

    pthread_mutex_t lock_;
};


class Event {
public:

    enum {
        EVENT_OK = 1,
        EVENT_TIMEOUT = 2,
        EVENT_FAILED = 0,
    };

    explicit Event(bool isAutoReset = true, bool isSignal = false)
        : _is_signalled(isSignal)
        , _isAutoReset(isAutoReset) {
        int ret = pthread_condattr_init(&_cond_cattr);

        if (ret != 0) {
            std::cerr << "Failed to init condattr..." << std::endl;
        }

        ret = pthread_condattr_setclock(&_cond_cattr, CLOCK_MONOTONIC);
        pthread_mutex_init(&_cond_locker, NULL);
        ret = pthread_cond_init(&_cond_var, &_cond_cattr);
    }

    ~Event() {
        release();
    }

    void set(bool isSignal = true) {
        if (isSignal) {
            pthread_mutex_lock(&_cond_locker);

            if (_is_signalled == false) {
                _is_signalled = true;
                pthread_cond_signal(&_cond_var);
            }

            pthread_mutex_unlock(&_cond_locker);
        }
        else {
            pthread_mutex_lock(&_cond_locker);
            _is_signalled = false;
            pthread_mutex_unlock(&_cond_locker);
        }
    }

    unsigned long wait(unsigned long timeout = 0xFFFFFFFF) {
        unsigned long ans = EVENT_OK;
        pthread_mutex_lock(&_cond_locker);

        if (!_is_signalled) {
            if (timeout == 0xFFFFFFFF) {
                pthread_cond_wait(&_cond_var, &_cond_locker);
            }
            else {
                struct timespec wait_time;
                clock_gettime(CLOCK_MONOTONIC, &wait_time);


                wait_time.tv_sec += timeout / 1000;
                wait_time.tv_nsec += (timeout % 1000) * 1000000ULL;

                if (wait_time.tv_nsec >= 1000000000) {
                    ++wait_time.tv_sec;
                    wait_time.tv_nsec -= 1000000000;
                }

                switch (pthread_cond_timedwait(&_cond_var, &_cond_locker, &wait_time)) {
                case 0:
                    // signalled
                    break;

                case ETIMEDOUT:
                    // time up
                    ans = EVENT_TIMEOUT;
                    goto _final;
                    break;

                default:
                    ans = EVENT_FAILED;
                    goto _final;
                }

            }
        }

        assert(_is_signalled);

        if (_isAutoReset) {
            _is_signalled = false;
        }

    _final:
        pthread_mutex_unlock(&_cond_locker);

        return ans;

    }

protected:
    void release() {
        pthread_condattr_destroy(&_cond_cattr);
        pthread_mutex_destroy(&_cond_locker);
        pthread_cond_destroy(&_cond_var);
    }

    pthread_condattr_t     _cond_cattr;
    pthread_cond_t         _cond_var;
    pthread_mutex_t        _cond_locker;
    bool                   _is_signalled;
    bool                   _isAutoReset;
};

class ScopedLocker {
public:
    explicit ScopedLocker(Locker& l) : _binded(l) {
        _binded.lock();
    }

    void forceUnlock() {
        _binded.unlock();
    }
    ~ScopedLocker() {
        _binded.unlock();
    }
    Locker& _binded;
};

} // namespace ydlidar
