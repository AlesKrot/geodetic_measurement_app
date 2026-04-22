from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .device_config import DeviceConfig
from .measurement import EnvironmentConditions, MeasurementRecord


@dataclass(slots=True)
class AppState:
    device_config: DeviceConfig = field(default_factory=DeviceConfig)
    environment: EnvironmentConditions = field(default_factory=EnvironmentConditions)
    measurements: list[MeasurementRecord] = field(default_factory=list)
    results: pd.DataFrame | None = None
    connection_status: str = "disconnected"
    logs: list[str] = field(default_factory=list)
