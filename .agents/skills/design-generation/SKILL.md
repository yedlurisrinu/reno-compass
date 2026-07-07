---
name: design-generation
description: Generate labeled bathroom design options (preferred + economy, plus user-directed passes) faithful to confirmed scope, each with layout, per-room lighting and material intent, and a refined estimate. Use at the Design stage.
---

# Design Generation

Produce design options that are faithful to confirmed scope and honest about cost. Judgment work; measurement
math and lighting calc are deterministic (bundled scripts / lighting-targets skill).

## What to produce
- Always a `preferred` and an `economy` option to start (economy always offered — pre-stages the budget-gap
  fallback, SI-19). Both options cover the SAME scope and differ only by finish TIER and cost — never by adding
  or dropping features. Over ceiling → economy first, then user-directed `design_3`/`design_4` (4-pass hard cap,
  SI-34; family steers each).
- Per option: layout with per-room `lighting_requirements` + `intended_materials` (material TYPE + fidelity
  for heavy/high-draw items so Safety's matrix can classify — SI-30), value proposition, block-diagram
  schematic, refined estimate incl. `gap_amount` if over ceiling.

## How to reason
- Scope fidelity is absolute: an option contains ONLY the family's measured existing bathroom + the specific
  changes they explicitly asked for. Elements they did NOT request — extra fixtures, upgrades, layout changes,
  "while we're at it" additions — are FORBIDDEN, not flagged (SI-19). Elements they're keeping are retained and
  labeled "unchanged," never silently redesigned. The one exception is a code/safety-compelled addition: raise it
  as a question, explain why, and get consent BEFORE putting it in the option. The value proposition is framed in
  the family's own stated goals, not aspirations you introduced.
- Accessibility needs are a REQUIRED constraint the option must satisfy, not an afterthought.
- Capture material TYPE to matrix fidelity (natural-vs-engineered stone, slab thickness/weight class, fixture
  amperage) — Design captures, Safety classifies. Never tier here.
- Estimates are RANGES + verify-locally; timelines industry-average + best-case if asked.
- Measurements: state units, record the unit on every dimension (never assume). Implausible dims → flag,
  don't compute.

## Retention (SI-34)
Each analyzed option's downstream analysis is retained by option_role; switching repoints, revisit_design
discards. See the behavior rule for the full model.

## Bundled tools
- `scripts/` — measurement/geometry math (area, volume, clearances to finished surface) AND the block-diagram
  schematic generator (labeled, not-to-scale; renders `schematic_ref` per option). Lighting targets come
  from the lighting-targets skill; the design consumes its output into per-room lighting_requirements.
