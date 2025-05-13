import atexit
import logging
import logging.handlers
import os
from pathlib import Path

from cogip.cpp.libraries import logger as cpp_logger


class Logger:
    """
    A Python class that integrates with C++ logging functionality.
    This class manages a Python logger and connects it to C++ logging streams.
    """

    def __init__(self, name: str, *, level: int = logging.INFO, enable_cpp: bool = True):
        """
        Initialize the logger with a specific name and level.

        Args:
            name: Name of the logger (appears in log output)
            level: Minimum logging level
            enable_cpp: If True, enables C++ logging integration
        """
        self.name = name
        self.is_destroyed = False  # Flag to track destruction

        # Create the Python logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Prevent the log messages from being handled by parent loggers
        self.logger.propagate = False

        # Remove existing handlers if any
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        formatter = logging.Formatter("[%(asctime)s][%(name)s][%(threadName)s] %(levelname)s: %(message)s")

        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Add file handler
        # Check if user has root permissions
        if os.geteuid() == 0:
            # If user has root permissions, like on Raspberry Pi,
            # use /var/log/cogip to allow log persistence
            log_dir = Path("/var/log/cogip")
        else:
            # If user does not have root permissions, like in Docker stack,
            # use /tmp since no persistent storage is required
            log_dir = Path("/tmp/cogip-logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        robot_id = os.getenv("ROBOT_ID", "X")
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"robot{robot_id}-{name}.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Add syslog handler
        if Path("/dev/log").exists():
            syslog_handler = logging.handlers.SysLogHandler(address="/dev/log")
            syslog_handler.setLevel(level)
            syslog_handler.setFormatter(formatter)
            self.logger.addHandler(syslog_handler)

        if enable_cpp:
            self.enable_cpp_logging()

        atexit.register(self.cleanup)  # Register cleanup function

    def __del__(self):
        self.cleanup()

    def enable_cpp_logging(self):
        """Enable C++ logging integration."""
        if not self.is_destroyed:
            cpp_logger.set_logger_callback(self.log_callback)

    def cleanup(self):
        """Cleanup function to unregister the callback."""
        if not self.is_destroyed:
            self.is_destroyed = True
            cpp_logger.unset_logger_callback()  # Unregister the callback

    def log_callback(self, message: str, level: cpp_logger.LogLevel):
        """
        Callback function for C++ logging.
        Routes C++ log messages to the appropriate Python logger method.

        Args:
            message: The log message from C++
            level: Logging level from C++
        """
        # Avoid processing if the logger is destroyed
        if self.is_destroyed:
            return
        if not message:
            return
        logger_func = getattr(self.logger, level.name.lower(), self.logger.info)
        logger_func(f"[C++] {message}")

    def debug(self, message):
        """Log a debug message from Python"""
        self.logger.debug(message)

    def info(self, message):
        """Log an info message from Python"""
        self.logger.info(message)

    def warning(self, message):
        """Log a warning message from Python"""
        self.logger.warning(message)

    def error(self, message):
        """Log an error message from Python"""
        self.logger.error(message)

    def setLevel(self, level: int):
        """
        Set the logging level for the logger.

        Args:
            level: The logging level to set
        """
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)
