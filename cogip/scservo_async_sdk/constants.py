from enum import IntEnum, IntFlag


# Instruction for SC Protocol
class Instruction(IntEnum):
    PING = 1
    READ = 2
    WRITE = 3
    REG_WRITE = 4
    ACTION = 5
    SYNC_WRITE = 131  # 0x83
    SYNC_READ = 130  # 0x82


# Communication Result
class CommResult(IntEnum):
    SUCCESS = 0
    PORT_BUSY = -1
    TX_FAIL = -2
    RX_FAIL = -3
    TX_ERROR = -4
    RX_WAITING = -5
    RX_TIMEOUT = -6
    RX_CORRUPT = -7
    NOT_AVAILABLE = -9


class ServoError(IntFlag):
    """
    Error Bits in Status Packet
    """

    INPUT_VOLTAGE = 1  # Bit 0
    ANGLE_LIMIT = 2  # Bit 1
    OVERHEATING = 4  # Bit 2
    RANGE = 8  # Bit 3
    CHECKSUM = 16  # Bit 4
    OVERLOAD = 32  # Bit 5
    INSTRUCTION = 64  # Bit 6


class Memory(IntEnum):
    # EPROM (Read Only)
    MODEL_L = 3
    MODEL_H = 4

    # EPROM (Read & Write)
    ID = 5
    BAUD_RATE = 6
    MIN_ANGLE_LIMIT_L = 9
    MIN_ANGLE_LIMIT_H = 10
    MAX_ANGLE_LIMIT_L = 11
    MAX_ANGLE_LIMIT_H = 12
    CW_DEAD = 26
    CCW_DEAD = 27

    # SRAM (Read & Write)
    TORQUE_ENABLE = 40
    ACC = 41
    GOAL_POSITION_L = 42
    GOAL_POSITION_H = 43
    GOAL_TIME_L = 44
    GOAL_TIME_H = 45
    GOAL_SPEED_L = 46
    GOAL_SPEED_H = 47
    LOCK = 48

    # SRAM (Read Only)
    PRESENT_POSITION_L = 56
    PRESENT_POSITION_H = 57
    PRESENT_SPEED_L = 58
    PRESENT_SPEED_H = 59
    PRESENT_LOAD_L = 60
    PRESENT_LOAD_H = 61
    PRESENT_VOLTAGE = 62
    PRESENT_TEMPERATURE = 63
    MOVING = 66
    PRESENT_CURRENT_L = 69
    PRESENT_CURRENT_H = 70


class Lock(IntEnum):
    UNLOCKED = 0
    LOCKED = 1


class TorqueEnable(IntEnum):
    OFF = 0
    ON = 1
