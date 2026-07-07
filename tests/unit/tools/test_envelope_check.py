"""Unit tests for safety envelope verification (structural and electrical checks)."""

from tools.envelope_check import evaluate_weight_band, validate_envelope


def test_evaluate_weight_band():
    """Verifies weight bands bounds classification."""
    assert evaluate_weight_band(700) == "under_800"
    assert evaluate_weight_band(800) == "800_1500"
    assert evaluate_weight_band(1499) == "800_1500"
    assert evaluate_weight_band(1500) == "over_1500"


def test_validate_envelope_structural_within():
    """Verifies standard framed floor with same weight band passes validation."""
    envelope = {
        "kind": "structural",
        "filled_weight_band": "800_1500",
        "floor_type": "framed",
        "aggravating_conditions": ["upper_floor"],
    }
    product_spec = {
        "filled_weight": 1000.0,
        "floor_type": "framed",
        "aggravating_conditions": ["upper_floor"],
    }
    assert validate_envelope(envelope, product_spec) == "within"


def test_validate_envelope_structural_slab_framed_breach():
    """Verifies that changing floor type from slab to framed breaches envelope."""
    envelope = {
        "kind": "structural",
        "filled_weight_band": "800_1500",
        "floor_type": "slab",
        "aggravating_conditions": [],
    }
    product_spec = {"filled_weight": 1000.0, "floor_type": "framed", "aggravating_conditions": []}
    # Framed triggers structural reviews that slab suppressed
    assert validate_envelope(envelope, product_spec) == "breach_reopened_safety"


def test_validate_envelope_structural_weight_breach():
    """Verifies that selecting an item in a heavier band than classified breaches envelope."""
    envelope = {
        "kind": "structural",
        "filled_weight_band": "under_800",
        "floor_type": "framed",
        "aggravating_conditions": [],
    }
    product_spec = {
        "filled_weight": 1000.0,  # 800_1500 band
        "floor_type": "framed",
        "aggravating_conditions": [],
    }
    assert validate_envelope(envelope, product_spec) == "breach_reopened_safety"


def test_validate_envelope_structural_aggravating_condition_breach():
    """Verifies that introducing a new aggravating condition breaches envelope."""
    envelope = {
        "kind": "structural",
        "filled_weight_band": "800_1500",
        "floor_type": "framed",
        "aggravating_conditions": ["upper_floor"],
    }
    product_spec = {
        "filled_weight": 1000.0,
        "floor_type": "framed",
        "aggravating_conditions": ["upper_floor", "span_gt_12ft"],  # span is new
    }
    assert validate_envelope(envelope, product_spec) == "breach_reopened_safety"


def test_validate_envelope_electrical_within():
    """Verifies electrical items within amperage and panel thresholds pass."""
    envelope = {
        "kind": "electrical",
        "max_amperage": 20.0,
        "requires_dedicated_circuit": False,
        "requires_panel_work": False,
    }
    product_spec = {
        "amperage_draw": 15.0,
        "requires_dedicated_circuit": False,
        "requires_panel_work": False,
    }
    assert validate_envelope(envelope, product_spec) == "within"


def test_validate_envelope_electrical_amperage_breach():
    """Verifies exceeding max amperage limits breaches envelope."""
    envelope = {
        "kind": "electrical",
        "max_amperage": 15.0,
        "requires_dedicated_circuit": False,
        "requires_panel_work": False,
    }
    product_spec = {
        "amperage_draw": 16.0,
        "requires_dedicated_circuit": False,
        "requires_panel_work": False,
    }
    assert validate_envelope(envelope, product_spec) == "breach_reopened_safety"


def test_validate_envelope_electrical_circuit_breach():
    """Verifies that requiring dedicated circuits when unclassified breaches envelope."""
    envelope = {
        "kind": "electrical",
        "max_amperage": 20.0,
        "requires_dedicated_circuit": False,
        "requires_panel_work": False,
    }
    product_spec = {
        "amperage_draw": 15.0,
        "requires_dedicated_circuit": True,
        "requires_panel_work": False,
    }
    assert validate_envelope(envelope, product_spec) == "breach_reopened_safety"
