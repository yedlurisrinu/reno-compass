---
name: displacement-alternatives
description: Generate empathetic displacement options with cost bands when a family can't live through a remodel, gated by dwelling type. Use at the Logistics stage.
---

# Displacement Alternatives

Offer where-to-stay options with rough costs, framed as choices, not verdicts (SI-22).

## How to reason
- Dwelling_type GATES what's offered: house → yard/on-site options available; condo/apartment → NO yard or
  on-site temp-structure, offer storage-unit / off-site only, and surface HOA/access disclosures.
- Options carry cost BANDS (from pricing-ballpark / material-bands), never false precision.
- If live-through-it is false, the CHOSEN displacement cost feeds `total_with_displacement` and the verdict.

## Displacement recalibration loop (SI-32/CL-47)
When `total_with_displacement` breaches the ceiling, run the staged loop (never a forced rollback):
1. Ask if a SEPARATE budget funds displacement → yes: resolved.
2. If no → inline optimization (sequencing to keep utilities longer; stay-with-family vs rental; cheaper
   off-site). Re-test against ceiling.
3. If still over → OFFER specific trims the family MAY choose (never auto-cut).
4. If declined/insufficient → verdict `proceed_with_budget_gap` → Synthesis full plan with gap-to-bridge.
