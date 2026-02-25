"""
Bridge between asyncio telemetry events and Qt graph widget.

Uses Qt signals to safely cross thread boundaries.
"""

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal as QtSignal
from PySide6.QtCore import Slot as QtSlot

from cogip.models.firmware_telemetry import TelemetryData

from .telemetry_view import TelemetryView


class TelemetryGraphBridge(QObject):
    """
    Bridge between asyncio telemetry events and Qt TelemetryView widget.

    Uses Qt signals to ensure thread-safe communication between
    the asyncio event loop and the Qt event loop.
    """

    # Signals for thread-safe communication
    signal_telemetry = QtSignal(object)  # TelemetryData
    signal_clear = QtSignal()
    signal_start_recording = QtSignal()
    signal_stop_recording = QtSignal()
    signal_load_plot = QtSignal(str)  # plot title to load

    def __init__(self, widget: TelemetryView):
        super().__init__()
        self._widget = widget

        # Connect signals to widget methods
        self.signal_telemetry.connect(self._on_telemetry)
        self.signal_clear.connect(self._on_clear)
        self.signal_start_recording.connect(self._on_start_recording)
        self.signal_stop_recording.connect(self._on_stop_recording)
        self.signal_load_plot.connect(self._on_load_plot)

    @QtSlot(object)
    def _on_telemetry(self, data: TelemetryData) -> None:
        """Handle telemetry data signal."""
        self._widget.update_telemetry(data)

    @QtSlot()
    def _on_clear(self) -> None:
        """Handle clear signal."""
        self._widget.clear()

    @QtSlot()
    def _on_start_recording(self) -> None:
        """Handle start recording signal."""
        self._widget.start_recording()

    @QtSlot()
    def _on_stop_recording(self) -> None:
        """Handle stop recording signal."""
        self._widget.stop_recording()

    @QtSlot(str)
    def _on_load_plot(self, title: str) -> None:
        """Handle load plot signal."""
        self._widget.load_plot(title)

    # Public methods called from asyncio context
    def emit_telemetry(self, data: TelemetryData) -> None:
        """Emit telemetry data to the graph (thread-safe)."""
        self.signal_telemetry.emit(data)

    def emit_clear(self) -> None:
        """Emit clear signal to reset curves (thread-safe)."""
        self.signal_clear.emit()

    def emit_start_recording(self) -> None:
        """Start recording telemetry data (thread-safe)."""
        self.signal_start_recording.emit()

    def emit_stop_recording(self) -> None:
        """Stop recording telemetry data (thread-safe)."""
        self.signal_stop_recording.emit()

    def emit_load_plot(self, title: str) -> None:
        """Load only the specified plot by title (thread-safe)."""
        self.signal_load_plot.emit(title)
