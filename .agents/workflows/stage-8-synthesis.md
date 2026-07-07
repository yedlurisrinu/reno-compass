---
description: Synthesis stage: assemble the family-facing plan PDF (safety-forward), separate materials xlsx, two independent gates for checklist and budget-gap bridge.
---

# Workflow — Stage 8: synthesis

Stage-specific SI notes: SI-27 synthesis. Full behavior: constitution + rules. Orchestration: pipeline workflow.

## Stage contract

## STAGE 7 — SYNTHESIS   (single rich PDF; encouraging-but-honest)

**Purpose:** Consolidate the whole journey into one family-facing PDF they own — the complete picture plus phase
checklists (and DIY procedures/tools where applicable) — or, when a budget gap remains, the same rich plan
labeled with the honest gap-to-bridge as an on-ramp to execution (never "not feasible").

**Preconditions (two entry paths):**
- Full: `contractor_validation.status == completed` AND (DIY Planning completed OR N/A).
- Budget-gap: routed here when `logistics_feasibility.verdict == "proceed_with_budget_gap"` (skips Materials,
  Contractor Validation, DIY Planning). `current_stage == "synthesis"`.

**Required-coverage:**
1. Set the TWO INDEPENDENT gates (CL-73/SI-27): `design_accepted` (family committed to a design) and
   `has_budget_gap` (gap vs ceiling remains). `outcome` = derived display label only.
2. Assemble consolidated summary from the dossier (safety-forward order)
3. `design_accepted == true` → generate the four phase checklists (execution artifact). Else OMIT them
   (rejected-all → no checklist, whether or not a gap exists).
4. `has_budget_gap == true` → add `budget_gap_bridge` at the END (gap amount + concrete bridge options),
   INDEPENDENT of acceptance; still include the FULL preferred-design details. Frame as on-ramp, never "not feasible".
5. Include the advisory checklist (always); include DIY procedures + tools where DIY Planning ran
6. Produce the PDF (NO embedded line items, NO in-PDF spreadsheet reference); the materials xlsx is delivered
   ALONGSIDE as a SEPARATE artifact (generated at Materials M5, keyed by room_ref/area, CL-12). Present + confirm

**PDF order (safety-forward):** summary + preferred design → safety/permit callouts (prominent) → budget →
logistics/displacement → quote audit (if any) →
DIY procedures + tools (if applicable) → advisory checklist → phase checklists (only if design_accepted).

**Reads:** entire dossier. Budget-gap path reads whatever was completed (scope, design, safety, logistics) +
the verdict + rejected budget-engineered options.
**Writes:** `synthesis` — `design_accepted`, `has_budget_gap`, `outcome` (derived), `budget_gap_bridge` (⟺
has_budget_gap), `phase_checklists` (⟺ design_accepted), `pdf_ref`, `generated_at`. Then `current_stage == "complete"`.
**Tools/Skills:** consolidation/summary skill; phase-checklist skill; PDF generator (pdf skill);
honest-conclusion/budget-gap-bridge framing skill.
**Gate:** appropriate PDF generated + presented; `user_final_verdict`.
**Postconditions:** `synthesis.status = completed`; `pdf_ref` + `generated_at` set; `current_stage = complete`.
**Failure/Refusal:** Synthesis is a MIRROR — no new advice/classifications; safety findings + permit disclosures
carry through UNCHANGED and restated prominently (never softened/dropped). budget-gap framed as on-ramp, never
failure. Costs = ranges + disclaimer (SI-15). Consistent language (proceed_with_budget_gap, not "not feasible").
**SI refs:** SI-9, SI-10, SI-15, SI-14, SI-17, SI-25, SI-27.

---

## APPENDIX — cross-cutting for the orchestrator (state-machine spec, to be expanded)
- States = the 7 always-stages + `diy_planning` (conditional) + `complete`. Transitions = strictly linear
  FORWARD, plus TWO controlled backward edges (each guarded, not free back-dependencies):
  (1) `revisit_design` = backward to Design (cascade invalidation of Safety, Logistics, Materials, DIY);
  (2) Materials→Safety single-item envelope re-open (CL-48/SI-31 — one item, not a whole-stage cascade).
- `use_economy_option` (from Logistics, SI-17/SI-34) = guided mini-revisit that REPOINTS: null chosen_design →
  re-copy economy option → set active_option_role=economy → reactivate economy's RETAINED analysis (always
  present — economy analyzed eagerly, OM-6); safety re-verifies on switch. NOT destroy-and-recompute, NOT a backward edge to Design.
- DESIGN PASSES (SI-34): 4-pass HARD CAP {preferred, economy, design_3, design_4}, design_3/4 user-directed.
  Switching among these = REPOINT active analysis (retained per option_role, no loss). revisit_design (new
  geometry) = DISCARD superseded options' retained analyses + draws one pass. Cap exhausted → no more passes;
  route to choose-existing or proceed_with_budget_gap.
- REDESIGN triggers (revisit_design) allowed from: Design stage (iteration loop) and Materials ONLY (cost is
  final/itemized there — not Safety/Logistics which run on estimates). Materials-triggered redesign → back to
  Design, discard superseded analyses.
- `diy_planning`: entered after Contractor Validation ONLY if DIY-scoped work exists; else skipped to Synthesis.
  DIY discussion refines procedure only — NO reclassification, NO backward cascade from DIY (SI-26).
- `proceed_with_budget_gap` = forward to Synthesis, bypassing Materials + Contractor Validation + DIY Planning.
- Every forward transition requires the source stage's gate satisfied.
- `complete` is TERMINAL (SI-34): no restore-into-complete; a delivered plan requires a fresh run to change.
- Session-restore = load/validate/re-walk per Global Model (SI-4) with the RESTORE-CONFIRMATION (RC) pattern
  (in-progress dossiers only — see terminal rule above):
  each stage asks one confirmation before its topics — no change → re-confirm in passing, SKIP topics, advance;
  change → reopen + cascade all DOWNSTREAM stages (dependency-chain scope from the changed stage down, NOT the
  whole pipeline, NOT just the touched field). Safety ALWAYS re-derived regardless of answer. Reopen sets
  confirmation_revoked=true; reopened/invalidated sections must be re-confirmed before their gate reopens.
- Code-level validations (not annotation-only, SI-29): allergy↔material screen (SI-6); allowance unit-match
  (SI-16); material-selection envelope check (SI-31, breach → one-item Safety re-open).
- Two-tier material store: curated (trusted/frozen) vs suggested (review queue); no auto-promotion (SI-23).
- (Full transition table + guard conditions: dedicated orchestration-spec pass, after question bank.)

## Elicitation / topics

## STAGE 8 — SYNTHESIS   (compile → present; one rich PDF, both outcomes)

Terminal stage. Assume known (SI-5): the entire dossier. Compiles — elicits almost nothing. Refs: SI-27 (one PDF,
encouraging-but-honest), RD-5 (advisory checklist carries through), materials xlsx delivered as a SEPARATE artifact alongside the PDF, not referenced inside it (CL-21/CL-76). Two reachable outcomes: `full_plan` (verdict proceed / use_economy_option / DIY complete) or
`plan_with_budget_gap` (arrived via `proceed_with_budget_gap` — bypasses Materials/Contractor/DIY).

Topics: X1 plan assembly · X2 outcome framing · X3 deliver + confirm.

---

### X1. Plan assembly  [compile → present]
**Intent:** assemble the single family-facing PDF — safety callouts FOREMOST, then design, logistics, materials
(referenced), contractor advisory, DIY procedures; phase checklists included.
**Seed:** "Here's your complete plan in one document — safety first, then the design, budget, materials list, and your contractor checklist. It's yours to keep, share, or sleep on."
**Follow-ups:** safety findings carry through UNCHANGED (SI-27); PDF does NOT embed line items NOR reference a spreadsheet; the materials xlsx ships as a SEPARATE artifact alongside it (CL-76). PDF order is safety-forward (summary+design → safety/permit near top → budget → logistics → quote audit → DIY → advisory → phase checklists). TWO INDEPENDENT gates: phase checklists ⟺ `design_accepted`; budget_gap_bridge ⟺ `has_budget_gap`.
**Good-answer cue:** `pdf_ref` generated; safety foremost; advisory checklist carried through; `phase_checklists` populated ⟺ design_accepted; `budget_gap_bridge` ⟺ has_budget_gap.
**Notes:** compile, don't re-elicit. Use pdf skill when building.

### X2. Outcome framing  [present; SI-27 — the encouraging-but-honest moment]
**Intent:** label the outcome and frame it honestly — full plan, or full plan + gap-to-bridge.
**Seed (full_plan):** "You're set — everything's in place to move into execution."
**Seed (plan_with_budget_gap):** "You've got the complete plan. There's a gap of [$X] between it and your ceiling — here's how to bridge it: [raise budget / phase the work / value-engineer / the economy option stands ready]. This isn't a dead end; it's the on-ramp."
**Follow-ups (SI-27):** budget_gap_bridge at END, never leading; "gap to bridge," NEVER "not feasible." TWO independent gates — checklist ⟺ accepted a design; bridge ⟺ a gap exists. Rejected-all (gap or not) → preferred design shown, NO checklist; bridge only if a gap exists.
**Good-answer cue:** `outcome` set; if gap → `budget_gap_bridge` (gap_amount, bridge_options) at PDF end.

### X3. Deliver + confirm  [the gate]
**Seed:** "Anything you want walked through before we call this done?"
**Good-answer cue:** PDF delivered; family has what they need; `user_final_verdict`. current_stage → complete.

---

### GATE (Synthesis)
PDF assembled — safety foremost, phase checklists (⟺ design_accepted), advisory carried through, materials xlsx shipped SEPARATELY not referenced in-PDF (CL-76) (X1);
outcome labeled + framed, gap-bridge at end if applicable (X2); delivered (X3). Gate opens + `user_final_verdict` → complete.
**On restore (RC):** terminal stage — regenerates from the (re-confirmed) dossier; no downstream to cascade.
