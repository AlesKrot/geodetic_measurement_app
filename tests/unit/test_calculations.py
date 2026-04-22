from __future__ import annotations

import math

import pandas as pd

from geodetic_app.calculations.engine import CalculationEngine
from geodetic_app.calculations.horizontal_distance import horizontal_distance_from_slope
from geodetic_app.models.measurement import EnvironmentConditions, MeasurementRecord


def test_horizontal_distance_from_slope() -> None:
    assert math.isclose(horizontal_distance_from_slope(10.0, 60.0), 5.0, rel_tol=1e-12)


def test_calculation_engine_returns_dataframe() -> None:
    engine = CalculationEngine()
    frame = engine.calculate(
        [MeasurementRecord(sample_id="a", slope_distance_m=10.0, vertical_angle_deg=0.0)],
        EnvironmentConditions(),
    )
    assert isinstance(frame, pd.DataFrame)
    assert "corrected_distance_m" in frame.columns
    assert len(frame) == 1
