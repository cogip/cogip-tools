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

#include <iostream>
#include <sstream>
#include <string>

namespace cogip {

namespace logger {

/// Log levels for the Logger class.
enum class LogLevel {
    DEBUG,
    INFO,
    WARNING,
    ERROR
};

/// A simple logger class that supports verbosity control and logging to stdout.
class Logger {
public:
    /// Constructs a Logger instance with a specified identifier.
    /// @param ident The identifier for the application.
    explicit Logger(const std::string& ident, LogLevel currentLevel = LogLevel::INFO)
        : ident_(ident), currentLevel_(currentLevel) {}

    /// Sets the verbosity level for logging.
    /// @param level The minimum log level to display.
    void setLevel(LogLevel level) {
        currentLevel_ = level;
    }

    /// Logs a debug-level message.
    Logger& debug() {
        return log(LogLevel::DEBUG);
    }

    /// Logs an info-level message.
    Logger& info() {
        return log(LogLevel::INFO);
    }

    /// Logs a warning-level message.
    Logger& warning() {
        return log(LogLevel::WARNING);
    }

    /// Logs an error-level message.
    Logger& error() {
        return log(LogLevel::ERROR);
    }

    /// Overloads the operator<< to append log data.
    template <typename T>
    Logger& operator<<(const T& value) {
        if (isActive_) {
            stream_ << value;
        }
        return *this;
    }

    /// Support for manipulators like std::endl.
    Logger& operator<<(std::ostream& (*manip)(std::ostream&)) {
        if (isActive_ && manip == static_cast<std::ostream& (*)(std::ostream&)>(std::endl)) {
            flush();
        }
        return *this;
    }

private:
    std::string ident_;            ///< Identifier for the logger.
    std::ostringstream stream_;    ///< Stream to accumulate log messages.
    LogLevel currentLevel_;        ///< Current verbosity level.
    LogLevel activeLevel_;         ///< Log level of the current message.
    bool isActive_ = false;        ///< Whether the current log entry is active.

    /// Logs a message with a specified log level.
    Logger& log(LogLevel level) {
        if (shouldLog(level)) {
            prepareLog(level);
        } else {
            isActive_ = false;
        }
        return *this;
    }

    /// Checks if a message should be logged based on the current verbosity level.
    bool shouldLog(LogLevel level) const {
        return static_cast<int>(level) >= static_cast<int>(currentLevel_);
    }

    /// Prepares a log entry with the specified log level.
    void prepareLog(LogLevel level) {
        static const char* levelStrings[] = {"DEBUG", "INFO", "WARNING", "ERROR"};
        activeLevel_ = level;
        isActive_ = true;
        stream_.str(""); // Clear the previous message
        stream_.clear();
        stream_ << "[" << ident_ << "] [" << levelStrings[static_cast<int>(level)] << "] ";
    }

    /// Writes the log entry to stdout.
    void flush() {
        if (isActive_) {
            const std::string& message = stream_.str();

            // Write to stdout (or stderr for errors)
            if (activeLevel_ == LogLevel::ERROR) {
                std::cerr << message << std::endl;
            } else {
                std::cout << message << std::endl;
            }

            // Clear the stream after flushing
            stream_.str("");
            stream_.clear();
            isActive_ = false;
        }
    }
};

} // namespace logger

} // namespace cogip
