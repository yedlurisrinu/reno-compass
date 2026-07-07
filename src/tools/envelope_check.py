"""Safety envelope verification tool.

This module evaluates concrete materials or design modifications against the
stored safety classifications (envelopes) established during Safety Stage.
If a breach is identified, it signals a return to Safety Stage for re-classification.
"""

import logging
from typing import Any, Literal

logger = logging.getLogger("reno_project")


def evaluate_weight_band(weight: float) -> Literal["under_800", "800_1500", "over_1500"]:
    """Categorizes weight into standard safety bands.

    Args:
        weight: The weight in lbs.

    Returns:
        The weight band string.
    """
    if weight >= 1500.0:
        res = "over_1500"
    elif weight >= 800.0:
        res = "800_1500"
    else:
        res = "under_800"

    logger.debug(f"Evaluated weight band: weight={weight} lbs -> band={res}")
    return res


def validate_envelope(
    envelope: dict[str, Any] | None, product_spec: dict[str, Any] | None
) -> Literal["not_applicable", "within", "breach_reopened_safety"]:
    """Validates selected product specifications against Safety-stage envelope guidelines.

    Enforces Safety Code Validation Invariants (SI-31):
    * Structural envelope weight band, floor type, or conditions check.
    * Electrical dedicated circuit/panel/amperage limit check.

    Args:
        envelope: Stored envelope properties.
        product_spec: Selected product specification details.

    Returns:
        Validation outcome: "not_applicable", "within", or "breach_reopened_safety".
    """
    logger.debug(
        f"Validating product spec against envelope. envelope={envelope}, product_spec={product_spec}"
    )

    if not envelope or not product_spec:
        logger.debug("Envelope check result: not_applicable (missing envelope or product spec).")
        return "not_applicable"

    kind = envelope.get("kind")
    if not kind:
        logger.debug("Envelope check result: not_applicable (envelope kind is missing).")
        return "not_applicable"

    if kind == "structural":
        # Envelope parameters
        env_band = envelope.get("filled_weight_band", "under_800")
        env_floor = envelope.get("floor_type", "slab")
        env_conditions = set(envelope.get("aggravating_conditions") or [])

        # Product parameters
        prod_weight = float(product_spec.get("filled_weight", 0.0))
        prod_band = evaluate_weight_band(prod_weight)
        prod_floor = product_spec.get("floor_type", "slab")
        prod_conditions = set(product_spec.get("aggravating_conditions") or [])

        logger.debug(
            f"Structural envelope check details: "
            f"env_band={env_band}, prod_band={prod_band}; "
            f"env_floor={env_floor}, prod_floor={prod_floor}; "
            f"env_conditions={env_conditions}, prod_conditions={prod_conditions}"
        )

        # Weight band progression: under_800 -> 800_1500 -> over_1500
        band_hierarchy = {"under_800": 0, "800_1500": 1, "over_1500": 2}

        env_val = band_hierarchy.get(env_band, 0)
        prod_val = band_hierarchy.get(prod_band, 0)

        # 1. If weight band increases -> breach
        if prod_val > env_val:
            logger.warning(
                f"Structural envelope breach: product weight band '{prod_band}' exceeds envelope limit '{env_band}'."
            )
            return "breach_reopened_safety"

        # 2. Slab to Framed change -> breach (framed triggers structural scrutiny)
        if prod_floor == "framed" and env_floor == "slab":
            logger.warning(
                "Structural envelope breach: floor type upgraded from 'slab' to 'framed' without safety re-evaluation."
            )
            return "breach_reopened_safety"

        # 3. New aggravating condition introduced -> breach
        if not prod_conditions.issubset(env_conditions):
            new_conds = prod_conditions - env_conditions
            logger.warning(
                f"Structural envelope breach: new aggravating conditions introduced: {new_conds}."
            )
            return "breach_reopened_safety"

        logger.info("Structural envelope validation: within limits.")
        return "within"

    elif kind == "electrical":
        # Envelope parameters
        env_max_amp = float(envelope.get("max_amperage") or 20.0)
        env_ded_circ = bool(envelope.get("requires_dedicated_circuit", False))
        env_panel_work = bool(envelope.get("requires_panel_work", False))

        # Product parameters
        prod_amp = float(product_spec.get("amperage_draw", 0.0))
        prod_ded_circ = bool(product_spec.get("requires_dedicated_circuit", False))
        prod_panel_work = bool(product_spec.get("requires_panel_work", False))

        logger.debug(
            f"Electrical envelope check details: "
            f"env_max_amp={env_max_amp}A, prod_amp={prod_amp}A; "
            f"env_ded_circ={env_ded_circ}, prod_ded_circ={prod_ded_circ}; "
            f"env_panel_work={env_panel_work}, prod_panel_work={prod_panel_work}"
        )

        # 1. If product amperage exceeds stored limit -> breach
        if prod_amp > env_max_amp:
            logger.warning(
                f"Electrical envelope breach: product amperage draw '{prod_amp}A' exceeds envelope limit '{env_max_amp}A'."
            )
            return "breach_reopened_safety"

        # 2. If product needs dedicated circuit but envelope did not account for it -> breach
        if prod_ded_circ and not env_ded_circ:
            logger.warning(
                "Electrical envelope breach: product requires dedicated circuit but envelope does not allow."
            )
            return "breach_reopened_safety"

        # 3. If product needs panel work but envelope did not account for it -> breach
        if prod_panel_work and not env_panel_work:
            logger.warning(
                "Electrical envelope breach: product requires panel work but envelope does not allow."
            )
            return "breach_reopened_safety"

        logger.info("Electrical envelope validation: within limits.")
        return "within"

    logger.debug(f"Envelope validation result: not_applicable (unknown kind '{kind}').")
    return "not_applicable"
