"""
Pydantic models for telemetry graph configuration.

Configuration is loaded from YAML files to define the layout
and behavior of real-time telemetry visualization.
"""

from pydantic import BaseModel, Field


class PlotConfig(BaseModel):
    """Configuration for a single plot in the telemetry graph."""

    title: str
    row: int
    col: int
    keys: list[str]
    y_unit: str = ""
    rowspan: int = 1
    colspan: int = 1


class TelemetryGraphConfig(BaseModel):
    """
    Complete configuration for the telemetry graph widget.

    Attributes:
        plots: List of plot configurations defining the layout.
        max_points: Maximum data points per curve before pruning.
        retention_seconds: Time window for data retention.
        update_interval_ms: Graph update interval in milliseconds.
        prune_interval: Prune old data every N updates.
    """

    plots: list[PlotConfig]
    max_points: int = Field(default=2000, ge=100, le=10000)
    retention_seconds: float = Field(default=60.0, ge=1.0, le=600.0)
    update_interval_ms: int = Field(default=33, ge=16, le=200)
    prune_interval: int = Field(default=30, ge=1)
