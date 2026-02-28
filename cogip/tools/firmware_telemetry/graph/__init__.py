"""
Telemetry graph visualization package.

Provides configurable real-time telemetry visualization using PyQtGraph.
"""

from pathlib import Path

import yaml

from cogip.models.telemetry_graph import PlotConfig, TelemetryGraphConfig
from .bridge import TelemetryGraphBridge
from .telemetry_view import TelemetryView

__all__ = [
    "TelemetryView",
    "TelemetryGraphBridge",
    "TelemetryGraphConfig",
    "PlotConfig",
    "create_telemetry_graph",
]


def create_telemetry_graph(
    config_path: Path | str,
) -> tuple[TelemetryView, TelemetryGraphBridge]:
    """
    Factory function to create telemetry graph widget and bridge from YAML config.

    Args:
        config_path: Path to YAML configuration file.

    Returns:
        Tuple of (TelemetryView widget, TelemetryGraphBridge).

    Example:
        widget, bridge = create_telemetry_graph("config.yaml")
        telemetry_manager.sio_events.set_telemetry_callback(bridge.emit_telemetry)
        widget.show()
    """
    config_path = Path(config_path)

    with config_path.open() as f:
        config_data = yaml.safe_load(f)

    config = TelemetryGraphConfig.model_validate(config_data)
    widget = TelemetryView(config)
    bridge = TelemetryGraphBridge(widget)

    return widget, bridge
