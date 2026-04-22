from __future__ import annotations

import math

EARTH_RADIUS_M = 6_371_000.0


def horizontal_distance_from_slope(slope_distance_m: float, vertical_angle_deg: float) -> float:
    return slope_distance_m * math.cos(math.radians(vertical_angle_deg))


def curvature_correction(distance_m: float, refraction_coeff: float = 0.13) -> float:
    return -(1.0 - refraction_coeff) * (distance_m**2) / (2.0 * EARTH_RADIUS_M)
