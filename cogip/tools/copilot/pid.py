from enum import IntEnum

from pydantic import BaseModel, ConfigDict, Field

from .messages import PB_Pid, PB_Pids


class PidEnum(IntEnum):
    LINEAR_POSE_PID = 0
    ANGULAR_POSE_PID = 1
    LINEAR_SPEED_PID = 2
    ANGULAR_SPEED_PID = 3


class Pid(BaseModel):
    model_config = ConfigDict(
        title="PID Properties",
        json_schema_extra=lambda s: s["properties"].pop("id"),
    )

    id: PidEnum = Field(
        ...,
        title="PID",
        description="PID name",
    )
    kp: float = Field(
        ...,
        ge=0,
        le=100000,
        multiple_of=0.001,
        title="KP",
        description="KP value",
    )
    ki: float = Field(
        ...,
        ge=0,
        le=100000,
        multiple_of=0.001,
        title="KI",
        description="KI value",
    )
    kd: float = Field(
        ...,
        ge=0,
        le=100000,
        multiple_of=0.001,
        title="KD",
        description="KD value",
    )
    integral_term_limit: int = Field(
        ...,
        ge=0,
        le=65535,
        multiple_of=1,
        title="Integral Term Limit",
        description="Integral term limit",
    )

    def pb_copy(self, message: PB_Pid) -> None:
        message.id = self.id
        message.kp = self.kp
        message.ki = self.ki
        message.kd = self.kd
        message.integral_term_limit = self.integral_term_limit


class Pids(BaseModel):
    model_config = ConfigDict(title="PID List")

    pids: list[Pid] = Field(..., title="PID List", description="List of PID properties")

    def pb_copy(self, message: PB_Pids) -> None:
        for pid in self.pids:
            pid.pb_copy(message.add_pids())
