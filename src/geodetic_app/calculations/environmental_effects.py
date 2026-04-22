from __future__ import annotations


def environmental_scale_factor(temperature_c: float, pressure_hpa: float, humidity_percent: float) -> float:
    temperature_term = 1.0 + ((temperature_c - 20.0) * 0.0001)
    pressure_term = 1.0 + ((pressure_hpa - 1013.25) * -0.00001)
    humidity_term = 1.0 + ((humidity_percent - 50.0) * 0.00002)
    return temperature_term * pressure_term * humidity_term


def apply_environmental_correction(
    distance_m: float,
    temperature_c: float,
    pressure_hpa: float,
    humidity_percent: float,
) -> float:
    return distance_m * environmental_scale_factor(temperature_c, pressure_hpa, humidity_percent) - distance_m
