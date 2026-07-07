"""Deterministic RD-2 ballpark cost and budget reality-check calculator.

Implements Constitution Principle 9 (numbers come from curated references via
deterministic tools, never hallucinated by the model) and SI-17 (budget reality
recalibration). All values are frozen from RD-2
(`.agents/skills/pricing-ballpark/SKILL.md`); update the version pointer there,
not these numbers, when the reference set changes.
"""

from typing import Literal

# RD2-A: per-sqft all-in bands (labor + professional + permit + logistics), national baseline (1.0x).
BALLPARK_BANDS: dict[str, tuple[float, float]] = {
    "budget": (80.0, 120.0),
    "mid": (180.0, 280.0),
    "high_end": (300.0, 450.0),
    "luxury": (500.0, 800.0),
}

# RD2-C5: single flat regional multiplier per ZIP. National baseline = 1.0x.
REGIONAL_MULTIPLIERS: dict[str, float] = {
    "95120": 1.55,  # San Jose / Silicon Valley (only populated instance in the frozen set)
}
DEFAULT_REGIONAL_MULTIPLIER = 1.0

# RD2-E: contingency = base 10% x regional factor, clamped to a 20% ceiling.
BASE_CONTINGENCY_PCT = 0.10
CONTINGENCY_CAP_PCT = 0.20

# RD2-G: reality-check thresholds, measured against the ballpark low end (contingency-inclusive).
#   stated >= L                 -> plausible
#   0.75*L <= stated < L        -> tight
#   stated < 0.75*L             -> unrealistic (triggers SI-17 recalibration loop)
TIGHT_FLOOR_FRACTION = 0.75

RealityVerdict = Literal["plausible", "tight", "unrealistic"]


def regional_multiplier(zipcode: str | None) -> float:
    """Returns the frozen flat regional cost multiplier for a ZIP (1.0 if unknown)."""
    if not zipcode:
        return DEFAULT_REGIONAL_MULTIPLIER
    return REGIONAL_MULTIPLIERS.get(str(zipcode).strip(), DEFAULT_REGIONAL_MULTIPLIER)


def contingency_pct(factor: float) -> float:
    """RD2-E: base 10% scaled by the regional factor, clamped to the 20% ceiling."""
    return min(BASE_CONTINGENCY_PCT * factor, CONTINGENCY_CAP_PCT)


def compute_ballpark(
    renovation_area: float,
    zipcode: str | None,
    tier: str = "mid",
    home_age: int | None = None,
) -> dict:
    """Computes an RD-2 ballpark cost range with a separate contingency band.

    Args:
        renovation_area: Target remodel area in square feet (must be positive).
        zipcode: Property ZIP driving the regional multiplier.
        tier: RD2-A band key (budget/mid/high_end/luxury); defaults to mid.
        home_age: Optional home age (informational; contingency scaling is regional).

    Returns:
        Dict with base low/high, the regional factor, the contingency band, and
        ``reality_basis_low`` (the contingency-inclusive low end used by the check).

    Raises:
        ValueError: If renovation_area is not positive (cannot price nothing).
    """
    if renovation_area is None or renovation_area <= 0:
        raise ValueError("renovation_area must be positive to compute a ballpark.")
    if tier not in BALLPARK_BANDS:
        tier = "mid"

    band_low, band_high = BALLPARK_BANDS[tier]
    factor = regional_multiplier(zipcode)
    base_low = renovation_area * band_low * factor
    base_high = renovation_area * band_high * factor

    pct = contingency_pct(factor)
    cont_low = round(base_low * pct, 2)
    cont_high = round(base_high * pct, 2)

    return {
        "low": round(base_low, 2),
        "high": round(base_high, 2),
        "regional_factor": factor,
        "tier": tier,
        "contingency": {
            "low": cont_low,
            "high": cont_high,
            "pct_of_ballpark": round(pct * 100, 2),
            "capped": pct >= CONTINGENCY_CAP_PCT,
        },
        # RD2-G basis: ballpark low end including the scaled contingency.
        "reality_basis_low": round(base_low * (1 + pct), 2),
    }


def assess_budget_reality(
    stated_budget: float, ballpark_reality_basis_low: float
) -> tuple[RealityVerdict, str]:
    """Classifies a stated budget against the ballpark low end (RD2-G).

    Args:
        stated_budget: The family's stated target budget.
        ballpark_reality_basis_low: ``reality_basis_low`` from :func:`compute_ballpark`.

    Returns:
        (verdict, note) where verdict is plausible/tight/unrealistic and note is a
        homeowner-facing, calibrated explanation (Principle 10).
    """
    low = ballpark_reality_basis_low
    if stated_budget >= low:
        return (
            "plausible",
            f"Your ${stated_budget:,.0f} target meets or exceeds the realistic low end "
            f"of about ${low:,.0f} for this scope.",
        )
    if stated_budget >= TIGHT_FLOOR_FRACTION * low:
        return (
            "tight",
            f"Your ${stated_budget:,.0f} target is under the roughly ${low:,.0f} low end, "
            "but reachable with careful, economy-minded choices.",
        )
    return (
        "unrealistic",
        f"Your ${stated_budget:,.0f} target is well below the realistic minimum of about "
        f"${low:,.0f} for this scope. Let's recalibrate the scope or the budget together.",
    )
