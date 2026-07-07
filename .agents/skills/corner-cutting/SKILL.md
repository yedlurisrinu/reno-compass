---
name: corner-cutting
description: Flag corner-cutting risk patterns in a contractor quote, severity-tagged, and generate the always-on what-to-demand advisory. Use at the Contractor Validation stage.
---

# Corner-Cutting Flags

Surface risk patterns from the quote-audit rubric (RD5-B), framed as questions to ask the contractor, not
accusations — the tool makes the family fluent, not adversarial.

## Severity
- HIGH: missing waterproofing line (in-wall failure); missing permit line where scope needs one; missing
  licensed trade for Tier-1/2 work (folds ex-tier_crossing).
- MEDIUM: lump-sum with no itemization; suspiciously low bid vs bands; open-ended allowances with no basis;
  demolition/haul omitted.
- LOW–MEDIUM: no change-order procedure; no written warranty; large upfront payment; no timeline/inspection
  milestones. [CA] Title 24 ventilation/lighting omission = medium+.

## Always-on advisory (SI-25)
Whether or not a quote exists, generate the what-to-demand checklist: itemized bid covering the full rubric;
3–5 bids on identical scope; verify license/insurance at the state board; confirm the invisible inclusions;
hold final payment until defects fixed and inspections signed off. We flag license presence/absence — we do
NOT validate license numbers.

## Output
`corner_cutting_flags[]` (flag, severity); `advisory_checklist[]` (generated in both modes).
