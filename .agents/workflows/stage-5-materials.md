---
description: Materials stage: itemize and price line items, allowance elicitation, envelope and allergy validation, total and divergence.
---

# Workflow — Stage 5: materials

Stage-specific SI notes: SI-20 divergence, SI-21 finish, SI-31 envelope (also constitution). Full behavior: constitution + rules. Orchestration: pipeline workflow.

## Stage contract

## STAGE 5 — MATERIALS   (product selection; production stage)

**Purpose:** Turn the chosen, feasible design into a complete, itemized, priced, shoppable materials list —
selecting products against design requirements, handling allowances transparently, screening allergies,
recommending finishes against lighting — and produce the spreadsheet + itemized final total.

**Preconditions:** `logistics_feasibility.status == completed` AND
`verdict ∈ {proceed, use_economy_option}`. (revisit_design → loops back; proceed_with_budget_gap → Synthesis.)
`current_stage == "materials"`.

**Required-coverage:**
1. Every design requirement → concrete line items (fixtures, surfaces, lighting products, backer/hidden)
2. Each item quantity with waste factor
3. Each item priced — banded (curated table) or allowance
4. Allowance items — elicit unit cost WITH basis stated; echo the arithmetic (SI-16)
5. Every material screened against allergies (SI-6)
6. Finish/color recommendation against lighting requirements; recommend CHARACTER, family sets allowance PRICE (SI-21)
7. Each concrete product code-validated against its item's stored `TierClassification.envelope` (SI-31):
   within → tier holds silently; BREACH → flag + re-open Safety for that ONE item (Materials never
   reclassifies); record `envelope_check` outcome
8. Final total; divergence-from-refined check (SI-20)

**Reads:** `design.chosen_design` (layout per-room → line items; per-room intended_materials → products; per-room lighting_requirements →
fixtures; refined_estimate → divergence check), `scope.special_considerations` (allergies MUST screen; health →
low-VOC steer), `scope.global_preferences` + per-room `area_preferences`. Frozen refs: itemized material bands + labor (RD-3); regional factor (RD-2); finish/lighting (RD-4).
**Reads (add):** `safety_permit.classifications[].envelope` (per-item bounds for the SI-31 check).
**Writes:** `materials` — `finish_recommendation`, `line_items[]` (pricing_mode, quantity, waste, cost_band or
unit_cost/basis, extended_cost, allergy_screened, satisfies_requirement, `envelope_check`), `spreadsheet_ref`,
`final_total` (allowance_portion, diverges_from_refined). On breach: re-opens `safety_permit` for one item.
**Tools/Skills:** quantity calc (with waste); cost-reference lookup; extended-cost tool (unit-match code-validated,
SI-16); envelope-check tool (product spec vs stored envelope, code-validated, SI-31) `[safety]`; finish/color
skill; allergy-screening skill (code-validated, SI-6); spreadsheet generator (xlsx skill);
total-rollup + divergence tool.
**Gate:** all items present, priced, allergy-screened, envelope-checked; allowances confirmed with basis; finish
recommended; spreadsheet generated; final total computed; `user_final_verdict`.
**Postconditions:** `materials.status = completed`; `line_items[]` priced; `spreadsheet_ref` set; `final_total` set.
**Failure/Refusal:**
- Allergy conflict → flag + seek alternative; never silently list an allergen material (SI-6, code-validated).
- Allowance unit mismatch → tool REFUSES to compute rather than produce garbage (SI-16, code-validated).
- Total diverges from Design's refined range → ALWAYS inform; ESCALATE to a family decision only when it pushes
  past ceiling; never auto-adjust selections (SI-20).
- Product exceeds stored envelope → do NOT reclassify here; flag + re-open Safety for that one item (SI-31); offer
  a lower-tier substitute as an alternative path (family choice, not forced).
- Itemized total is the FINAL/real cost — so Materials is the ONE later stage that may trigger `revisit_design`
  (SI-34): if the family finds the real total unacceptable, they may redesign (→ back to Design, discard the
  superseded option's retained analyses) IF design passes remain under the 4-cap. If the cap is exhausted →
  no redesign; route to choose an existing retained option or `proceed_with_budget_gap` (graceful, terminating).
**SI refs:** SI-6, SI-15, SI-16, SI-18, SI-20, SI-21, SI-17, SI-30, SI-31, SI-34.

---


## Elicitation / topics

## STAGE 5 — MATERIALS   (itemize → price → validate → present; allowance elicitation only)

Assume known (SI-5): `design.chosen_design` (layout per-room, intended_materials incl. fidelity, per-room lighting),
`safety_permit.classifications[].envelope` (SI-31 check), `scope.special_considerations.allergies` (screen), preferences.
Precondition: verdict ∈ {proceed, use_economy_option}. Refs: RD-3 (bands+labor), RD-4 (finish/lighting), RD-1 (envelope),
SI-15/16/20/21/31. Per prefs: fetch current price/availability + suggest economical alternatives where useful.

Topics: M1 line-item buildup · M2 allowance elicitation · M3 finish recommendation · M4 envelope + allergy validation ·
M5 total + divergence · M6 confirm.

---

### M1. Line-item buildup  [compute → present]
**Intent:** every design requirement → concrete line items (fixtures, surfaces, lighting, backer/hidden), quantities with
waste, priced banded (RD-3) or flagged allowance.
**Seed:** "Here's the full materials list built from your design — each item, quantity with waste overage, and a cost band. I'll flag the few where you set the budget."
**Follow-ups:** banded items priced from RD-3 (× regional factor); missing items → suggested-items store, flagged unvalidated, never auto-added (SI-23). Per prefs: where a spec'd product is pricey, note an economical alternative achieving the same result.
**Good-answer cue:** `line_items[]` — each with quantity, waste_factor, pricing_mode, cost_band or allowance flag, room_ref, satisfies_requirement.

### M2. Allowance elicitation  [elicitation — the one real input; SI-16]
**Intent:** for wild-variability finishes (tile, stone, faucets, glass, decorative lighting — RD3-H), elicit unit cost WITH basis stated.
**Seed:** "For the finishes that swing a lot on taste — [tile, counter] — what's your target cost PER SQUARE FOOT for tile? (not total — per sq ft, so the math stays honest)."
**Follow-ups (SI-16):** echo arithmetic on confirm ("$8/sq ft × 120 sq ft incl. 10% waste = $1,056"); `unit_cost_basis` MUST match the item `unit` — code-validated, refuse to compute a mismatch rather than multiply garbage.
**Good-answer cue:** allowance items have `unit_cost` + `unit_cost_basis` (unit-matched); arithmetic echoed.
**Notes:** agent recommends CHARACTER, family sets PRICE (SI-21) — keep taste-guidance and cost-control separate.

### M3. Finish recommendation  [present; SI-21 + RD-4]
**Intent:** finish/color character recommendation informed by per-room lighting (RD-4), screened against allergies.
**Seed:** "Given your [north-facing, low-natural-light] bath, I'd lean [warmer palette / higher-CRI fixtures] so colors read true. Character suggestion only — you set the spend on the allowance items."
**Good-answer cue:** `finish_recommendation` (palette_note, rationale) set, lighting-informed.

### M4. Envelope + allergy validation  [compute; code-validated — SI-31 + SI-6]
**Intent:** validate each concrete product against (a) the Safety envelope (SI-31) and (b) allergies (SI-6) — both code-level, must-not-fail.
**Seed (only surfaces if a check trips):**
- Envelope breach: "The [3cm marble slab] you picked is heavier than what we assumed when we cleared this as [Tier-3]. I'm sending just this item back to safety for a quick re-check — likely a professional-install flag. Or we look at a lighter option."
- Allergy: "[Product] contains [allergen] you flagged — here's an alternative that avoids it."
**Follow-ups:** envelope WITHIN → tier holds silently; BREACH → flag + re-open Safety for THAT ONE item (Materials never re-classifies, SI-31); record `envelope_check`. Allergy `skipped`≠safe: if allergies unknown, flag unscreened, don't pass silently (SI-6). Confirmed empty `[]` → screens clear.
**Good-answer cue:** every item `envelope_check` (not_applicable/within/breach_reopened_safety) + `allergy_screened` set.
**Notes:** these are the two must-not-fail code validations (SI-29) — annotation alone insufficient.

### M5. Total + divergence  [compute → present; SI-20]
**Intent:** itemized `final_total`; compare to Design's refined_estimate range; flag divergence.
**Seed:** "Itemized total: [range]. That's [within / above] the Design estimate — [if above: here's why, and whether it crosses your ceiling]."
**Follow-ups (SI-20):** ALWAYS inform on divergence; ESCALATE to a family decision only when it pushes past ceiling; never auto-adjust selections. Spreadsheet artifact = shoppable (xlsx skill).
**Good-answer cue:** `final_total` (low/high, allowance_portion, diverges_from_refined) set; `spreadsheet_ref` generated.

### M6. Confirm  [the gate]
**Seed:** "Materials list is complete, priced, allergy-checked, and within [budget picture]. Ready to lock it?"
**Good-answer cue:** all items present, priced, envelope- + allergy-validated; allowances confirmed with basis; finish recommended; spreadsheet generated; total computed; `user_final_verdict`.

---

### GATE (Materials)
Every requirement → priced line item, waste-adjusted (M1); allowances elicited with matched basis + echoed (M2); finish
recommended, lighting-informed (M3); every item envelope- + allergy-validated, breaches routed (M4); final total + divergence
computed, spreadsheet generated (M5). Gate opens + `user_final_verdict`.
**On restore (RC):** unchanged → re-confirm + skip topics; changed → reopen + cascade downstream.

---

