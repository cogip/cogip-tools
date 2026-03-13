from enum import IntEnum


class ControllerEnum(IntEnum):
    QUADPID = 0
    QUADPID_TRACKER = 1
    TRACKER_SPEED_TUNING = 2
    ADAPTIVE_PURE_PURSUIT = 3
