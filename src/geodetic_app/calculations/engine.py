from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from geodetic_app.calculations.atmospheric_corrections import atmospheric_correction
from geodetic_app.calculations.em_wave_refraction import refraction_correction
from geodetic_app.calculations.environmental_effects import apply_environmental_correction
from geodetic_app.calculations.horizontal_distance import curvature_correction, horizontal_distance_from_slope
from geodetic_app.models.measurement import EnvironmentConditions, MeasurementRecord


class CalculationEngine:
    def calculate(self, measurements: list[MeasurementRecord], environment: EnvironmentConditions) -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        for record in measurements:
            horizontal_distance_m = horizontal_distance_from_slope(record.slope_distance_m, record.vertical_angle_deg)
            curve_correction_m = curvature_correction(horizontal_distance_m)
            refraction_correction_m = refraction_correction(horizontal_distance_m)
            environmental_correction_m = apply_environmental_correction(
                horizontal_distance_m,
                environment.temperature_c,
                environment.pressure_hpa,
                environment.humidity_percent,
            )
            atmospheric_correction_m = atmospheric_correction(
                horizontal_distance_m,
                environment.temperature_c,
                environment.pressure_hpa,
                environment.humidity_percent,
            )
            corrected_distance_m = (
                horizontal_distance_m
                + curve_correction_m
                + refraction_correction_m
                + environmental_correction_m
                + atmospheric_correction_m
            )
            row = asdict(record)
            row.update(
                {
                    "horizontal_distance_m": horizontal_distance_m,
                    "curvature_correction_m": curve_correction_m,
                    "refraction_correction_m": refraction_correction_m,
                    "environmental_correction_m": environmental_correction_m,
                    "atmospheric_correction_m": atmospheric_correction_m,
                    "corrected_distance_m": corrected_distance_m,
                }
            )
            rows.append(row)
        return pd.DataFrame(rows)
