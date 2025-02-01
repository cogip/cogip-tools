from enum import IntEnum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field

from cogip.scservo_sdk import COMM_SUCCESS, PortHandler, scscl
from . import logger


def upper_snake_to_title(string: str):
    return " ".join(word.capitalize() for word in string.split("_"))


class SCServoEnum(IntEnum):
    """Enum defining SC Servo IDs"""

    MAGNET_SIDE_RIGHT = 1
    ARM_RIGHT = 2
    MAGNET_CENTER_RIGHT = 3
    MAGNET_CENTER_LEFT = 4
    ARM_LEFT = 5
    MAGNET_SIDE_LEFT = 6
    ARM_GRIP_LEFT = 7
    ARM_GRIP_RIGHT = 8
    GRIP_RIGHT = 9
    GRIP_LEFT = 10


class SCServosProperties(BaseModel):
    MAGNET_SIDE_RIGHT: Annotated[int, Field(ge=1, le=1000)] = 1
    ARM_RIGHT: Annotated[int, Field(ge=1, le=1000)] = 1
    MAGNET_CENTER_RIGHT: Annotated[int, Field(ge=1, le=1000)] = 1
    MAGNET_CENTER_LEFT: Annotated[int, Field(ge=1, le=1000)] = 1
    ARM_LEFT: Annotated[int, Field(ge=1, le=1000)] = 1
    MAGNET_SIDE_LEFT: Annotated[int, Field(ge=1, le=1000)] = 1
    ARM_GRIP_LEFT: Annotated[int, Field(ge=1, le=1000)] = 1
    ARM_GRIP_RIGHT: Annotated[int, Field(ge=1, le=1000)] = 1
    GRIP_RIGHT: Annotated[int, Field(ge=1, le=1000)] = 1
    GRIP_LEFT: Annotated[int, Field(ge=1, le=1000)] = 1


class SCServos:
    def __init__(self, port: Path | None = None, baud_rate: int = 0):
        self.properties = SCServosProperties()
        if not port:
            self.port_handler = None
            self.packet_handler = None
            return

        self.port_handler = PortHandler(str(port))
        self.packet_handler = scscl(self.port_handler)

        if not self.port_handler.openPort():
            logger.error("Failed to open SC Servos port")
            self.port_handler = None
            return
        logger.info("Succeeded to open SC Servos port")

        if not self.port_handler.setBaudRate(baud_rate):
            logger.error("Failed to change the baudrate")
            self.port_handler = None
            return

    def get_schema(self) -> dict:
        self.read_all()
        schema = SCServosProperties.model_json_schema()
        # Add namespace in JSON Schema
        schema["namespace"] = "/planner"
        schema["sio_event"] = "scservo_updated"
        # Add current values in JSON Schema
        for prop, value in self.properties.model_dump().items():
            schema["properties"][prop]["value"] = value
            schema["properties"][prop]["title"] = upper_snake_to_title(prop)
        return schema

    def update_property(self, id: SCServoEnum, value: int):
        self.properties.__setattr__(id.name, value)

    def read_all(self):
        if not self.port_handler:
            return

        for id in SCServoEnum:
            current_position, _, result, _ = self.packet_handler.ReadPosSpeed(id)
            if result != COMM_SUCCESS:
                logger.error(f"SCServo {id.name}: failed to read position ({self.packet_handler.getTxRxResult(result)}")
            self.update_property(id, current_position)

    def set(self, id: SCServoEnum, value: int, speed: int = 2400):
        if not self.port_handler:
            return

        self.update_property(id, value)
        result, error = self.packet_handler.WritePos(id.value, value, 0, speed)
        if result != COMM_SUCCESS:
            logger.error(f"SCServo {id.name}: failed to write position ({self.packet_handler.getTxRxResult(result)}")
