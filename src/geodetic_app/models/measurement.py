from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class MeasurementRecord:
    sample_id: str
    slope_distance_m: float
    vertical_angle_deg: float = 0.0
    temperature_c: float = 20.0
    pressure_hpa: float = 1013.25
    humidity_percent: float = 50.0
    target_height_m: float = 0.0
    instrument_height_m: float = 0.0
    quality_flag: str = "ok"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class EnvironmentConditions:
    temperature_c: float = 20.0
    pressure_hpa: float = 1013.25
    humidity_percent: float = 50.0
