// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @defgroup    lib_logger Logger module
/// @ingroup     lib
/// @brief       Python Logger module
///
/// The Python Logger module provides an interface to forward log messages to a Python logger.
///
/// @{
/// @file
/// @brief       PythonLogger class declaration
/// @author      Eric Courtois <eric.courtois@gmail.com>

#pragma once

#include "LogLevel.hpp"

#include <functional>
#include <iostream>
#include <streambuf>
#include <string>

namespace cogip {

namespace logger {

/// Custom streambuf that redirects to the Python callback
class PythonLogger : public std::streambuf {
    public:
    /// Constructor
    /// @param level The default log level
    PythonLogger(LogLevel level) : default_level_(level) {
    }

    /// Destructor
    /// @note This will call sync() to ensure that any remaining data in the buffer is sent to the Python logger
    ~PythonLogger() {
        sync();
    }

protected:
    /// Override overflow to handle character input
    virtual int overflow(int c = EOF);

    /// Override sync to handle flushing the buffer
    virtual int sync();

private:
    std::string buffer_; ///< Buffer to hold the data before sending it to the Python logger
    LogLevel default_level_; ///< Default log level
};

/// Class for logging to Python
/// This class inherits from std::ostream and uses a custom streambuf to redirect output to Python
class PythonStreamLogger : public std::ostream {
public:
    /// Constructor
    /// @param level The log level for this stream
    PythonStreamLogger(LogLevel level) : std::ostream(nullptr), buffer_(level) {
        rdbuf(&buffer_);
    }

    /// Destructor
    /// @note This will call sync() to ensure that any remaining data in the buffer is sent to the Python logger
    ~PythonStreamLogger() {
    }

private:
    PythonLogger buffer_; ///< Buffer to hold the data before sending it to the Python logger
};

PythonStreamLogger debug(LogLevel::DEBUG);
PythonStreamLogger info(LogLevel::INFO);
PythonStreamLogger warning(LogLevel::WARNING);
PythonStreamLogger error(LogLevel::ERROR);

/// Function to set the Python callback
void set_logger_callback(std::function<void(const std::string&, LogLevel)> callback);

/// Function to unset the Python callback
void unset_logger_callback();

// API for explicit logging in C++
void log_debug(const std::string& message);

void log_info(const std::string& message);

void log_warning(const std::string& message);

void log_error(const std::string& message);

} // namespace logger

} // namespace cogip

/// @}
