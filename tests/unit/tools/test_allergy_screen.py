"""Unit tests for the 3-state allergy screening tool (TS-24)."""

from tools.allergy_screen import screen_material_allergy


def test_allergy_screen_explicit_safe():
    """Verifies that items with no allergen overlap are screened as safe."""
    allergies = ["latex", "dust"]
    product_allergens = ["wool"]
    assert screen_material_allergy(allergies, product_allergens) is True


def test_allergy_screen_explicit_conflict():
    """Verifies that items with allergen overlaps fail screening (case-insensitive)."""
    allergies = ["latex", "dust"]
    product_allergens = ["Wool", "Latex"]
    assert screen_material_allergy(allergies, product_allergens) is False


def test_allergy_screen_confirmed_empty_list():
    """Verifies that an empty allergy list [] is considered safe."""
    allergies = []
    product_allergens = ["wool", "latex"]
    assert screen_material_allergy(allergies, product_allergens) is True


def test_allergy_screen_skipped_raises_unsafe():
    """Verifies that skipped or unknown allergies are NOT assumed safe (TS-24)."""
    allergies = ["skipped"]
    product_allergens = ["wool"]
    assert screen_material_allergy(allergies, product_allergens) is False

    allergies = ["SKIPPED "]
    product_allergens = ["wool"]
    assert screen_material_allergy(allergies, product_allergens) is False


def test_allergy_screen_none_raises_unsafe():
    """Verifies that a None allergy field is flagged as unsafe (TS-24)."""
    assert screen_material_allergy(None, ["wool"]) is False
