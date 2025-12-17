#!/usr/bin/env python3

# This script performs an ACTIVE check for a YDLidar G2.
# 1. Checks ROBOT_ID. If not 1, skip check and exit 0 (success).
# 2. If ROBOT_ID=1, checks if DETECTOR_LIDAR_PORT is set and exists.
# 3. If port exists, sends a "Get Health Status" command and waits for
#    the specific response header.
#
# Exits 0 (success) if Lidar responds correctly OR if check is skipped.
# Exits 1 (failure) if the port is missing or the Lidar doesn't respond.

import logging
import os
import sys
from pathlib import Path

import serial

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- YDLidar G2 specific commands from manual ---
# "Get Health Status" command
HEALTH_CMD = b"\xa5\x92"
# Expected "Start Sign" in all responses
EXPECTED_RESP_HEADER = b"\xa5\x5a"

try:
    # Verify ROBOT_ID
    robot_id_str = os.environ.get("ROBOT_ID")
    if not robot_id_str:
        logger.error("Lidar check FAILED: ROBOT_ID is not set in environment.")
        sys.exit(3)  # Configuration error

    try:
        robot_id = int(robot_id_str)
    except ValueError:
        logger.error(f"Lidar check FAILED: ROBOT_ID '{robot_id_str}' is not a valid integer.")
        sys.exit(3)  # Configuration error

    # Skip check if not Robot 1
    if robot_id > 1:
        logger.info(f"ROBOT_ID={robot_id}. Skipping YDLidar G2 check (intended for Robot 1 only).")
        sys.exit(0)  # Success (skip)

    logger.info(f"ROBOT_ID={robot_id}. Proceeding with YDLidar G2 check.")

    # Verify environment variable is set
    port = os.environ.get("DETECTOR_LIDAR_PORT")
    if not port:
        logger.error("Lidar check FAILED: DETECTOR_LIDAR_PORT is not set in environment.")
        sys.exit(1)  # Failure!

    # Verify the port file exists
    port_path = Path(port)
    if not port_path.exists() or not port_path.is_char_device():
        logger.error(f"Lidar check FAILED: Port '{port}' does not exist or is not a TTY device.")
        sys.exit(1)  # Failure!

    # Get BAUD RATE
    try:
        baud = int(os.environ.get("DETECTOR_LIDAR_BAUD", "115200"))
    except ValueError:
        logger.error("Invalid DETECTOR_LIDAR_BAUD. Must be an integer.")
        sys.exit(3)  # Configuration error

    # Set a 1-second timeout
    timeout = 1.0

    logger.info(f"Probing Lidar on {port} at {baud} baud...")

    # Open the port
    ser = serial.Serial(port, baudrate=baud, timeout=timeout)

    # Send the command
    ser.write(HEALTH_CMD)

    # Read the response header
    response_header = ser.read(2)

    ser.close()

    if response_header == EXPECTED_RESP_HEADER:
        logger.info(f"Lidar check SUCCESS on {port} (received valid header).")
        sys.exit(0)  # Success!
    elif not response_header:
        logger.warning(f"Lidar check FAILED on {port} (no response, timed out).")
        sys.exit(1)  # Failure!
    else:
        logger.warning(f"Lidar check FAILED on {port} (received invalid data: {response_header.hex()}).")
        sys.exit(1)  # Failure!

except serial.SerialException as e:
    # Handle errors during serial comms
    port_str = os.environ.get("DETECTOR_LIDAR_PORT", "N/A")
    logger.error(f"Lidar check FAILED on {port_str}: {e}")
    sys.exit(2)  # Failure!
except Exception as e:
    # Handle all other unexpected errors
    logger.error(f"Lidar check FAILED with unexpected error: {e}")
    sys.exit(3)  # General failure
