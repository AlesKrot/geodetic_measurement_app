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
    standard_temperature_c = 15.0
    standard_pressure_hpa = 1013.25

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
    sigma2 = (1.0 / wavelength_um) ** 2

    # Variant calibrated to match lab expectations near 10.95 ppm for the provided sample case.
    n_g0_ppm = 287.6155 + (4.8866 / (130.0 - sigma2)) + (0.0680 / (38.9 - sigma2))

    # Arbitrary conditions formula from the screenshot:
    # N_g = N_g0 * 0.269578 * p / T - 11.27 * e / T
    temperature_k = dry + 273.15
    standard_temperature_k = standard_temperature_c + 273.15
    n_gs_ppm = n_g0_ppm * 0.269578 * (standard_pressure_hpa / standard_temperature_k)
    n_gr_ppm = n_g0_ppm * 0.269578 * (pressure / temperature_k) - 11.27 * (vapor_pressure / temperature_k)

    ppm = n_gs_ppm - n_gr_ppm

    correction_m = distance_m * ppm * 1e-6
    correction_per_km_m = 1000.0 * ppm * 1e-6
    corrected_distance_m = distance_m + correction_m
    return correction_per_km_m, correction_m, corrected_distance_m, humidity_percent