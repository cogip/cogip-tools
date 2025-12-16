"""
Firmware Telemetry Models.

This module provides models for parsing generic telemetry data received
from the robot's MCU firmware via Protobuf messages using FNV-1a key hashes.
"""

from pydantic import BaseModel, ConfigDict

from cogip.protobuf import PB_TelemetryData

# FNV-1a hash constants (32-bit)
FNV_OFFSET_BASIS = 0x811C9DC5
FNV_PRIME = 0x01000193


def fnv1a_hash(key: str) -> int:
    """
    Compute FNV-1a 32-bit hash of a string.

    This matches the firmware's hash implementation used for telemetry keys.

    Args:
        key: The string to hash.

    Returns:
        32-bit FNV-1a hash value.
    """
    hash_value = FNV_OFFSET_BASIS
    for char in key.encode("utf-8"):
        hash_value ^= char
        hash_value = (hash_value * FNV_PRIME) & 0xFFFFFFFF
    return hash_value

# Discriminated union of all firmware telemetry value types
TelemetryValue = (float| int)


class TelemetryData(BaseModel):
    """
    Generic telemetry data point with key hash, timestamp, and value.

    Attributes:
        key_hash: FNV-1a hash of the telemetry key.
        timestamp_ms: Timestamp in milliseconds when the data was captured.
        value: The telemetry value (float or int depending on type).
    """
    model_config = ConfigDict(validate_assignment=True)

    key_hash: int
    timestamp_ms: int
    value: TelemetryValue

    @classmethod
    def from_protobuf(cls, message: PB_TelemetryData) -> "TelemetryData":
        """
        Parse a TelemetryData from a PB_TelemetryData protobuf message.

        Args:
            message: The PB_TelemetryData protobuf message.

        Returns:
            TelemetryData instance with parsed values.
        """
        key_hash = message.key_hash
        timestamp_ms = message.timestamp_ms

        # Extract the value from the oneof field
        which_value = message.WhichOneof("value")
        if which_value is None:
            value: TelemetryValue = 0
        else:
            value = getattr(message, which_value)

        return cls(key_hash=key_hash, timestamp_ms=timestamp_ms, value=value)


class TelemetryStore:
    """
    Store for telemetry data points indexed by key hash.

    This class collects telemetry data and provides access by key name.
    """

    def __init__(self):
        self._data: dict[int, TelemetryData] = {}

    def update(self, data: TelemetryData) -> None:
        """
        Update the store with a new telemetry data point.

        Args:
            data: The telemetry data point to store.
        """
        self._data[data.key_hash] = data

    def get_by_hash(self, key_hash: int) -> TelemetryData | None:
        """
        Get telemetry data by key hash.

        Args:
            key_hash: The FNV-1a hash of the key.

        Returns:
            The telemetry data point, or None if not found.
        """
        return self._data.get(key_hash)

    def get_by_key(self, key: str) -> TelemetryData | None:
        """
        Get telemetry data by key name.

        Args:
            key: The telemetry key name.

        Returns:
            The telemetry data point, or None if not found.
        """
        return self.get_by_hash(fnv1a_hash(key))

    def get_value(self, key: str, default: TelemetryValue = 0) -> TelemetryValue:
        """
        Get the value for a telemetry key.

        Args:
            key: The telemetry key name.
            default: Default value if key not found.

        Returns:
            The telemetry value, or default if not found.
        """
        data = self.get_by_key(key)
        return data.value if data else default
