import socketio

from cogip.models import TelemetryData, TelemetryDict
from .sio_events import SioEvents


class FirmwareTelemetryManager:
    """
    Manager to receive firmware telemetry data via SocketIO through copilot.

    This class is designed to be embedded into another Socket.IO client (e.g., Planner,
    Monitor, Calibration tool, or any tool that needs firmware telemetry access). It registers
    its own namespace (/telemetry) on the provided client, allowing the host tool to manage
    the connection lifecycle while benefiting from telemetry data reception.

    Telemetry data is stored in a TelemetryDict and can be accessed by key name or hash.

    Note on concurrent usage: Multiple clients can receive telemetry data simultaneously
    as the server broadcasts to all connected clients. However, having multiple consumers
    may lead to debugging complexity. Prefer having a single client handle telemetry at a time.
    """

    def __init__(
        self,
        sio: socketio.AsyncClient,
    ):
        """
        Initialize the FirmwareTelemetryManager.

        Args:
            sio: External Socket.IO client on which to register the /telemetry namespace.
                 The host client is responsible for connection management.
        """
        self.sio = sio
        self.data = TelemetryDict()

        self.sio_events = SioEvents(self)
        self.sio.register_namespace(self.sio_events)

    @property
    def namespace(self) -> str:
        """Return the namespace path to include when connecting the host client."""
        return self.sio_events.namespace

    @property
    def is_connected(self) -> bool:
        """Check if the namespace is connected and ready."""
        return self.sio_events.connected

    async def enable(self) -> None:
        """
        Enable telemetry on the firmware.
        Sends telemetry_enable event to copilot via the server.
        """
        await self.sio.emit("telemetry_enable", namespace="/telemetry")

    async def disable(self) -> None:
        """
        Disable telemetry on the firmware.
        Sends telemetry_disable event to copilot via the server.
        """
        await self.sio.emit("telemetry_disable", namespace="/telemetry")

    def get_value(self, key: str, default: float | int = 0) -> float | int:
        """
        Get the latest telemetry value for a key.

        Args:
            key: The telemetry key name.
            default: Default value if key not found.

        Returns:
            The telemetry value, or default if not found.
        """
        if key in self.data:
            return self.data[key]
        return default

    def get_model(self, key: str) -> TelemetryData:
        """
        Get the full telemetry data model for a key.

        Args:
            key: The telemetry key name.

        Returns:
            TelemetryData containing key_hash, timestamp_ms, and value.

        Raises:
            KeyError: If the key is not found in the store.
        """
        return self.data.get_model(key)
