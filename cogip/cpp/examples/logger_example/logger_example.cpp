#include "logger/PythonLogger.hpp"

#include <cstdlib>

namespace logger_example {

void emit_logs() {
    // Explicit method
    cogip::logger::log_debug("This is a debug message (explicit method)");
    cogip::logger::log_info("This is an info message (explicit method)");
    cogip::logger::log_warning("This is a warning (explicit method)");
    cogip::logger::log_error("This is an error (explicit method)");

    // Stream method
    cogip::logger::debug << "This is a debug message (stream method)" << std::endl;
    cogip::logger::info << "This is an info message (stream method)" << std::endl;
    cogip::logger::warning << "This is a warning (stream method)" << std::endl;
    cogip::logger::error << "This is an error (stream method)" << std::endl;

    // Standard redirection
    std::cout << "This is a stdout message (info by default)" << std::endl;
    std::cerr << "This is a stderr message (error by default)" << std::endl;

    // Usage with variables and expressions
    int value = 42;
    double pi = 3.14159;
    cogip::logger::info << "The value is " << value << " and Pi is " << pi << std::endl;
}

} // logger_example namespace
