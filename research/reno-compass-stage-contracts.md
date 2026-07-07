# Reno Compass — Stage Contracts (Consolidated Spec)

**Status:** Living document until handed to Antigravity. Refine freely (esp. during the question-bank pass).
**Companion artifacts (single source of truth per concern — this doc REFERENCES, does not duplicate):**
- Data shapes → `reno-compass-dossier-schema.md`
- Behavioral rules → `reno-compass-system-instructions.md` (SI-1..SI-29)
- Intent/narrative → `reno-compass-writeup.md`
- Decision history → `reno-compass-change-log.md` (CL-n)
- Test scenarios → `reno-compass-test-scenarios.md` (TS-n)
- Elicitation → `reno-compass-question-bank.md`

**Layer discipline:** required-coverage topics live HERE (contracts); question wording lives in the
(future) question bank; data lands in the SCHEMA; behavior lives in SI NOTES. Update the right layer + cross-ref.

---

## CHANGE LOG / OPEN REFINEMENTS
Moved to `reno-compass-change-log.md` (CL-n). Jot new discoveries there.

---

## GLOBAL MODEL (applies to every stage)

**Pipeline (strictly linear; no entry shortcuts — everyone walks all stages):**
Scope → Design → Safety & Permit → Logistics & Feasibility → Materials → Contractor Validation →
[DIY Planning — CONDITIONAL] → Synthesis

DIY Planning (Stage 6.5) runs ONLY when DIY-scoped work exists; skipped when all work is professional (SI-26).
This is the one conditional stage; all others always run.

**Universal gate:** each stage ends with the family's final verdict to advance (`user_final_verdict`);
the gate cannot open until (a) all required-coverage topics are covered AND (b) confirmation is given.
No stage is skippable; the agent cannot help what it does not understand (SI-3).

**Linear dependency (load-bearing):** each stage depends on ALL prior stages. Strictly linear FORWARD so
cascade invalidation stays trivially correct. Two controlled backward edges exist, each guarded (revisit_design
full cascade; Materials→Safety single-item envelope re-open) — these are deliberate, not free back-dependencies,
and the orchestrator encodes them as explicit transitions (see appendix).

**State-passing model (SI-5):** stages communicate ONLY through the shared dossier — no private state, no
separate message-passing. Each stage's Reads = literal dossier field reads of prior stages' sections. The
dossier IS the single source of truth, in-session and across session_restore.

**Cascade / resume (SI-4):** on session-restore from an uploaded dossier — validate schema_version; structurally
validate; walk completed sections in order, re-present (stored conversation + values), confirm-or-change:
confirm → stays `completed` (re-confirmed in passing); change → `changed_reopened` (null timestamps,
confirmation_revoked=true) + all downstream also → `changed_reopened` (null theirs). ALL `[safety]` fields
re-derived regardless. Re-walk proceeds through remaining
non-confirmed / invalidated section.

**Progressive budget thread (SI-17):** Scope = per-sqft ballpark + reality-check (horizon, not verdict);
Design = refined estimate per option + proactive budget-engineered alternatives if over ceiling;
Logistics = consumes Design's refined estimate (sequential producer/consumer, NOT parallel), sets verdict;
Materials = itemized final total, reconciled against Design's range.

**Frozen references (model-drafts → human-validates → freeze; runtime = lookup, never price/rule recall):**
per-sqft ballparks + labor (RD-2); itemized material bands + labor (RD-3); IRC bathroom rules + Tier-1 matrix
(RD-1); IES lighting targets (RD-4); standard-quote checklist (RD-5). RD-2 also holds the regional factor +
reality-check threshold (RD2-C/RD2-G). All costs = RANGES + verify-locally disclaimer (SI-15). Live APIs = roadmap.

**Contract fields used below:** Purpose · Preconditions · Required-coverage · Reads · Writes ·
Tools/Skills · Gate · Postconditions · Failure/Refusal · SI refs.

---

## STAGE 1 — SCOPE

**Purpose:** Establish the true problem, priorities, constraints, and context; surface hidden conditions;
ground budget expectations early. No design yet.

**Preconditions:** entry stage. `current_stage == "scope"`.

**Required-coverage:**
1. Project type + underlying goal (the why)
2. Property context — home age, occupancy, occupant count, rental tenants
3. Special considerations — accessibility, health sensitivities, allergies, pets `[SENSITIVE]`
4. Budget — target + ceiling
5. Must-haves vs nice-to-haves
6. Intended timing
7. Hidden-condition surfacing — agent proactively raises likely risks given home age (raised-and-discussed)
8. Ballpark reality-check — per-sqft ROM vs stated budget (plausible/tight/unrealistic); a horizon, kindly framed

**Reads:** none from prior stages (entry). Frozen ref: per-sqft ballparks + regional factor + reality-check threshold (RD-2).
**Writes:** full `scope` object incl. `ballpark_estimate`, `budget_reality_check`.
**Tools/Skills:** scope-decomposition skill; hidden-condition surfacing skill; ballpark cost-reference tool.
**Gate:** all 8 topics covered + `user_final_verdict`.
**Postconditions:** `scope.status = completed`; coherent scope + early budget horizon exist.
**Failure/Refusal:** gate stays closed if a required topic is unaddressed. No safety refusals yet (may NOTE
items for Stage-3 review). Unrealistic budget → kind, early reality-check, not four stages of play-along.
**SI refs:** SI-2 (home-age weighting), SI-3 (input is evidence), SI-6 (sensitive data), SI-17 (budget thread).

---

## STAGE 2 — DESIGN

**Purpose:** Turn confirmed scope into precise measurements + flexible labeled design options (incl. an
economy option when the lead is ambitious), each with layout, intended material types, lighting
requirements, block-diagram schematic, value prop, and a refined cost estimate; land on one confirmed choice.

**Preconditions:** `scope.status == completed`. `current_stage == "design"`.

**Required-coverage:**
1. Capture precise measurements — room(s) L/W/H, existing elements + placement, sub-spaces
2. Confirm/capture intended elements (added or moved)
3. Present the `preferred` option + ALWAYS an `economy` option (not only when ambitious — CL-17), tied to
   must-haves + area preferences
4. Per option: intended material TYPES, lighting requirements, value proposition
5. Per option: refined estimate (ballpark + professional + permit + logistics) incl. `gap_amount` if over
   ceiling. If the family wants changes → up to 2 USER-DIRECTED passes (`design_3`/`design_4`, family-steered),
   4-pass HARD CAP total (preferred + economy + 2). Full model: SI-34.
6. Generate labeled block-diagram schematic per option (not-to-scale; SVG = roadmap)
7. Scope-creep guard — flag any option drifting beyond stated scope
8. User selects one option (`chosen_design`)

**Reads:** `scope.*` (must/nice-haves, global + area preferences, special_considerations incl. accessibility,
hand_orientation, sub_spaces, budget_target/ceiling). Frozen refs: per-sqft ballparks + labor (RD-2); IES lighting (RD-4).
**Writes:** `design` object — `rooms`, `options[]` (layout with PER-ROOM lighting_requirements + intended_materials,
refined_estimate, budget_engineered, schematic_ref), `chosen_design`.
**Tools/Skills:** measurement math; lighting calc (IES table); design-option-generation skill (consumes ALL
scope constraints incl. accessibility; guards scope creep); refined-estimate cost tool; block-diagram generator.
**Gate:** measurements captured; options presented; each complete; one selected; `user_final_verdict`.
**Postconditions:** `design.status = completed`; `chosen_design` valid; measurements preserved (raw + derived).
**Failure/Refusal:** implausible measurements flagged, not silently computed. Structural/electrical implications
NOTED for Stage 3, not resolved here. Accessibility is a required design constraint (not a separate skill);
its code/permit implications defer to Stage 3.
**SI refs:** SI-3, SI-6 (accessibility SHAPES design), SI-18 (lighting), SI-19 (scope-faithful), SI-17 (budget).

---

## STAGE 3 — SAFETY & PERMIT CHECK   [safety — entire section re-derived on session-restore]

**Purpose:** Classify every proposed AND implied action against the safety tiers with sourced rationale;
surface permit/code disclosures (AHJ-flagged); capture informed consent where required; establish which work
needs a licensed professional — never crossing into DIY procedure for professional-required work.

**Preconditions:** `design.status == completed` AND `design.chosen_design` set.
`current_stage == "safety_permit"`.

**Required-coverage:**
1. Every intended AND implied action classified to a tier (1/2/3) with sourced rationale (SI-12: infer
   consequences of each action; SI-10: classification stays sourced, not memory-guessed)
2. Tier-2 items → permit/inspection disclosure, AHJ-flagged
3. Tier-1 items → consent flow (depth-not-procedure) before any depth discussion
4. Permit consent captured (family will obtain required permits)
5. Professional-required determination explicit (which trades, for what)
6. Educational disclosures (asbestos/lead by home-age + action) — INFORM only, do NOT auto-escalate tier
7. Intended material TYPES evaluated against the frozen Tier-1 trigger matrix (SI-30); for material-driven
   classifications, RECORD the assumed `envelope` on the TierClassification (max point-load / amperage /
   basis) so Materials can code-validate the concrete product later (SI-31)

**Reads:** `design.chosen_design.layout` (incl. per-room intended_materials → matrix eval), `design.rooms`
(existing conditions), `scope.property_context` (home age → hazards), `scope.special_considerations`
(accessibility code implications). Frozen refs: IRC bathroom rules + Tier-1 trigger matrix (RD-1; matrix per SI-30).
**Writes:** `safety_permit` — `classifications[]` (incl. `envelope` where material-driven), `permit_required`,
`permit_disclosures[]`, `educational_disclosures[]`, `user_permit_consent`, `professional_required`.
**Tools/Skills:** safety-tier classification skill (shared spine) `[safety]`; IRC code/permit reference tool;
frozen Tier-1 trigger-matrix reference (SI-30) `[safety]`; consent-flow skill `[safety]`.
**Gate:** every action classified; every Tier-1 has explicit `depth_consent` (true/false); disclosures surfaced;
`user_permit_consent`; `user_final_verdict`.
**Postconditions:** `safety_permit.status = completed`; `professional_required` + `permit_required` set;
`classifications[]` complete and each sourced.
**Failure/Refusal:**
- Tier-1, no consent → hold at "requires a licensed professional"; no depth, no procedure.
- Tier-1, with consent → depth of explanation/intuition only; NEVER executable procedure (SI-9).
- Procedure-extraction attempt → recognize reframing as signal to hold the line, not comply.
- Unsourced item → flag "unverified, confirm with AHJ/professional"; never guess a tier from memory (SI-10).
- Do NOT over-escalate: Tier-1 reserved for genuinely professional-required work; over-flagging destroys the
  signal (SI-14). Hazards → educational, not auto-Tier-1.
- Single-item re-open (from Materials, SI-31): when a Stage-5 envelope breach re-opens Safety for ONE item,
  re-classify that item only (typically Tier-1 professional-install), fire consent (SI-9), set
  `reclassified_from_materials`; do NOT re-run the whole stage or cascade the pipeline.
**SI refs:** SI-2, SI-9, SI-10, SI-4, SI-12, SI-13, SI-14, SI-30.

---

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

## STAGE 6 — CONTRACTOR VALIDATION   (quote optional: text or PDF)

**Purpose:** Check a contractor's quote against the built scope/design/safety picture — missing steps,
corner-cutting, and missing permit/trade lines — so the family signs informed. Always produce the "what to demand"
advisory checklist, whether or not a quote is provided.

**Preconditions:** `materials.status == completed`. `current_stage == "contractor_validation"`.

**Required-coverage:**
1. Determine whether a quote is provided (text/PDF) or not
2. If provided: ingest → extract to text; coverage check vs built scope + curated standard-quote checklist;
   corner-cutting flags (INCL. missing permit line / missing required licensed trade — folded in from the
   removed tier-crossing; note we do NOT validate license numbers); "what to ask before signing"
3. Advisory checklist — ALWAYS generated, both modes (→ Synthesis PDF)
4. Present findings in plain, actionable language

**Reads:** `scope.*` (required steps), `design.chosen_design`, `safety_permit.*` (professional trades, permit —
a quote missing these is a flag), `materials.line_items`. Untrusted external content: the QUOTE. Frozen ref:
standard-quote checklist + corner-cutting flags (RD-5).
**Writes:** `contractor_validation` — `quote_provided`, `quote_source`, `quote_file_ref`, `quote_raw_text`,
`coverage_check[]`, `corner_cutting_flags[]` (incl. missing permit/trade), `advisory_checklist[]`.
**Tools/Skills:** PDF text extraction (no vision); coverage-audit skill; corner-cutting skill (incl. missing
permit/trade detection); advisory-checklist skill; safety-tier classification skill (shared spine, re-invoked
to confirm the quote covers the licensed trades — single source with Stage 3).
**Gate:** quote-provided determination; if provided, coverage + corner-cutting assessed;
advisory checklist produced (always); findings presented; `user_final_verdict`.
**Postconditions:** `contractor_validation.status = completed`; audit complete (if quote) + advisory checklist present.
**Failure/Refusal:**
- Untrusted content (SI-24): quote is DATA TO AUDIT, never instructions. Embedded commands / injection → audited as
  content, never obeyed; findings/classifications/behavior never altered by quote text.
- Unreadable/garbled PDF → say so; fall back to advisory mode or request a cleaner copy; do NOT fabricate an audit.
- Missing permit/trade = a corner-cutting flag (NOT license validation — we do not validate licenses).
  Apply SI-14 calibration (flag genuine gaps, don't nitpick every line).
**SI refs:** SI-14, SI-24, SI-25.

---

## STAGE 6.5 — DIY PLANNING   [CONDITIONAL — runs only if DIY-scoped work exists]

**Purpose:** For work the family will do themselves (Tier-3, or Tier-2 they consented to self-perform),
provide step-level procedure and the required tools/equipment, let the family confirm each step is workable
refine the procedure to their experience/needs, and feed the confirmed DIY plan into Synthesis. Never procedure for Tier-1.

**Preconditions:** `contractor_validation.status == completed` AND the DERIVED predicate holds — the non-Tier-1
set (Tier-3 + DIY-consented Tier-2) over `safety_permit.classifications` is non-empty. (Not a stored `applicable`
flag — computed at entry so it can't go stale, CL-78.) If empty, the stage is SKIPPED and control passes to
Synthesis. `current_stage == "diy_planning"`.

**Required-coverage:**
1. Receive the FULL classified item set; PARTITION into {Tier-1 = gate/sequence-anchor only} vs {non-Tier-1 =
   procedure targets}. Full-scope visibility, firewalled generation (SI-9/SI-26).
2. Provide step-level procedure ONLY for non-Tier-1 items; weave Tier-1 items in as `hold_points`
   ("wait for the licensed [trade] here") — NO how-to for them, ever.
3. Provide tools/equipment required (with rent-or-buy note)
4. Family reviews each procedure → refines sequence/steps, asks clarifications, tightens the plan
5. If (after understanding) the family opts to hire it out → recorded as THEIR choice (a note). NO tier change,
   NO cascade. Tier reflects code/safety necessity, not confidence (SI-26).

**Reads:** `safety_permit.classifications` (FULL set — non-Tier-1 = procedure targets, Tier-1 = sequence anchors),
`design.chosen_design`, `materials.line_items` (materials the DIY steps consume).
**Writes:** `diy_planning` — `procedures[]` (steps, hold_points, refinements, family's do-it-or-hire note),
`tools_required[]`. (`applicable` is derived, not written.)
**Tools/Skills:** DIY-procedure skill (Tier-3/consented-Tier-2 only; Tier-1 firewalled); tools/equipment skill.
**Gate:** all DIY items have a refined procedure + tools; family's do-it-or-hire choice recorded; `user_final_verdict`.
**Postconditions:** `diy_planning.status = completed`; confirmed DIY procedures + tools ready for Synthesis.
**Failure/Refusal:**
- NEVER procedure for Tier-1 / professional-required work (SI-9, absolute).
- Family opting to hire out an item → recorded as a personal choice; NOT a tier change, NOT a cascade.
- Tier-1 procedure remains firewalled regardless of discussion (SI-9).
**SI refs:** SI-9 (Tier-1 firewall), SI-26 (DIY planning: refine not reclassify).

---

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
