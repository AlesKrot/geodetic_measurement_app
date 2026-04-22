from __future__ import annotations

from pathlib import Path

from geodetic_app.calculations.engine import CalculationEngine
from geodetic_app.exports.exporters import export_csv, export_json
from geodetic_app.models.measurement import EnvironmentConditions, MeasurementRecord


def test_pipeline_exports(tmp_path: Path) -> None:
    engine = CalculationEngine()
    frame = engine.calculate(
        [MeasurementRecord(sample_id="a", slope_distance_m=12.5, vertical_angle_deg=0.2)],
        EnvironmentConditions(),
    )

    csv_path = export_csv(frame, tmp_path / "results.csv")
    json_path = export_json(frame, tmp_path / "results.json")

    assert csv_path.exists()
    assert json_path.exists()
