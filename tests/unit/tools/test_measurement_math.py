"""Unit tests for measurement math calculations and dimension validations."""

import pytest

from tools.measurement_math import (
    ImplausibleMeasurementError,
    calculate_area_and_volume,
)


def test_calculate_area_and_volume_success():
    """Verifies area/volume logic on standard dimensions."""
    res = calculate_area_and_volume(10.0, 8.0, 8.5, "ft")
    assert res["area_sqft"] == 80.0
    assert res["volume_cuft"] == 680.0


def test_calculate_area_and_volume_unit_conversion():
    """Verifies dimension conversion from inches/cm to feet."""
    # 120 inches = 10 feet, 96 inches = 8 feet, 96 inches = 8 feet
    res = calculate_area_and_volume(120.0, 96.0, 96.0, "in")
    assert res["area_sqft"] == 80.0
    assert res["volume_cuft"] == 640.0


def test_implausible_large_footprint_raises_error():
    """Verifies that dimensions >= 40 ft throw ImplausibleMeasurementError (TS-38)."""
    with pytest.raises(ImplausibleMeasurementError):
        calculate_area_and_volume(40.0, 10.0, 8.0, "ft")

    with pytest.raises(ImplausibleMeasurementError):
        calculate_area_and_volume(10.0, 480.0, 8.0, "in")  # 480 inches = 40 feet


def test_implausible_low_ceiling_raises_error():
    """Verifies that ceiling height <= 6 inches throws ImplausibleMeasurementError (TS-38)."""
    with pytest.raises(ImplausibleMeasurementError):
        calculate_area_and_volume(10.0, 10.0, 0.5, "ft")  # 0.5 ft = 6 inches

    with pytest.raises(ImplausibleMeasurementError):
        calculate_area_and_volume(10.0, 10.0, 5.0, "in")  # 5 inches < 6 inches


def test_implausible_high_ceiling_raises_error():
    """Verifies that ceiling height >= 20 ft throws ImplausibleMeasurementError."""
    with pytest.raises(ImplausibleMeasurementError):
        calculate_area_and_volume(10.0, 10.0, 20.0, "ft")

    with pytest.raises(ImplausibleMeasurementError):
        calculate_area_and_volume(10.0, 10.0, -1.0, "ft")  # negative dimension
