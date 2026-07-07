"""Unit tests for lighting calculations, lumen targets, and Title 24 bounds."""

from tools.lighting_calc import calculate_lighting_requirements


def test_calculate_lighting_requirements_base():
    """Verifies lighting calculations on standard room sizes."""
    # Area: 80 sqft, height 8 ft (scale = 1.0), neutral reflectivity (mult = 1.0)
    # Vanity: 1 (area = 10 sqft, lumens = 800)
    # Shower: True (area = 15 sqft, lumens = 450)
    # Ambient: 80 - 25 = 55 sqft (lumens = 1650)
    # Expected lumens: 800 + 450 + 1650 = 2900
    # Expected fixture count: 2900 / 800 = 3.6
    # Recommended window: 80 * 0.08 = 6.4 sqft
    res = calculate_lighting_requirements(80.0, 8.0, vanity_count=1, shower_present=True)

    assert res["required_artificial_lumens"] == 2900.0
    assert res["required_fixture_count"] == 3.6
    assert res["recommended_window_area"] == 6.4
    assert res["required_natural_lumens"] == 2400.0


def test_calculate_lighting_height_scaling():
    """Verifies that height scaling applies proportionally."""
    # Area: 80 sqft, height 10 ft (scale = 1.25)
    # Neutral base lumens = 2900
    # Expected lumens = 2900 * 1.25 = 3625.0
    # Expected fixtures = 3625.0 / 800 = 4.5
    res = calculate_lighting_requirements(80.0, 10.0, vanity_count=1, shower_present=True)
    assert res["required_artificial_lumens"] == 3625.0
    assert res["required_fixture_count"] == 4.5


def test_calculate_lighting_reflectivity_modifications():
    """Verifies dark/matte and light/white wall reflectivity modifiers."""
    # Base lumens = 2900.0, scale = 1.0
    # Dark: mult = 1.15 -> 2900 * 1.15 = 3335.0
    res_dark = calculate_lighting_requirements(80.0, 8.0, wall_reflectivity="dark")
    assert res_dark["required_artificial_lumens"] == 3335.0

    # Light: mult = 0.85 -> 2900 * 0.85 = 2465.0
    res_light = calculate_lighting_requirements(80.0, 8.0, wall_reflectivity="white")
    assert res_light["required_artificial_lumens"] == 2465.0


def test_calculate_lighting_min_fixtures():
    """Verifies that fixture target counts are clamped at a minimum of 1."""
    # Very small powder room: 15 sqft, height 8ft
    # Vanity: 0, Shower: False
    # Ambient: 15 sqft * 30 = 450 lumens
    # Count: 450 / 800 = 0.6 -> clamped to 1.0
    res = calculate_lighting_requirements(15.0, 8.0, vanity_count=0, shower_present=False)
    assert res["required_fixture_count"] == 1.0
