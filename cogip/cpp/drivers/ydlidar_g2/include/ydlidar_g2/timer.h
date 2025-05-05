#pragma once

#include <cassert>
#include <ctime>
#include <inttypes.h>
#include <sys/time.h>
#include <unistd.h>

static inline void delay(uint32_t ms) {
    while (ms >= 1000) {
        usleep(1000 * 1000);
        ms -= 1000;
    };

    if (ms != 0) {
        usleep(ms * 1000);
    }
}

uint32_t getHDTimer();
uint64_t getCurrentTime();
