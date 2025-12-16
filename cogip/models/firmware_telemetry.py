"""
Firmware Telemetry Models.

This module provides models for parsing generic telemetry data received
from the robot's MCU firmware via Protobuf messages using FNV-1a key hashes.
"""

from pydantic import BaseModel, ConfigDict

from cogip.protobuf import PB_TelemetryData
from cogip.utils.fnv1a import fnv1a_hash

# Discriminated union of all firmware telemetry value types
TelemetryValue = float | int


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


class TelemetryDict:
    """
    Dict-like store for telemetry data points indexed by key hash.

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

    def get_model(self, key: str) -> TelemetryData:
        """
        Get telemetry data model by key name.

        Args:
            key: The telemetry key name to look up.

        Returns:
            TelemetryData for the key.

        Raises:
            KeyError: If the key is not found in the store.
        """
        return self._data[fnv1a_hash(key)]

    def __getitem__(self, key: str) -> TelemetryValue:
        """
        Get telemetry value by key name. Raises KeyError if not found.

        Args:
            key: The telemetry key name to look up.

        Returns:
            The telemetry value for the key.

        Raises:
            KeyError: If the key is not found in the store.
        """
        return self._data[fnv1a_hash(key)].value

    def __contains__(self, key: str) -> bool:
        """
        Check if a key exists in the store.

        Args:
            key: The telemetry key name to check.

        Returns:
            True if the key exists, False otherwise.
        """
        return fnv1a_hash(key) in self._data

    def __len__(self) -> int:
        """Return the number of telemetry entries."""
        return len(self._data)

    def __bool__(self) -> bool:
        """Return True if the store contains any data."""
        return bool(self._data)

    def items(self):
        """Iterate over (key_hash, TelemetryData) tuples."""
        return self._data.items()

    def values(self):
        """Iterate over TelemetryData values."""
        return self._data.values()
