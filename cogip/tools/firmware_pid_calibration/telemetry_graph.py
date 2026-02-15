"""
Real-time telemetry visualization using pyqtgraph.

Displays telemetry curves for PID calibration analysis.
Two graphs: one for linear, one for angular.
"""

from collections import deque

import pyqtgraph as pg
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal as QtSignal
from PySide6.QtCore import Slot as QtSlot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from cogip.models.firmware_telemetry import TelemetryData, fnv1a_hash
from .types import PidType, TelemetryType


class TelemetryGraphWidget(QWidget):
    """
    Real-time telemetry graph widget using pyqtgraph.

    Features:
    - Two plots: Position and Speed
    - Curves filtered by PID type (linear vs angular)
    - Time-based X axis (relative to iteration start)
    - Clear/reset between iterations
    - Dark theme
    """

    # Colors for different telemetry curves
    CURVE_COLORS = {
        # Linear
        TelemetryType.LINEAR_SPEED_ORDER: "#f1c40f",  # Yellow - setpoint
        TelemetryType.LINEAR_CURRENT_SPEED: "#2ecc71",  # Green - actual speed
        TelemetryType.LINEAR_TRACKER_VELOCITY: "#9b59b6",  # Purple - tracker
        TelemetryType.LINEAR_SPEED_COMMAND: "#e74c3c",  # Red - command to motors
        # Angular
        TelemetryType.ANGULAR_SPEED_ORDER: "#f1c40f",  # Yellow - setpoint
        TelemetryType.ANGULAR_CURRENT_SPEED: "#2ecc71",  # Green - actual speed
        TelemetryType.ANGULAR_TRACKER_VELOCITY: "#9b59b6",  # Purple - tracker
        TelemetryType.ANGULAR_SPEED_COMMAND: "#e74c3c",  # Red - command to motors
    }

    MAX_POINTS = 2000  # Maximum data points per curve

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("PID Calibration - Telemetry")
        self.setMinimumSize(900, 700)

        self._key_hashes: dict[int, TelemetryType] = {}
        self._iteration_start_ms: int | None = None
        self._recording = False  # Only record when robot is moving

        # Data storage for displayed telemetry types
        self._data: dict[TelemetryType, tuple[deque, deque]] = {}

        self._setup_ui()
        self._setup_all_curves()

    def _setup_ui(self) -> None:
        """Configure the Qt layout with two plot widgets (linear and angular)."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Configure pyqtgraph dark theme
        pg.setConfigOption("background", "#1E1E1E")
        pg.setConfigOption("foreground", "#CCCCCC")

        # Linear plot
        self._linear_plot = pg.PlotWidget(title="Linear PID")
        self._linear_plot.setLabel("left", "Value")
        self._linear_plot.setLabel("bottom", "Time", units="ms")
        self._linear_plot.addLegend(offset=(10, 10))
        self._linear_plot.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self._linear_plot)

        # Angular plot
        self._angular_plot = pg.PlotWidget(title="Angular PID")
        self._angular_plot.setLabel("left", "Value")
        self._angular_plot.setLabel("bottom", "Time", units="ms")
        self._angular_plot.addLegend(offset=(10, 10))
        self._angular_plot.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self._angular_plot)

    # Telemetry types to display
    LINEAR_TYPES = [
        TelemetryType.LINEAR_SPEED_ORDER,
        TelemetryType.LINEAR_CURRENT_SPEED,
        TelemetryType.LINEAR_TRACKER_VELOCITY,
        TelemetryType.LINEAR_SPEED_COMMAND,
    ]
    ANGULAR_TYPES = [
        TelemetryType.ANGULAR_SPEED_ORDER,
        TelemetryType.ANGULAR_CURRENT_SPEED,
        TelemetryType.ANGULAR_TRACKER_VELOCITY,
        TelemetryType.ANGULAR_SPEED_COMMAND,
    ]

    def _setup_all_curves(self) -> None:
        """Create all curves on their respective plots."""
        self._curves: dict[TelemetryType, pg.PlotDataItem] = {}
        all_types = self.LINEAR_TYPES + self.ANGULAR_TYPES

        # Initialize data storage
        for ttype in all_types:
            self._data[ttype] = (deque(maxlen=self.MAX_POINTS), deque(maxlen=self.MAX_POINTS))

        # Linear curves
        for ttype in self.LINEAR_TYPES:
            color = self.CURVE_COLORS.get(ttype, "#FFFFFF")
            curve = self._linear_plot.plot(pen=pg.mkPen(color=color, width=2), name=ttype.label)
            self._curves[ttype] = curve

        # Angular curves
        for ttype in self.ANGULAR_TYPES:
            color = self.CURVE_COLORS.get(ttype, "#FFFFFF")
            curve = self._angular_plot.plot(pen=pg.mkPen(color=color, width=2), name=ttype.label)
            self._curves[ttype] = curve

        # Build key hashes for all displayed types
        self._key_hashes = {fnv1a_hash(t.telemetry_key): t for t in all_types}

    def set_pid_type(self, pid_type: PidType) -> None:
        """
        Called when PID type is selected.
        Both linear and angular plots are always visible.

        Args:
            pid_type: The selected PID type
        """
        # All curves are always visible, nothing to do
        pass

    def clear_curves(self) -> None:
        """Clear all curves and reset iteration timestamp."""
        self._iteration_start_ms = None
        self._recording = False
        for time_data, value_data in self._data.values():
            time_data.clear()
            value_data.clear()
        for curve in self._curves.values():
            curve.setData([], [])

    def start_recording(self) -> None:
        """Start recording telemetry data."""
        self._recording = True

    def stop_recording(self) -> None:
        """Stop recording telemetry data."""
        self._recording = False

    def update_telemetry(self, data: TelemetryData) -> None:
        """
        Process incoming telemetry data and update curves.

        Args:
            data: TelemetryData from firmware
        """
        # Only record when robot is moving
        if not self._recording:
            return

        # Check if this is a tracked telemetry type
        telemetry_type = self._key_hashes.get(data.key_hash)
        if telemetry_type is None:
            return

        # Initialize start time on first data point
        if self._iteration_start_ms is None:
            self._iteration_start_ms = data.timestamp_ms

        # Calculate relative time
        relative_time = data.timestamp_ms - self._iteration_start_ms

        # Append data
        time_data, value_data = self._data[telemetry_type]
        time_data.append(relative_time)
        value_data.append(data.value)

        # Update curve
        self._curves[telemetry_type].setData(list(time_data), list(value_data))


class TelemetryGraphBridge(QObject):
    """
    Bridge between asyncio telemetry events and Qt graph widget.

    Uses Qt signals to safely cross thread boundaries (though with qasync,
    we're in the same thread, signals still ensure proper event queue handling).
    """

    # Signals for thread-safe communication
    signal_telemetry = QtSignal(object)  # TelemetryData
    signal_clear = QtSignal()
    signal_set_pid_type = QtSignal(object)  # PidType
    signal_start_recording = QtSignal()
    signal_stop_recording = QtSignal()

    def __init__(self, widget: TelemetryGraphWidget):
        super().__init__()
        self._widget = widget

        # Connect signals to widget methods
        self.signal_telemetry.connect(self._on_telemetry)
        self.signal_clear.connect(self._on_clear)
        self.signal_set_pid_type.connect(self._on_set_pid_type)
        self.signal_start_recording.connect(self._on_start_recording)
        self.signal_stop_recording.connect(self._on_stop_recording)

    @QtSlot(object)
    def _on_telemetry(self, data: TelemetryData) -> None:
        """Handle telemetry data signal."""
        self._widget.update_telemetry(data)

    @QtSlot()
    def _on_clear(self) -> None:
        """Handle clear signal."""
        self._widget.clear_curves()

    @QtSlot(object)
    def _on_set_pid_type(self, pid_type: PidType) -> None:
        """Handle PID type selection signal."""
        self._widget.set_pid_type(pid_type)

    @QtSlot()
    def _on_start_recording(self) -> None:
        """Handle start recording signal."""
        self._widget.start_recording()

    @QtSlot()
    def _on_stop_recording(self) -> None:
        """Handle stop recording signal."""
        self._widget.stop_recording()

    # Public methods called from asyncio context
    def emit_telemetry(self, data: TelemetryData) -> None:
        """Emit telemetry data to the graph (thread-safe)."""
        self.signal_telemetry.emit(data)

    def emit_clear(self) -> None:
        """Emit clear signal to reset curves (thread-safe)."""
        self.signal_clear.emit()

    def emit_set_pid_type(self, pid_type: PidType) -> None:
        """Emit PID type to configure displayed curves (thread-safe)."""
        self.signal_set_pid_type.emit(pid_type)

    def emit_start_recording(self) -> None:
        """Start recording telemetry data (thread-safe)."""
        self.signal_start_recording.emit()

    def emit_stop_recording(self) -> None:
        """Stop recording telemetry data (thread-safe)."""
        self.signal_stop_recording.emit()
