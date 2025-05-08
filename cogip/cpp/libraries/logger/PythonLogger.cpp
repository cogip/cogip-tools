#include "logger/PythonLogger.hpp"

namespace cogip {

namespace logger {

// Function that will be defined on the Python side
std::function<void(const std::string&, LogLevel)> py_log_callback;

int PythonLogger::overflow(int c) {
    if (c != EOF) {
        if (c == '\n') {
            // When we encounter a newline, we send the buffer to the Python logger
            if (py_log_callback) {  // Ensure callback is valid
                py_log_callback(buffer_, default_level_);
            }
            buffer_.clear();
        } else {
            buffer_ += static_cast<char>(c);
        }
    }
    return c;
}

int PythonLogger::sync() {
    if (!buffer_.empty() && py_log_callback) {  // Ensure callback is valid
        py_log_callback(buffer_, default_level_);
        buffer_.clear();
    }
    return 0;
}

// Buffers and backups for stdout and stderr
PythonLogger stdout_buf(LogLevel::INFO);
PythonLogger stderr_buf(LogLevel::ERROR);

void set_logger_callback(std::function<void(const std::string&, LogLevel)> callback) {
    py_log_callback = callback;
    std::cout.rdbuf(&stdout_buf);
    std::cerr.rdbuf(&stderr_buf);
}

void unset_logger_callback() {
    py_log_callback = nullptr;
    std::cout.rdbuf(nullptr);  // Reset to default
    std::cerr.rdbuf(nullptr);  // Reset to default
}

// API for explicit logging in C++
void log_debug(const std::string& message) {
    if (py_log_callback) py_log_callback(message, LogLevel::DEBUG);
}

void log_info(const std::string& message) {
    if (py_log_callback) py_log_callback(message, LogLevel::INFO);
}

void log_warning(const std::string& message) {
    if (py_log_callback) py_log_callback(message, LogLevel::WARNING);
}

void log_error(const std::string& message) {
    if (py_log_callback) py_log_callback(message, LogLevel::ERROR);
}

} // namespace logger

} // namespace cogip

