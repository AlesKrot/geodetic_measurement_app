from __future__ import annotations


def atmospheric_correction(distance_m: float, temperature_c: float, pressure_hpa: float, humidity_percent: float) -> float:
    return distance_m * (
        ((pressure_hpa - 1013.25) * 1e-6)
        - ((temperature_c - 20.0) * 2e-6)
        + ((humidity_percent - 50.0) * 1e-6)
    )


def atmospheric_correction_from_wet_dry(
    distance_m: float,
    wavelength_nm: float,
    dry_temperature_c: float,
    wet_temperature_c: float,
    pressure_hpa: float,
) -> tuple[float, float, float, float]:
    def saturated_vapor_pressure_hpa(temp_c: float) -> float:
        # Tetens formula for saturation vapor pressure over water.
        return 6.112 * (10.0 ** ((7.5 * temp_c) / (237.3 + temp_c)))

    dry = dry_temperature_c
    wet = wet_temperature_c
    pressure = pressure_hpa

    es_wet = saturated_vapor_pressure_hpa(wet)
    es_dry = saturated_vapor_pressure_hpa(dry)
    psychrometric_coeff = 0.00066 * (1.0 + 0.00115 * wet)
    vapor_pressure = es_wet - psychrometric_coeff * pressure * (dry - wet)
    vapor_pressure = max(0.0, min(vapor_pressure, es_dry))
    humidity_percent = 100.0 * vapor_pressure / es_dry if es_dry > 0.0 else 0.0

    wavelength_um = max(0.2, wavelength_nm / 1000.0)
    reference_um = 0.633
    dispersion_factor = 1.0 + 0.005 * ((1.0 / (wavelength_um**2)) - (1.0 / (reference_um**2)))

    ppm = (
        (pressure - 1013.25)
        - (2.0 * (dry - 20.0))
        + (humidity_percent - 50.0)
    ) * dispersion_factor

    correction_m = distance_m * ppm * 1e-6
    correction_per_km_m = 1000.0 * ppm * 1e-6
    corrected_distance_m = distance_m + correction_m
    return correction_per_km_m, correction_m, corrected_distance_m, humidity_percent
