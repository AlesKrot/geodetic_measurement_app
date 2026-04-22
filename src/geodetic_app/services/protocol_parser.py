from __future__ import annotations

from dataclasses import dataclass

from geodetic_app.models.measurement import MeasurementRecord


@dataclass(slots=True)
class ParsedPacket:
    sample_id: str
    slope_distance_m: float
    vertical_angle_deg: float = 0.0


class ProtocolParser:
    def parse(self, payload: dict[str, object]) -> MeasurementRecord:
        return MeasurementRecord(
            sample_id=str(payload.get("sample_id", "sample-1")),
            slope_distance_m=float(payload.get("slope_distance_m", 0.0)),
            vertical_angle_deg=float(payload.get("vertical_angle_deg", 0.0)),
            temperature_c=float(payload.get("temperature_c", 20.0)),
            pressure_hpa=float(payload.get("pressure_hpa", 1013.25)),
            humidity_percent=float(payload.get("humidity_percent", 50.0)),
        )
