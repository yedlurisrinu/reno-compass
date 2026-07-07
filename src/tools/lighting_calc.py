"""Lighting calculator tool.

This module computes recommended window areas for natural lighting and calculated
artificial lighting output targets (lumens, fixture counts) per IES guidelines.
"""

import logging
from typing import Any

logger = logging.getLogger("reno_project")


def calculate_lighting_requirements(
    room_area_sqft: float,
    ceiling_height_ft: float,
    vanity_count: int = 1,
    shower_present: bool = True,
    wall_reflectivity: str = "neutral",
) -> dict[str, Any]:
    """Calculates footcandle/lumen targets and recommended fixtures.

    Enforces IES Curation target math (SI-18 / RD-4):
    * Ambient general zone: 30 fc
    * Vanity grooming task zone: 80 fc (assumes 10 sqft per vanity mirror)
    * Shower wet task zone: 30 fc (assumes 15 sqft shower zone)
    * Scaling: scale lumens by (ceiling_height / 8.0)
    * Wall color reflection modifiers: dark/matte +15%, light/white -15%
    * Recommended natural window area: 8% of room area (min 3 sqft)

    Args:
        room_area_sqft: Total floor area of the bathroom.
        ceiling_height_ft: Ceiling height in feet.
        vanity_count: Number of separate vanity stations.
        shower_present: True if a wet shower/tub area exists.
        wall_reflectivity: "light", "white", "dark", "matte", or "neutral".

    Returns:
        Dict of results containing:
            'required_natural_lumens': float,
            'recommended_window_area': float,
            'required_artificial_lumens': float,
            'required_fixture_count': float
    """
    logger.debug(
        f"Calculating lighting requirements: area={room_area_sqft} sqft, height={ceiling_height_ft} ft, "
        f"vanities={vanity_count}, shower={shower_present}, reflectivity={wall_reflectivity}"
    )

    # Calculate zone breakdowns
    vanity_area = 10.0 * vanity_count
    shower_area = 15.0 if shower_present else 0.0

    # Ambient area takes the remaining footprint
    ambient_area = max(0.0, room_area_sqft - vanity_area - shower_area)

    # Base lumens per zone
    ambient_lumens = ambient_area * 30.0
    vanity_lumens = vanity_area * 80.0
    shower_lumens = shower_area * 30.0

    base_lumens = ambient_lumens + vanity_lumens + shower_lumens

    # Height scaling factor (normalized to 8.0 ft ceiling)
    height_scale = ceiling_height_ft / 8.0

    # Reflectivity adjustment
    reflectivity = wall_reflectivity.lower().strip()
    if reflectivity in ("dark", "matte"):
        reflectivity_mult = 1.15
    elif reflectivity in ("light", "white"):
        reflectivity_mult = 0.85
    else:
        reflectivity_mult = 1.0

    logger.debug(
        f"Lighting calculations base values: base_lumens={base_lumens:.2f}, "
        f"height_scale={height_scale:.4f}, reflectivity_mult={reflectivity_mult:.2f}"
    )

    # Calculate final artificial lumens
    required_art_lumens = base_lumens * height_scale * reflectivity_mult

    # Fixture count target (assuming standard 800 lm LED downlight/sconce bulb)
    required_fixtures = max(1.0, round(required_art_lumens / 800.0, 1))

    # Natural light computations (standard 8% glazing recommendation)
    recommended_window = max(3.0, round(room_area_sqft * 0.08, 1))
    required_nat_lumens = room_area_sqft * 30.0

    logger.info(
        f"Lighting calculations complete: art_lumens={required_art_lumens:.2f}, "
        f"fixtures={required_fixtures}, recommended_window={recommended_window} sqft"
    )

    return {
        "required_natural_lumens": round(required_nat_lumens, 2),
        "recommended_window_area": round(recommended_window, 2),
        "required_artificial_lumens": round(required_art_lumens, 2),
        "required_fixture_count": required_fixtures,
    }
