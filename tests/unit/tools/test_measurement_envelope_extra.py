"""Coverage for remaining branches in measurement and envelope calculators."""

import pytest

from tools.envelope_check import validate_envelope
from tools.measurement_math import (
    ImplausibleMeasurementError,
    convert_to_feet,
    validate_room_dimensions,
)

# --------------------------------------------------------------------------- #
# convert_to_feet / validate_room_dimensions
# --------------------------------------------------------------------------- #


def test_convert_centimeters():
    assert convert_to_feet(304.8, "cm") == pytest.approx(10.0)


def test_convert_unsupported_unit_raises():
    with pytest.raises(ValueError, match="Unsupported measurement unit"):
        convert_to_feet(5.0, "furlongs")


def test_validate_room_dimensions_bad_unit_wraps_error():
    with pytest.raises(ImplausibleMeasurementError):
        validate_room_dimensions(10.0, 8.0, 8.0, "furlongs")


# --------------------------------------------------------------------------- #
# validate_envelope
# --------------------------------------------------------------------------- #


def test_envelope_not_applicable_when_missing():
    assert validate_envelope({}, {}) == "not_applicable"


def test_envelope_not_applicable_without_kind():
    assert validate_envelope({"floor_type": "slab"}, {"filled_weight": 100}) == "not_applicable"


def test_envelope_unknown_kind():
    assert validate_envelope({"kind": "plumbing"}, {"x": 1}) == "not_applicable"


def test_structural_weight_band_breach():
    envelope = {"kind": "structural", "filled_weight_band": "under_800", "floor_type": "slab"}
    product = {"filled_weight": 2000.0, "floor_type": "slab"}
    assert validate_envelope(envelope, product) == "breach_reopened_safety"


def test_structural_within_limits():
    envelope = {"kind": "structural", "filled_weight_band": "over_1500", "floor_type": "slab"}
    product = {"filled_weight": 100.0, "floor_type": "slab"}
    assert validate_envelope(envelope, product) == "within"


def test_electrical_panel_work_breach():
    envelope = {"kind": "electrical", "max_amperage": 20.0, "requires_panel_work": False}
    product = {"amperage_draw": 15.0, "requires_panel_work": True}
    assert validate_envelope(envelope, product) == "breach_reopened_safety"


def test_electrical_within_limits():
    envelope = {"kind": "electrical", "max_amperage": 20.0}
    product = {"amperage_draw": 10.0}
    assert validate_envelope(envelope, product) == "within"
