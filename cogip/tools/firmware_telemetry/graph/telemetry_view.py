"""
Real-time telemetry visualization widget using PyQtGraph.

Configurable layout via YAML configuration file.
"""

from collections import deque

import pyqtgraph as pg
from PySide6.QtWidgets import QVBoxLayout, QWidget

from cogip.models.firmware_telemetry import TelemetryData
from cogip.models.telemetry_graph import TelemetryGraphConfig
from cogip.utils.fnv1a import fnv1a_hash

type Color = tuple[int, int, int]
type DataStorage = dict[str, tuple[deque[float], deque[float]]]


class TelemetryView(QWidget):
    """
    Real-time telemetry graph widget using PyQtGraph.

    Features:
    - Configurable grid layout (row/col)
    - Automatic color assignment
    - Automatic Y-axis scaling
    - Time-based pruning (retention_seconds)
    - Memory-limited data storage (max_points)
    """

    DEFAULT_COLORS: list[Color] = [
        (31, 119, 180),  # Blue
        (255, 127, 14),  # Orange
        (44, 160, 44),  # Green
        (214, 39, 40),  # Red
        (148, 103, 189),  # Purple
        (140, 86, 75),  # Brown
        (227, 119, 194),  # Pink
        (127, 127, 127),  # Gray
        (188, 189, 34),  # Olive
        (23, 190, 207),  # Cyan
    ]

    def __init__(self, config: TelemetryGraphConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self._config = config
        self._recording = False
        self._start_time_ms: int | None = None
        self._update_counter = 0

        # Data storage: key -> (times deque, values deque)
        self._data: DataStorage = {}

        # Curves: key -> PlotDataItem
        self._curves: dict[str, pg.PlotDataItem] = {}

        # Plots: title -> PlotItem
        self._plots: dict[str, pg.PlotItem] = {}

        # Key hash mapping: hash -> key name
        self._key_hashes: dict[int, str] = {}

        # Color assignment: key -> color tuple
        self._colors: dict[str, Color] = {}

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configure the Qt layout with PyQtGraph plots."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        # Configure pyqtgraph dark theme
        pg.setConfigOption("background", "#1E1E1E")
        pg.setConfigOption("foreground", "#CCCCCC")

        # Create graphics layout widget
        self._graph_layout = pg.GraphicsLayoutWidget()
        layout.addWidget(self._graph_layout)

        self._build_plots()

        # Set window properties
        self.setWindowTitle("Telemetry View")
        self.setMinimumSize(900, 700)

    def _build_plots(self) -> None:
        """Build plots from current config."""
        # Assign colors to all keys
        self._assign_colors()

        # Create plots from config
        for plot_config in self._config.plots:
            plot = self._graph_layout.addPlot(
                row=plot_config.row,
                col=plot_config.col,
                rowspan=plot_config.rowspan,
                colspan=plot_config.colspan,
                title=plot_config.title,
            )
            y_label = f"Value ({plot_config.y_unit})" if plot_config.y_unit else "Value"
            plot.setLabel("left", y_label)
            plot.setLabel("bottom", "Time (ms)")
            plot.addLegend(offset=(10, 10))
            plot.showGrid(x=True, y=True, alpha=0.3)

            self._plots[plot_config.title] = plot

            # Create curves for each key in this plot
            for key in plot_config.keys:
                color = self._colors[key]
                curve = plot.plot(
                    pen=pg.mkPen(color=color, width=2),
                    symbol="o",
                    symbolSize=5,
                    symbolBrush=color,
                    name=key,
                )
                self._curves[key] = curve

                # Initialize data storage
                self._data[key] = (
                    deque(maxlen=self._config.max_points),
                    deque(maxlen=self._config.max_points),
                )

                # Map key hash to key name
                self._key_hashes[fnv1a_hash(key)] = key

    def load_config(self, config: TelemetryGraphConfig) -> None:
        """Load a new configuration, rebuilding all plots."""
        self._config = config
        self._recording = False
        self._start_time_ms = None
        self._update_counter = 0

        # Clear existing state
        self._data.clear()
        self._curves.clear()
        self._plots.clear()
        self._key_hashes.clear()
        self._colors.clear()

        # Clear the graphics layout and rebuild
        self._graph_layout.clear()
        self._build_plots()

    def _assign_colors(self) -> None:
        """Assign colors to all telemetry keys."""
        color_idx = 0
        for plot_config in self._config.plots:
            for key in plot_config.keys:
                if key not in self._colors:
                    self._colors[key] = self.DEFAULT_COLORS[color_idx % len(self.DEFAULT_COLORS)]
                    color_idx += 1

    def start_recording(self) -> None:
        """Start recording telemetry data."""
        self._recording = True
        self._start_time_ms = None

    def stop_recording(self) -> None:
        """Stop recording telemetry data."""
        self._recording = False

    def clear(self) -> None:
        """Clear all curves and reset state."""
        self._start_time_ms = None
        self._recording = False
        self._update_counter = 0

        for times, values in self._data.values():
            times.clear()
            values.clear()

        for curve in self._curves.values():
            curve.setData([], [])

    def update_telemetry(self, data: TelemetryData) -> None:
        """
        Process incoming telemetry data and update curves.

        Args:
            data: TelemetryData from firmware
        """
        if not self._recording:
            return

        # Check if this key is tracked
        key = self._key_hashes.get(data.key_hash)
        if key is None:
            return

        # Initialize start time on first data point
        if self._start_time_ms is None:
            self._start_time_ms = data.timestamp_ms

        # Calculate relative time
        relative_time = data.timestamp_ms - self._start_time_ms

        # Append data
        times, values = self._data[key]
        times.append(relative_time)
        values.append(data.value)

        # Update curve
        self._curves[key].setData(list(times), list(values))

        # Periodic pruning
        self._update_counter += 1
        if self._update_counter % self._config.prune_interval == 0:
            self._prune_old_data(relative_time)

    def _prune_old_data(self, current_time_ms: float) -> None:
        """Remove data older than retention_seconds."""
        cutoff_ms = current_time_ms - (self._config.retention_seconds * 1000)

        for key, (times, values) in self._data.items():
            # Remove old data points
            while times and times[0] < cutoff_ms:
                times.popleft()
                values.popleft()

            # Update curve
            curve = self._curves.get(key)
            if curve:
                curve.setData(list(times), list(values))
