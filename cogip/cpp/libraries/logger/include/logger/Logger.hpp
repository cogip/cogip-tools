// Copyright (C) 2025 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @defgroup    lib_logger Logger module
/// @ingroup     lib
/// @brief       Logger module
///
/// The Logger module provides a simple interface for logging messages
/// to the system log (Syslog).
///
/// @{
/// @file
/// @brief       Public API for the Logger module
/// @author      Gilles DOFFE <g.doffe@gmail.com>

#pragma once

#include <string>
#include <sstream>
#include <syslog.h>

namespace cogip {

namespace logger {

/// A logger class for logging messages to the system log (Syslog) with various log levels.
class Logger {
public:
    /// Constructs a Logger instance with a specified identifier.
    /// @param ident The identifier for the application.
    /// @param facility The logging facility (default is LOG_USER).
    Logger(const std::string& ident, int facility = LOG_USER) : _ident(ident), _facility(facility) {
        openlog(_ident.c_str(), LOG_PID | LOG_CONS, _facility);
    }

    ///  Destructor that closes the Syslog connection.
    ~Logger() {
        closelog();
    }

    /// Begins a debug-level log entry.
    /// @return A reference to the internal stream object to allow chained operator<< calls.
    Logger& debug() {
        return setLogLevel(LOG_DEBUG);
    }

    /// Begins an info-level log entry.
    /// @return A reference to the internal stream object to allow chained operator<< calls.
    Logger& info() {
        return setLogLevel(LOG_INFO);
    }

    /// Begins a warning-level log entry.
    /// @return A reference to the internal stream object to allow chained operator<< calls.
    Logger& warning() {
        return setLogLevel(LOG_WARNING);
    }

    /// Begins an error-level log entry.
    /// @return A reference to the internal stream object to allow chained operator<< calls.
    Logger& error() {
        return setLogLevel(LOG_ERR);
    }

    /// Sends the log entry to syslog.
    void flush() {
        syslog(_logLevel, "%s", _stream.str().c_str());
        _stream.str("");  // Clear the stream buffer after logging
        _stream.clear();  // Reset the stream state
    }

    /// Overloads the operator<< to collect log data.
    /// @param value Any type of value that can be streamed.
    /// @return A reference to the Logger instance.
    template<typename T>
    Logger& operator<<(const T& value) {
        _stream << value;
        return *this;
    }

private:
    std::ostringstream _stream;  // Stream to accumulate log messages
    int _logLevel;               // The current log level for the message
    std::string _ident;          // Application identifier
    int _facility;               // Logging facility for syslog

    /// Sets the log level and prepares the stream.
    /// @param logLevel The syslog log level (LOG_DEBUG, LOG_INFO, etc.).
    /// @return A reference to the Logger instance.
    Logger& setLogLevel(int logLevel) {
        _logLevel = logLevel;
        return *this;
    }
};

} // namespace logger

} // namespace cogip
