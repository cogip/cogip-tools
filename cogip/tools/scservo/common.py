import sys
from pathlib import Path

from cogip.scservo_sdk import PortHandler, scscl
from . import logger


def init_servo(port: Path, baud_rate: int) -> tuple[PortHandler, scscl]:
    port_handler = PortHandler(str(port))
    packet_handler = scscl(port_handler)

    if not port_handler.openPort():
        logger.error("Failed to open the port")
        sys.exit(1)

    logger.info("Succeeded to open the port")

    if not port_handler.setBaudRate(baud_rate):
        logger.error("Failed to change the baudrate")
        sys.exit(1)

    logger.info("Succeeded to change the baudrate")

    return port_handler, packet_handler
