// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @defgroup    lib_logger Logger module
/// @ingroup     lib
/// @brief       Logger module
///
/// @{
/// @file
/// @brief       Definition of the LogLevel enum
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

namespace cogip {

namespace logger {

/// Log levels for the Logger class.
enum class LogLevel {
    DEBUG,
    INFO,
    WARNING,
    ERROR
};

} // namespace logger

} // namespace cogip

/// @}
