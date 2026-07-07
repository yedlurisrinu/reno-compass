---
name: consolidation-summary
description: Assemble the final family-facing plan PDF (safety-forward) and ship the materials spreadsheet as a separate artifact. Use at the Synthesis stage.
---

# Consolidation & Summary

Compile the whole dossier into the deliverable, honest and encouraging (SI-27). Compile, don't re-elicit.

## PDF assembly (safety-forward order)
summary + preferred design → safety/permit callouts (prominent) → budget → logistics/displacement → quote
audit (if any) → DIY procedures + tools (if applicable) → advisory checklist → phase checklists.
- Materials xlsx ships as a SEPARATE artifact ALONGSIDE the PDF — the PDF does NOT embed line items nor
  reference a spreadsheet pointer.
- Two INDEPENDENT gates: `phase_checklists` ⟺ `design_accepted` (execution artifact, only if the family
  committed to a design); `budget_gap_bridge` ⟺ `has_budget_gap` (gap section at the END, framed as the
  on-ramp — never "not feasible").

## Framing
Costs as ranges + verify-locally. Safety findings carry through unchanged. The family leaves informed.

## Bundled tools
- `scripts/` — PDF generator; xlsx (materials spreadsheet) generator. Deterministic; the model composes
  content, the scripts render.
