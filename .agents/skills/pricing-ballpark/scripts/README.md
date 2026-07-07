# Deterministic tools for pricing-ballpark
Antigravity implements these at codegen; contracts only here.
- ballpark_cost.py — Scope-stage ballpark: room sqft x RD-2 per-sqft band (tier chosen by scope) x regional factor, PLUS the contingency line (base 10% x regional factor, clamped 20%, weighted by home_age) shown as its OWN line, never folded into base. Also evaluates the RD2-G reality-check threshold (tight = within ~15% below ballpark low; unrealistic = >~25% below) feeding SI-17/T1a. Returns ranges, never point values.
