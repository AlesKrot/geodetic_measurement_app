from __future__ import annotations

import math

import pandas as pd

from geodetic_app.calculations.atmospheric_corrections import atmospheric_correction_from_wet_dry
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


def test_atmospheric_correction_from_wet_dry_matches_15c_reference_close_to_10_95() -> None:
    correction_per_km_m, correction_m, corrected_distance_m, humidity_percent = atmospheric_correction_from_wet_dry(
        distance_m=1000.0,
        wavelength_nm=633.0,
        dry_temperature_c=22.25,
        wet_temperature_c=13.25,
        pressure_hpa=998.5,
    )

    assert math.isclose(correction_per_km_m * 1000.0, 10.916, rel_tol=1e-4)
    assert math.isclose(correction_m * 1000.0, 10.916, rel_tol=1e-4)
    assert math.isclose(corrected_distance_m, 1000.010916, rel_tol=1e-6)
    assert math.isclose(humidity_percent, 34.2965815, rel_tol=1e-6)
