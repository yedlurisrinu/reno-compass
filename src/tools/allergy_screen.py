"""Allergy screening validation tool.

This module screens product material ingredients against user allergy lists.
It enforces the 3-state allergy check:
- Explicit allergies -> match-screened
- Confirmed no allergies ([]) -> clear
- Skipped/Unknown -> flagged unsafe/unscreened (never passes silently)
"""

import logging

logger = logging.getLogger("reno_project")


def screen_material_allergy(allergies: list[str] | None, product_allergens: list[str]) -> bool:
    """Evaluates if a product is safe to use based on the user's allergy history.

    Enforces 3-state sensitive skip logic (SI-6):
    * allergies = None -> returns False (unscreened, not safe)
    * allergies contains "skipped" -> returns False (unscreened, not safe)
    * allergies = [] -> returns True (confirmed no allergies, safe)
    * allergen overlap -> returns False (conflict, not safe)

    Args:
        allergies: User's reported allergies.
        product_allergens: Allergens/irritants associated with the material.

    Returns:
        bool: True if safe and cleared, False if conflict or unscreened.
    """
    logger.debug(
        f"Screening material allergy: user_allergies={allergies}, product_allergens={product_allergens}"
    )

    if allergies is None:
        logger.debug("Allergy screening result: False (user allergies are undefined/None).")
        return False

    # Check for "skipped" indicator
    for item in allergies:
        if isinstance(item, str) and item.strip().lower() == "skipped":
            logger.debug("Allergy screening result: False (user explicitly skipped allergy check).")
            return False

    if not allergies:
        # Confirmed empty list [] -> clear
        logger.debug("Allergy screening result: True (user confirmed no allergies).")
        return True

    # Normalize list items for case-insensitive matching
    user_allergies_set = {a.strip().lower() for a in allergies if isinstance(a, str)}
    prod_allergens_set = {p.strip().lower() for p in product_allergens if isinstance(p, str)}

    # Check for intersection
    intersection = user_allergies_set.intersection(prod_allergens_set)
    if intersection:
        logger.debug(f"Allergy screening result: False (allergen conflict found: {intersection}).")
        return False

    logger.debug("Allergy screening result: True (no allergen overlap found).")
    return True
