# Deterministic tools for material-bands
- quantity_waste.py — quantities with waste overage from dimensions.
- cost_lookup.py — banded cost from frozen RD-3 tables x regional factor (RD-2).
- extended_cost.py — allowance unit-cost x quantity; REFUSE on unit-mismatch (SI-16, code-validated).
- total_rollup.py — itemized total + divergence vs Design refined estimate (SI-20).
- allergy_screen.py — screen line items vs allergies; skipped/null != safe (SI-6, code-validated).
- envelope_check.py — product spec vs stored TierClassification.envelope; breach -> reopen Safety, 1 item (SI-31, code-validated).
