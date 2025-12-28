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

    FRONT_GRIP_LEFT_SIDE = 1
    FRONT_GRIP_LEFT_CENTER = 2
    FRONT_GRIP_RIGHT_CENTER = 3
    FRONT_GRIP_RIGHT_SIDE = 4
    FRONT_AXIS_LEFT_SIDE = 5
    FRONT_AXIS_LEFT_CENTER = 6
    FRONT_AXIS_RIGHT_CENTER = 7
    FRONT_AXIS_RIGHT_SIDE = 8
    FRONT_ARM_LEFT = 9
    FRONT_ARM_RIGHT = 10

    BACK_GRIP_LEFT_SIDE = 11
    BACK_GRIP_LEFT_CENTER = 12
    BACK_GRIP_RIGHT_CENTER = 13
    BACK_GRIP_RIGHT_SIDE = 14
    BACK_AXIS_LEFT_SIDE = 15
    BACK_AXIS_LEFT_CENTER = 16
    BACK_AXIS_RIGHT_CENTER = 17
    BACK_AXIS_RIGHT_SIDE = 18
    BACK_ARM_LEFT = 19
    BACK_ARM_RIGHT = 20


class SCServosProperties(BaseModel):
    FRONT_GRIP_LEFT_SIDE: Annotated[int, Field(ge=1, le=1200)] = 1
    FRONT_GRIP_LEFT_CENTER: Annotated[int, Field(ge=1, le=1200)] = 1
    FRONT_GRIP_RIGHT_CENTER: Annotated[int, Field(ge=1, le=1200)] = 1
    FRONT_GRIP_RIGHT_SIDE: Annotated[int, Field(ge=1, le=1200)] = 1
    FRONT_AXIS_LEFT_SIDE: Annotated[int, Field(ge=1, le=1200)] = 1
    FRONT_AXIS_LEFT_CENTER: Annotated[int, Field(ge=1, le=1200)] = 1
    FRONT_AXIS_RIGHT_CENTER: Annotated[int, Field(ge=1, le=1200)] = 1
    FRONT_AXIS_RIGHT_SIDE: Annotated[int, Field(ge=1, le=1200)] = 1
    FRONT_ARM_LEFT: Annotated[int, Field(ge=1, le=1200)] = 1
    FRONT_ARM_RIGHT: Annotated[int, Field(ge=1, le=1200)] = 1

    BACK_GRIP_LEFT_SIDE: Annotated[int, Field(ge=1, le=1200)] = 1
    BACK_GRIP_LEFT_CENTER: Annotated[int, Field(ge=1, le=1200)] = 1
    BACK_GRIP_RIGHT_CENTER: Annotated[int, Field(ge=1, le=1200)] = 1
    BACK_GRIP_RIGHT_SIDE: Annotated[int, Field(ge=1, le=1200)] = 1
    BACK_AXIS_LEFT_SIDE: Annotated[int, Field(ge=1, le=1200)] = 1
    BACK_AXIS_LEFT_CENTER: Annotated[int, Field(ge=1, le=1200)] = 1
    BACK_AXIS_RIGHT_CENTER: Annotated[int, Field(ge=1, le=1200)] = 1
    BACK_AXIS_RIGHT_SIDE: Annotated[int, Field(ge=1, le=1200)] = 1
    BACK_ARM_LEFT: Annotated[int, Field(ge=1, le=1200)] = 1
    BACK_ARM_RIGHT: Annotated[int, Field(ge=1, le=1200)] = 1


class SCServos:
    def __init__(self, port: Path | None = None, baud_rate: int = 0):
        self.properties = SCServosProperties()
        if not port:
            self.port_handler = None
            self.packet_handler = None
            return

        self.port_handler = PortHandler(str(port))
        self.packet_handler = scscl(self.port_handler)
        self.reg_props: dict[SCServoEnum, int] = {}

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

    def set(self, id: SCServoEnum, value: int, speed: int = 2400, reg_only: bool = False):
        if not self.port_handler:
            return

        if reg_only:
            self.reg_props[id] = value
            func = self.packet_handler.RegWritePos
        else:
            self.update_property(id, value)
            func = self.packet_handler.WritePos

        result, _ = func(id.value, value, 0, speed)
        if result != COMM_SUCCESS:
            logger.error(
                f"SCServo {id.name}: failed to {'reg' if reg_only else ''} write position "
                f"({self.packet_handler.getTxRxResult(result)}"
            )
            return

    def action(self):
        if not self.port_handler:
            return

        if not self.reg_props:
            logger.warning("SCServo: failed to reg action (no registered actions)")
            return

        result, _ = self.packet_handler.RegAction()
        if result != COMM_SUCCESS:
            logger.error(f"SCServo: failed to reg action ({self.packet_handler.getTxRxResult(result)}")
            return

        for id, value in self.reg_props.items():
            self.update_property(id, value)
        self.reg_props.clear()
