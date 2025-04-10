from pydantic import BaseModel, ConfigDict, Field


class Properties(BaseModel):
    model_config = ConfigDict(title="Detector Properties")

    min_distance: int = Field(
        ...,
        ge=0,
        le=1000,
        title="Min Distance",
        description="Minimum distance to detect an obstacle (mm)",
    )
    max_distance: int = Field(
        ...,
        ge=0,
        le=4000,
        title="Max Distance",
        description="Maximum distance to detect an obstacle (mm)",
    )
    min_intensity: int = Field(
        ...,
        ge=0,
        le=255,
        title="Min intensity",
        description="Minimum intensity to detect an obstacle",
    )
    refresh_interval: float = Field(
        ...,
        ge=-1.0,
        le=2.0,
        multiple_of=0.01,
        title="Refresh Interval",
        description="Interval between each update of the obstacle list (seconds)",
    )
    sensor_delay: int = Field(
        ...,
        ge=0,
        le=100,
        title="Sensor Delay",
        description=(
            "Delay to compensate the delay between sensor data fetch and obstacle positions computation,"
            "unit is the index of pose current to get in the past"
        ),
    )
    cluster_min_samples: int = Field(
        ...,
        ge=1,
        le=20,
        title="Cluster Min Samples",
        description="Minimum number of samples to form a cluster",
    )
    cluster_eps: float = Field(
        ...,
        ge=1.0,
        le=100.0,
        multiple_of=1.0,
        title="Cluster Epsilon",
        description="Maximum distance between two samples to form a cluster (mm)",
    )
