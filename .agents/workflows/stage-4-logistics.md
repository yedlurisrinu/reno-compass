---
description: Logistics and feasibility stage: disruption, displacement (dwelling-gated), budget verdict and the displacement recalibration loop.
---

# Workflow — Stage 4: logistics

Stage-specific SI notes: SI-22 dwelling, SI-23 two-tier store, SI-32 displacement loop. Full behavior: constitution + rules. Orchestration: pipeline workflow.

## Stage contract

## STAGE 4 — LOGISTICS & FEASIBILITY

**Purpose:** Ground the chosen, safety-checked design against the two realities that decide whether a family
can proceed — the budget gap and the disruption to daily life — offering empathetic alternatives, and setting
the feasibility verdict (incl. the encouraging budget-gap path).

**Preconditions:** `safety_permit.status == completed`. `current_stage == "logistics_feasibility"`.

**Required-coverage:**
1. Disruption assessment — which utilities/rooms offline, how long
2. Live-through-it determination — given occupant count, pets, special considerations
3. Displacement alternatives where disruption significant (portable unit / temp structure / sequencing to keep a
   bathroom usable / stay with family / lodging); if live-through-it is false, the CHOSEN displacement cost feeds the verdict
4. Tenant obligations if `has_rental_tenants`
5. Weather/timing implications given `intended_timing` (reasoning, no stored forecast)
6. Budget: CONSUME Design's refined estimate (do not recompute); fold in displacement cost →
   `total_with_displacement`; set `feasible_within_target` / `_within_ceiling`
6a. If `total_with_displacement` breaches ceiling → DISPLACEMENT RECALIBRATION LOOP (SI-32/CL-47):
    (i) ask if a separate budget funds displacement; (ii) if not, inline-optimize displacement (sequencing /
    stay-with-family / cheaper off-site) and re-test; (iii) if still over, OFFER specific slices (never
    auto-cut); (iv) if declined/insufficient → `proceed_with_budget_gap`. NEVER a forced rollback; NEVER
    mutates chosen_design; `revisit_design` only on explicit family choice.
7. Feasibility verdict discussed and understood

**Reads:** `design.chosen_design` (+ `refined_estimate`), `safety_permit.*` (professional/permit cost+time),
`scope.property_context` (occupants, tenants), `scope.special_considerations`, `scope.budget_target/ceiling`,
`scope.intended_timing`. Frozen ref: labor/professional/permit/logistics ballparks + regional factor (RD-2, for displacement costing).
**Writes:** `logistics_feasibility` — `disruption`, `displacement_options[]`, `chosen_displacement`,
`tenant_obligation_note`, `weather_timing_note`, `total_with_displacement`, `feasible_within_target/ceiling`, `verdict`.
**Tools/Skills:** disruption-assessment skill; displacement-alternative-generation skill; budget-feasibility tool.
**Gate:** disruption assessed; displacement presented where warranted; both feasibility booleans computed;
verdict discussed; `user_final_verdict` = family UNDERSTANDS the feasibility reality.
**Postconditions:** `logistics_feasibility.status = completed`; verdict set:
`proceed` / `use_economy_option` / `revisit_design` / `proceed_with_budget_gap`.
**Failure/Refusal:** never pretend feasibility. Over ceiling after budget-engineered options (or family declines
economy) → `proceed_with_budget_gap` → Synthesis full plan labeled with gap-to-bridge (NOT a dead end).
Professional/permit costs from Stage 3 MUST be reflected. Costs = ranges + disclaimer (SI-15).
Budget-driven design revisit correctly re-runs Safety via cascade (economy option may have fewer Tier-1 items).
**SI refs:** SI-6, SI-15, SI-17, SI-27, SI-32.

---


## Elicitation / topics

## STAGE 4 — LOGISTICS & FEASIBILITY   (compute-and-judge; the budget verdict + CL-47 loop)

Assume known (SI-5): `scope.*` (occupants, tenants, timing, budget target/ceiling, dwelling_type), `design.chosen_design`
(+ refined_estimate — CONSUMED, not recomputed, SI-17), `safety_permit.*` (professional/permit cost+time). Refs:
RD-2 (displacement costing, regional factor), SI-22 (dwelling gates displacement), SI-32/CL-47 (recalibration loop).

Topics: L1 disruption · L2 live-through-it · L3 displacement options · L4 tenant/timing notes · L5 feasibility
verdict + CL-47 loop · L6 confirm.

---

### L1. Disruption assessment  [compute → disclose]
**Intent:** which utilities/rooms go offline and for how long.
**Seed:** "Here's the disruption picture: [water/the only bathroom/etc.] offline about [duration]. Let's make sure that's livable."
**Follow-ups:** duration reasons on trade sequencing (RD3-G4) + timing; single-bathroom home → offline bath is high-impact (TS-4).
**Good-answer cue:** `disruption` (offline_utilities, offline_duration_estimate) set.
**Notes:** timelines as industry-average + best-case (RD2-F/RD3-G).

### L2. Live-through-it determination  [elicitation — genuine question]
**Intent:** can the household stay during work, given occupant count, pets, special_considerations, single-bath status.
**Seed:** "Can you live in the home through this, or will you need somewhere else for part of it? Big factor if this is your only full bath."
**Good-answer cue:** `can_live_through_it` set (or knowingly deferred pending displacement cost, L3).
**Notes:** if false, the CHOSEN displacement cost feeds the verdict (TS-4).

### L3. Displacement options  [compute; dwelling-type gated — SI-22]
**Intent:** where warranted, present empathetic alternatives WITH cost bands; dwelling_type gates what's offered.
**Seed:** "If you need to be out, here are options with rough costs: [stay-with-family / off-site rental / sequencing to keep the bath usable longer / on-site]. Which fits?"
**Follow-ups (SI-22):** condo/apartment → NO yard/on-site temp-structure (TS-9): storage-unit/off-site only + HOA/access disclosures; house → yard options available.
**Good-answer cue:** `displacement_options[]` (option + cost_band); `chosen_displacement` if live-through-it false.
**Notes:** costs = ranges (RD-2). Framed as choices, not verdicts.

### L4. Tenant + timing notes  [disclose]
**Intent:** tenant legal-notice obligations if `has_rental_tenants`; weather/timing implications from `intended_timing`.
**Seed:** "[If tenants] There may be legal notice you owe tenants before work — worth checking. [Timing] Your [season] target — [weather/lead-time implication]."
**Good-answer cue:** `tenant_obligation_note` (if applicable) + `weather_timing_note` set. No stored forecast — reasoning only.

### L5. Feasibility verdict + CL-47 recalibration loop  [compute-and-judge; the budget judgment]
**Intent:** consume Design's estimate, fold in displacement → `total_with_displacement`; set feasibility booleans + verdict;
if over ceiling, run the SI-32/CL-47 loop.
**Seed (verdict):** "Total including [displacement] lands at [range]. Against your target [$X] and ceiling [$Y]: [within / over]."
**Seed (CL-47 loop, only if total > ceiling — mirrors Scope's honesty, no forced rollback):**
1. "Is displacement funded from a separate budget?" (yes → resolved)
2. If no → "Let me optimize — [sequencing to keep utilities longer / stay-with-family vs rental]." Re-test.
3. If still over → "Here are specific nice-to-haves or high-cost lines you COULD trim to land under: [list]." (offer, never auto-cut)
4. If declined/insufficient → "We don't have to drop the project — I'll carry the full plan forward with an honest gap to bridge." → `proceed_with_budget_gap`.
**Good-answer cue:** `total_with_displacement`, `feasible_within_target/_ceiling` computed; `verdict` set (proceed /
use_economy_option / revisit_design / proceed_with_budget_gap).
**Notes (SI-32/CL-47/SI-34):** NEVER a forced rollback or "not feasible" wall. `use_economy_option` REPOINTS to the
economy option's retained analysis (economy offered first; SI-34), not a destroy-recompute. If economy is also
rejected, user-directed design_3/design_4 passes apply under the 4-cap. `revisit_design` (new geometry) only on
explicit family choice, and draws a design pass. CL-47 never mutates chosen_design on its own.

### L6. Confirm  [the gate]
**Seed:** "You understand the disruption, the displacement plan and cost, and where the budget lands?"
**Good-answer cue:** disruption assessed; displacement presented where warranted; both feasibility booleans + verdict set;
family understands; `user_final_verdict`.

---

### GATE (Logistics)
Disruption assessed (L1); live-through-it determined (L2); displacement presented where warranted, dwelling-gated (L3);
tenant/timing notes where applicable (L4); `total_with_displacement` + feasibility booleans + verdict set, CL-47 loop run
if over ceiling (L5). Gate opens + `user_final_verdict`.
**On restore (RC):** unchanged → re-confirm + skip topics; changed → reopen + cascade downstream.

---

