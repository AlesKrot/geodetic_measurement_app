from __future__ import annotations

from .horizontal_distance import EARTH_RADIUS_M


def refraction_correction(distance_m: float, refraction_coeff: float = 0.13) -> float:
    return refraction_coeff * (distance_m**2) / (2.0 * EARTH_RADIUS_M)
