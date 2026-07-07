"""Measurement mathematics and dimension validation tool.

This module provides functions for calculating area/volume and validating
spatial dimensions, raising errors for implausible inputs (e.g. 40ftx40ft rooms).
"""

import logging

logger = logging.getLogger("reno_project")


class ImplausibleMeasurementError(ValueError):
    """Custom exception raised when a dimension is physically implausible for a bathroom."""

    pass


def convert_to_feet(value: float, unit: str) -> float:
    """Converts a dimension value from its native unit to feet.

    Args:
        value: The dimension magnitude.
        unit: Unit string ('ft', 'in', 'cm').

    Returns:
        Converted value in feet.
    """
    u_lower = unit.lower().strip()
    if u_lower in ("ft", "feet"):
        res = value
    elif u_lower in ("in", "inch", "inches"):
        res = value / 12.0
    elif u_lower in ("cm", "centimeter", "centimeters"):
        res = value / 30.48
    else:
        logger.error(f"Unit conversion failed: unsupported unit '{unit}'")
        raise ValueError(f"Unsupported measurement unit: {unit}")

    logger.debug(f"Converted unit: {value} {unit} -> {res:.4f} ft")
    return res


def validate_room_dimensions(length: float, width: float, height: float, unit: str) -> None:
    """Checks if room dimensions are realistic.

    Rules (SI-3):
    * Length or Width >= 40 ft -> Implausible.
    * Ceiling Height <= 6 inches (0.5 ft) -> Implausible.
    * Ceiling Height >= 20 ft -> Implausible for standard home.
    * Any dimension <= 0 -> Implausible.

    Args:
        length: Room length.
        width: Room width.
        height: Room ceiling height.
        unit: Measurement unit ('ft', 'in', 'cm').
    """
    logger.debug(
        f"Validating room dimensions: length={length}, width={width}, height={height}, unit={unit}"
    )
    try:
        l_ft = convert_to_feet(length, unit)
        w_ft = convert_to_feet(width, unit)
        h_ft = convert_to_feet(height, unit)
    except ValueError as exc:
        logger.warning(f"Validation failed due to conversion error: {exc}")
        raise ImplausibleMeasurementError(str(exc)) from exc

    if l_ft <= 0 or w_ft <= 0 or h_ft <= 0:
        logger.warning(
            f"Validation failed: dimensions must be positive values (got length={l_ft}ft, width={w_ft}ft, height={h_ft}ft)."
        )
        raise ImplausibleMeasurementError("Dimensions must be positive values greater than zero.")

    if l_ft >= 40.0 or w_ft >= 40.0:
        msg = f"Room footprint dimensions are implausibly large ({length}x{width} {unit}). Max allowed is 40 ft."
        logger.warning(f"Validation failed: {msg}")
        raise ImplausibleMeasurementError(msg)

    if h_ft <= 0.5:
        msg = f"Ceiling height is implausibly low ({height} {unit}). Min allowed is 6 inches (0.5 ft)."
        logger.warning(f"Validation failed: {msg}")
        raise ImplausibleMeasurementError(msg)

    if h_ft >= 20.0:
        msg = f"Ceiling height is implausibly high ({height} {unit}). Max allowed is 20 ft."
        logger.warning(f"Validation failed: {msg}")
        raise ImplausibleMeasurementError(msg)

    logger.debug("Room dimensions successfully validated.")


def calculate_area_and_volume(
    length: float, width: float, height: float, unit: str
) -> dict[str, float]:
    """Calculates floor area and volume in feet units after running validation.

    Args:
        length: Room length.
        width: Room width.
        height: Room ceiling height.
        unit: Measurement unit.

    Returns:
        Dict containing:
            'area_sqft': Calculated floor area.
            'volume_cuft': Calculated volume.
    """
    logger.info(
        f"Calculating area and volume for dimensions: length={length}, width={width}, height={height}, unit={unit}"
    )
    validate_room_dimensions(length, width, height, unit)

    l_ft = convert_to_feet(length, unit)
    w_ft = convert_to_feet(width, unit)
    h_ft = convert_to_feet(height, unit)

    area = l_ft * w_ft
    volume = area * h_ft

    logger.info(f"Calculated results: area={area:.2f} sqft, volume={volume:.2f} cuft")
    return {"area_sqft": round(area, 4), "volume_cuft": round(volume, 4)}
