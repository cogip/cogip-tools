#pragma once

#include <cassert>
#include <iostream>
#include <pthread.h>

typedef unsigned long  _size_t;
typedef _size_t(*thread_proc_t)(void*);

#define CLASS_THREAD(c , x ) Thread::ThreadCreateObjectFunctor<c, &c::x>(this)

namespace ydlidar {
class Thread {
public:
    template <class CLASS, int (CLASS::* PROC)(void)> static Thread
        ThreadCreateObjectFunctor(CLASS* pthis) {
        return createThread(createThreadAux<CLASS, PROC>, pthis);
    }

    template <class CLASS, int (CLASS::* PROC)(void) > static _size_t
        createThreadAux(void* param) {
        return (static_cast<CLASS*>(param)->*PROC)();
    }

    static Thread createThread(thread_proc_t proc, void* param = NULL) {
        Thread thread_(proc, param);
        assert(sizeof(thread_._handle) >= sizeof(pthread_t));

        pthread_create((pthread_t*)&thread_._handle, NULL, (void* (*)(void*))proc,
            param);
        return thread_;
    }

    explicit Thread() : _param(NULL), _func(NULL), _handle(0) {}
    virtual ~Thread() {}
    _size_t getHandle() {
        return _handle;
    }
    int terminate() {
        if (!this->_handle) {
            return 0;
        }

        return pthread_cancel((pthread_t)this->_handle);
    }
    void* getParam() {
        return _param;
    }
    int join(unsigned long timeout = -1) {
        if (!this->_handle) {
            return 0;
        }

        void* res;
        int s = -1;
        s = pthread_cancel((pthread_t)(this->_handle));

        if (s != 0) {
        }

        s = pthread_join((pthread_t)(this->_handle), &res);

        if (s != 0) {
        }

        if (res == PTHREAD_CANCELED) {
            std::cout << this->_handle << " thread has been canceled" << std::endl;
            this->_handle = 0;
        }

        return 0;
    }

    bool operator== (const Thread& right) {
        return this->_handle == right._handle;
    }

protected:
    explicit Thread(thread_proc_t proc, void* param) : _param(param), _func(proc),
        _handle(0) {
    }
    void* _param;
    thread_proc_t _func;
    _size_t _handle;
};

} // namespace ydlidar
