# Pending Architectural Decisions & Issue Backlog

This document tracks unresolved design points and spec-conformance gaps to be
revisited. Findings from the 2026-07-06 full stage-by-stage conformance audit
(implementation in `src/` vs spec in `.agents/`, `.specify/`, `research/`) are
consolidated below and ranked by severity.

---

## ✅ Resolved on 2026-07-06 — new DIY / Contractor per-item decision flow

Redesigned and shipped the DIY/Contractor experience. Verified end-to-end live
against real Vertex AI (all three routing paths). Suite: **142 passed / 1 skipped**;
new coverage in `tests/unit/test_diy_contractor_flow.py` + updated
`tests/integration/test_full_pipeline_walk.py`.

**Root cause of the tier_2 complaint (FIXED).** `diy_self_perform_consent` was a
**dead field** — defined on `TierClassification`, read only in
`should_skip_diy_planning`, and **never written anywhere**. So every Tier-2 item was
permanently `False` → structurally excluded from DIY → the agent deferred it to
Safety/professional with no procedure. Tier-2 is DIY-able *with a permit*; it should
always have been eligible.

**New model.**
* **DIY eligibility = ALL non-Tier-1** (Tier-2 + Tier-3), via `diy_eligible_items()`.
  The dead consent gate is gone; the real decision is made per item in the loop.
* **Contractor = all-or-none.** New `ContractorValidationStage.wants_diy`. Chips
  "I'll do the eligible work myself" / "Use contractors for everything".
  `wants_diy=False` skips DIY entirely → straight to Synthesis.
* **DIY = one item per loop.** Skeletons seeded from Safety (`_seed_diy_skeletons`),
  `active_item` pins the current item; the agent authors tools+procedure for THAT
  item only. Per-item chips: can-do (`user_feasible=True`) / refine (loop, capped ~3)
  / can't (`user_feasible=False` + `reclassify_to_professional`). Atomic per item
  (no partial hand-off within a Safety bundle). Tier-2 procedures carry the permit
  hold-point.
* **Synthesis split.** `diy_scope` (self-perform) vs `contractor_scope_additions`
  (handed back — surfaced as "Add to your contractor's scope", never dropped). PDF
  section 6 shows self-perform steps/tools; 6b lists the hand-offs.

**Two live-only bugs found & fixed during verification:**
* First DIY item's steps were lost — it is presented in the stage-entry greeting
  (never extracted) and the decision moved the loop on before capture. Fix: extract
  the DIY stage right after its entry greeting (`main.py`).
* Extraction rewords item names / echoes several procedures, so exact-name matching
  missed. Fix: progressive matcher (exact → substring → token-overlap → sole-with-steps)
  in `_apply_diy_procedures`.

Specs rewritten: `.agents/workflows/stage-6-contractor.md`, `stage-7-diy.md`,
`.agents/skills/diy-procedure/SKILL.md`.

---

## ✅ Resolved on 2026-07-06 — live UI session hardening (extraction, advancement, UX)

Found during live browser walks and **all fixed** this session. Suite: **130
passed / 1 skipped**; new coverage in `tests/unit/agents/test_base.py`,
`tests/unit/test_orchestrator_gates.py`, and `tests/integration/test_resume_advance.py`.

### A. Live structured-extraction corruption — a whole class (FIXED)
Root pattern: `_run_live_extraction` did `model_validate` on the full stage model
and blind-copied every field, so any field the LLM omitted or echoed imperfectly
corrupted state. Each surfaced as a "gate won't pass even though I provided it."

* **Mock fabrication in live mode (FIXED).** On any extraction exception the code
  fell back to `_run_mock_extraction`, silently injecting fake data (e.g. a
  `tier_2 "Mock electrical wiring"` classification) into a *live* dossier — which
  then drove wrong gate/cascade decisions (skipped DIY). Now: on failure, preserve
  existing state, never fabricate.
* **`conversation` echo broke validation (FIXED).** The schema included
  `conversation`; the model echoed it with `at: null` → datetime validation error →
  mock fallback. Now `conversation` is stripped from the extraction schema and from
  `extracted_data` before validation.
* **List fields clobbered to `[]` (FIXED).** An omitted list (options, rooms,
  classifications, line_items, procedures) was refilled from `default_factory` `[]`
  and overwrote captured data → "Design choice lost between Design→Safety." Now
  lists are only overwritten when the model actually sends a non-empty one.
* **Dict fields clobbered (FIXED).** Same for `disruption` (logistics
  `can_live_through_it`) — now merged, not replaced.
* **Field carve-outs (FIXED).** Extraction prompt now guarantees capture of fields
  the USER-only bias was dropping: allergies→`[]` (SI-6), `disruption.can_live_through_it`
  (M5/L2), and the **agent-deliverable carve-out** (diy `procedures`, design
  `options`, safety `classifications`, materials `line_items`, contractor
  `coverage_check`) — the agent's own structured output, previously ignored as
  "AGENT content."

### B. Deterministic passes replacing LLM inference (Principle 9) (FIXED)
* **`chosen_design` binding (FIXED).** No longer reconstructed by the LLM (it
  mislabeled/omitted nested data); `_apply_design_choice` rebinds the chosen option
  to the authoritative `options[]` entry by role/label.
* **Materials allergy screen (FIXED).** `screen_material_allergy` was exported but
  never called in live flow, so `allergy_screened` stayed `False` and Materials
  never advanced. `_apply_materials_allergy_screen` now runs the 3-state screen per
  line item against the Scope allergy profile (`[]`→clear all; named allergen→flag;
  `None`→leave unscreened so SI-6 keeps the gate closed).

### C. Stage advancement (FIXED)
* **Resume never advanced (FIXED).** Advancement only fired on the
  `[APPROVE_STAGE_TRANSITION]` tag, which a resumed session never re-emits. Now
  advances on the tag **or** when `evaluate_stage_gate` already holds.
* **`user_final_verdict` no longer inferred by extraction (FIXED).** It is set only
  by the explicit tag (or `/advance`) — extraction inferring it from agreeable
  phrasing caused premature advancement. This also makes the resume gate-advance
  safe.
* **DIY gate requires ≥1 procedure (FIXED).** Prevents an empty "DIY plan"; paired
  with the agent-deliverable carve-out so procedures reliably populate.

### D. Behavior & output hygiene (FIXED)
* **Stage scope discipline (FIXED).** New `behavior.md` rule: an agent must not
  produce a later stage's deliverable (e.g. DIY procedures during Safety); it defers
  and names the stage. Aligned with constitution Principle 1 (Tier-1 firewall still
  absolute at every stage).
* **Internal reference codes leaking (FIXED).** Contractor stage emitted `RD5-A9`,
  `RD5-D` etc. Broadened the "No Internal References" rule to cover RD-n/CL/TS/OM/DM
  codes, plus a deterministic `_scrub_internal_refs` scrub on all agent chat output
  (defense-in-depth).
* **Literal `\n` in UI (FIXED).** Model emitted literal `\n`; `_normalize_agent_text`
  converts escape sequences to real breaks and collapses blank-line runs.
* **Confusing gate warning (FIXED).** Reworded from "you still need to provide X"
  (which blamed the user for system-side capture gaps) to a non-blaming
  finalization prompt with accurate per-stage hints; a "yes, proceed" re-confirm
  re-runs extraction.

### E. Performance (FIXED — see P1 below, now resolved)
Post-chat extraction latency (~18s) cut via `disable_thinking` + `json_output` on
the extraction call and skipping extraction on trivial acknowledgement turns.

### F. Frontend UX (FIXED — static assets)
Frozen pipeline header (app-shell layout) with clear stage states (green ✓ +
filled connectors + pulsing active); "thinking…" indicator with rotating phrases
while awaiting a reply; terminal "plan complete" end-screen that clears the
localStorage token after download (server checkpoint kept for Restore PDF); tagline
updated.

---

## ✅ Resolved on 2026-07-06

These runtime blockers were found and fixed this session (all 46 tests pass; a
live grounded Vertex call was verified):

1. **LLM SDK consolidation (was Pending #2).** Migrated `src/agents/base.py` off
   the deprecated `google.generativeai` + `vertexai` split onto the unified
   **`google-genai`** SDK. One client path serves both AI Studio (`GEMINI_API_KEY`)
   and Vertex AI (ADC); grounding uses `types.Tool(google_search=GoogleSearch())`,
   valid on both backends. `requirements.txt` updated. This fixed the
   `google_search_retrieval is not supported` / `Unknown field ... google_search`
   errors, whose root cause was the AI Studio path sending the legacy
   `google_search_retrieval` tool to a modern model.
2. **Grounding removed from extraction.** `_run_live_extraction` now calls the
   model with `use_grounding=False` — structured JSON extraction must not carry a
   search tool.
3. **Materials runtime crash.** `_create_default_stage_object("materials")` used
   non-existent `MaterialTotal(materials_allowance=…)` fields and `_run_mock_extraction`
   assigned to a non-existent `stage_obj.totals`. Corrected to the real
   `MaterialTotal(low/high/allowance_portion/diverges_from_refined)` and
   `stage_obj.final_total`. (Previously crashed every Materials-stage walk.)
4. **Synthesis terminal crash.** `main.py` set `stage_obj.user_final_verdict = True`
   on the current stage, but `SynthesisStage` has no such field → `ValueError` /
   unhandled 500 at synthesis→complete. Guarded both sites with `hasattr(...)`.
5. **Model 404.** `GEMINI_MODEL` was `gemini-3.5-flash`, which returns 404 in
   `us-central1` for this project. Set to **`gemini-2.5-flash`** (verified accessible;
   `gemini-2.5-pro` also works; `gemini-3.x`/`gemini-2.0-flash` are not provisioned).
   Code default in `config.py` updated from stale `gemini-1.5-pro`.

---

## ✅ Resolved on 2026-07-06 — HIGH + MEDIUM conformance pass

All 10 HIGH and 9 MEDIUM findings below are now implemented and covered by
regression tests (suite: 80 passing). Tests live in
`tests/unit/test_orchestrator_gates.py`, `tests/unit/agents/test_injection_fence.py`,
`tests/unit/tools/test_pdf_xlsx_generator.py`, and the end-to-end
`tests/integration/test_full_pipeline_walk.py` (scope→complete). Each maps to an
acceptance scenario (TS-n) where one exists.

HIGH: H1 deterministic RD-2 ballpark + reality-check (`tools/pricing_ballpark.py`);
H2 scope gate (budget target+ceiling, resolved reality-check, goal/area/allergies);
H3 Tier-1 `depth_consent` (None blocks, False is a valid held state); H4
`user_permit_consent` gated on `permit_required`; H5 single-item Materials→Safety
envelope-breach reopen (`reopen_safety_for_material_breach`, TS-25); H6 contractor
gate (advisory checklist always, coverage audit when quoted); H7 untrusted-quote
fence in the prompt (`_fence_untrusted_quote`, TS-5); H8 synthesis structured writes
(`populate_synthesis`); H9 artifact ref persisted + terminal gate requires PDF +
verdict; H10 safety-forward PDF with all sections + SI-15 disclaimer (also fixed a
latent crash on design options).

MEDIUM: M1 design economy option required; M2 design measurements required; M3 revisit
discards `retained_analysis`; M4 DIY-skip keyed on per-item `diy_self_perform_consent`
(new schema field, TS-8); M5 logistics gate (live-through-it + displacement); M6
missing RD references added to design/materials/contractor/diy cards; M7 design &
logistics grounding disabled (frozen-reference discipline); M8 contractor gains the
`safety-tier-classification` spine; M9 phantom `displacement_need` removed.

Schema bumped to 1.1.0 (added `TierClassification.diy_self_perform_consent` and
`SynthesisStage.user_final_verdict`). Constitution/behavior cross-links added.

**Two additional bugs found during the live click-through (real Gemini) and fixed:**
- **Allergies carve-out not resolved by live extraction.** The scope gate correctly
  blocked on `allergies = null` (SI-6), but the LLM extraction wasn't converting "no
  known allergies" into a confirmed `[]`. Added an explicit allergies-carve-out rule
  to the extraction prompt in `_run_live_extraction`. Verified: gate opens, advances.
- **DIY→Synthesis chat transition crashed** (`'SynthesisStage' object has no attribute
  'conversation'`). The auto-advance seed-greeting in `main.py` assumed every stage has
  a conversation log; SynthesisStage (terminal mirror) does not. Guarded the seeding
  with `hasattr`. Regression test: `tests/integration/test_chat_synthesis_transition.py`.
  This bug had made `complete` unreachable via the UI.

Full live walk (scope→complete on real Vertex) now passes; artifacts verified
(safety-forward PDF, all 9 sections, embedded dossier.json, XLSX). Captured as a
guarded suite: `tests/e2e/test_live_walk.py` (run with `RUN_LIVE_E2E=1`).

Remaining open: the LOW / hygiene items and cross-cutting themes below.

---

## Mostly resolved — one sub-item still parked

### P1. Latency & Token Performance Optimization — ✅ FIXED (extraction latency); GCS cache still parked

**Root cause (measured, not GCS).** A single chat turn observed at ~18s between
`Executing post-chat structured parameter extraction pass` and the stage state
change. That window contains exactly one thing: the **second, hidden Gemini
round-trip** in `_run_live_extraction` (`base.py`). Every user message costs two
sequential LLM calls — `run_chat()` (visible reply) + the structured-extraction
pass. This is stage-agnostic: both methods live only in `base.py` with no
subclass overrides, so **all 8 stages** paid it. The extraction leg was slow
because (1) `gemini-2.5-flash` runs with its default dynamic **thinking budget**
even for a purely mechanical JSON pass, (2) the prompt embedded the full stage
JSON schema plus the conversation twice, and (3) output was free-text JSON that
was string-parsed out of markdown fences.

**Resolved (A + B + C).**
* **A — thinking disabled on the extraction call.** New `disable_thinking` param on
  `execute_vertex_call` sets `ThinkingConfig(thinking_budget=0)`; extraction opts
  in. Biggest single latency cut. `run_chat` is untouched (visible reply keeps
  thinking).
* **B — forced JSON output.** New `json_output` param sets
  `response_mime_type="application/json"`, eliminating the fragile fence-parsing.
  **Deliberately did NOT pass a rigid `response_schema`:** the stage models have
  required, non-nullable fields (`budget_target`, `project_title`,
  `ballpark_estimate`, …), and schema-constrained decoding would pressure the
  model to fabricate unprovided values — a Principle 10 / SI-6 violation. The
  schema stays in the prompt as guidance so unknown fields remain null, and
  `model_validate` + mock fallback still governs.
* **C — skip extraction on trivial turns.** `_is_trivial_ack()` short-circuits the
  round-trip when the latest user turn is a bare acknowledgement ("ok",
  "proceed", …). Safe because extraction is cumulative over the full history
  (idempotent) — any digit or content beyond a fixed ack set makes a turn
  non-trivial, so no parameter-bearing message is ever skipped.
* **Tests**: `tests/unit/agents/test_base.py` — `_is_trivial_ack` true/false
  tables, extraction-skipped-vs-runs, and config assertions (thinking_budget=0 +
  JSON mime on extraction; both `None` on default chat calls).

**Still parked (not yet done):**
* **GCS write/read latency** in the synchronous chat loop — bypass via an
  in-memory (or Redis) cache for active turns, flushing checkpoints
  asynchronously. Independent of the extraction-call fix above.
* **D (not done, intentional)**: disabling thinking on `run_chat` too. Would cut
  the *other* call but touches user-facing tone/quality — left on unless we
  decide the visible replies don't need reasoning.

---

## ✅ Resolved — HIGH severity (implementation detail / changelog)

All items below are fixed and tested (see the resolution summary above).

### H1. Scope ballpark & budget reality-check are fabricated, not computed
`base.py` sets the ballpark to `budget_target ± 2000` and hardcodes
`budget_reality_check = "plausible"`, `budget_reality_resolved = True` regardless
of the numbers. Violates Constitution Principle 9 (numbers from curated RD-2
references via deterministic tools, not the LLM/heuristics) and Principle 10
(honest, calibrated framing). Consequence: the T1a recalibration loop can never
fire, and the mock chat text can say "unrealistic" while the field says "plausible".
**Fix**: compute the ballpark from RD-2 (per-sqft ROM × area × regional factor)
using the `tools/` calculators; derive the reality-check verdict from real numbers.

### H2. Scope gate omits most spec exit conditions
`orchestrator.py` scope gate enforces only `budget_target > 0`, the unrealistic-block,
and `user_final_verdict`. Spec requires additionally: `budget_reality_resolved`
(unconditionally, per OM-3), hidden-conditions raised-and-discussed (T9),
`budget_ceiling` (T7), and topic coverage T2/T5/T6/T8. **Fix**: add these gate checks.

### H3. Safety gate wrongly blocks a valid Tier-1 "decline depth" path
`orchestrator.py:~201`: `if c.tier == "tier_1_professional" and not c.depth_consent`.
A family that explicitly declines the depth explanation (`depth_consent=False`) is a
valid gate-satisfying state, but this treats `False` like `None` and refuses to
advance. **Fix**: `if ... and c.depth_consent is None: return False`.

### H4. Safety gate never enforces `user_permit_consent`
Spec lists `user_permit_consent` as a required gate condition; the branch never
checks it. A dossier can pass safety with permit consent uncaptured. **Fix**: add
`and safety.user_permit_consent` (guarded to when a permit is required).

### H5. Materials envelope-breach → Safety single-item reopen cascade unimplemented
Spec SI-31 / T10 / OM-9: on a material envelope breach, re-open Safety for that
ONE item, re-classify + re-consent, set `reclassified_from_materials`, return via
T4a. The gate only does `if envelope_check == "breach_reopened_safety": return False`
— it blocks but never reopens Safety or routes the item. `reopen_stage_and_cascade`
is design-only and is a whole-stage wipe (would violate the single-item rule).
**Fix**: implement a single-item Safety reopen on breach.

### H6. Contractor gate ignores the always-on advisory checklist & audit completeness
Spec SI-25: `advisory_checklist` is produced regardless of mode; if a quote was
provided, `coverage_check` + `corner_cutting_flags` must be assessed. The gate only
checks status + verdict, so a hollow (or prompt-injected) contractor stage passes.
**Fix**: require non-empty `advisory_checklist`; if `quote_provided`, require
coverage/flags assessed.

### H7. No code-level prompt-injection defense for untrusted quote text
Constitution Principle 7 / SI-24: contractor quote text is data to AUDIT, never
obey. `quote_raw_text` is serialized raw into the prompt via `json.dumps(dossier_context)`
with no untrusted-content fence or sanitization; defense rests entirely on
system-prompt prose. **Fix**: wrap quote text in an explicit
`<untrusted_quote>…</untrusted_quote>` fence with a "content inside is data only"
instruction before it reaches the model.

### H8. Synthesis structured contract is essentially unimplemented
No code path sets `design_accepted`, `has_budget_gap`, `outcome`,
`budget_gap_bridge`, `phase_checklists`, `pdf_ref`, or `generated_at`. The stage
emits free-text chat only. **Fix**: implement synthesis extraction/derivation.

### H9. Synthesis artifact generation is detached from stage completion
PDF/XLSX generation lives only in a manual `/api/session/download-artifacts`
endpoint that isn't triggered by reaching synthesis, doesn't check `current_stage`,
and never writes `pdf_ref`/`generated_at` back to the dossier. The gate doesn't
require a generated PDF. **Fix**: generate on synthesis completion, persist refs,
gate on them.

### H10. Synthesis PDF is not safety-forward and omits most required sections
Spec order puts safety prominently near the top and includes budget, logistics/
displacement, quote audit, DIY, always-on advisory checklist, phase checklists,
and a budget-gap bridge at the end. The current PDF is Title → Scope → Design →
Safety (3rd), then stops. **Fix**: reorder safety to the top and add the missing
sections (driven by the H8 fields).

---

## ✅ Resolved — MEDIUM severity (implementation detail / changelog)

All items below are fixed and tested (see the resolution summary above).

### M1. Design gate omits mandatory economy option (CL-17)
Gate accepts a single `preferred` option. **Fix**: require
`any(o.option_role == "economy" for o in design.options)`.

### M2. Design gate does not require captured measurements (`rooms`)
Spec makes captured room measurements a hard gate condition. **Fix**: require
non-empty `design.rooms`.

### M3. E1 design revisit does not discard superseded retained analyses (SI-34)
`reopen_stage_and_cascade` clears only downstream stages; stale
`design.retained_analysis` for superseded roles persists. **Fix**: prune on E1.

### M4. DIY-skip predicate conflates permit consent with self-perform consent
`should_skip_diy_planning` uses `safety.user_permit_consent` as the Tier-2 proxy,
but that flag means "family will obtain permits", not "family will self-perform".
No per-item self-perform flag exists on `TierClassification`. Result: routing into
DIY when the family intends to hire out. **Fix**: add a per-item self-perform
signal and key Tier-2 DIY eligibility on it. (Affects Safety + DIY.)

### M5. Logistics gate enforces no domain invariants
Gate checks only status + verdict; spec requires disruption assessed, both
feasibility booleans computed, verdict set, and the CL-47 over-ceiling loop.
**Fix**: assert feasibility/verdict/disruption are populated and consistent.

### M6. Missing frozen references on agent cards
Design lacks RD-2 (needed for refined estimates); Materials lacks RD-2/RD-4/RD-1;
Contractor lacks RD-2/RD-3 (for the low-bid cross-check); DIY lacks RD-3. **Fix**:
add the references so the relevant tables reach the prompt.

### M7. Questionable grounding on frozen-reference stages
Design and Logistics set `search_grounding_enabled=True`, risking live pricing
leaking into estimates the spec says must come from RD-2. Materials/DIY grounding
is legitimate (live availability/tool rental). **Fix**: set Design/Logistics to
`False` or confine grounding to non-numeric research.

### M8. Contractor: missing skills & no PDF quote ingestion
Card lacks `safety-tier-classification`; no `advisory-checklist` skill folder
exists; no PDF-to-text extraction path for uploaded quotes (with an
unreadable→advisory-only fallback). **Fix**: author/attach the skills; implement
quote ingestion.

### M9. Logistics phantom field
`_create_default_stage_object("logistics_feasibility")` sets `displacement_need`,
which is not a field on `LogisticsFeasibilityStage` (silently dropped under
Pydantic `extra="ignore"`). **Fix**: remove it or populate the real `disruption`.

---

## Open — LOW severity / hygiene

### L1. Duplicate skill/reference hydration
`REF_MAP` maps RD-n to the same folder as an `associated_skill` on several cards
(scope→pricing-ballpark, safety→irc-safety, materials→material-bands,
contractor→quote-audit), so `SKILL.md` is injected twice. Dedupe by resolved
folder in `compose_system_instructions`, and treat RD-n as reference-only.

### L2. DIY gate under-enforcement + redundant check
Gate doesn't require `tools_required` populated or each procedure's feasibility/
opt-out recorded; the Tier-1 check is unreachable (schema `Literal` already
forbids `tier_1_professional`). Harmless but note as defense-in-depth.

### L3. Synthesis: missing framing skill + SI-15 disclaimer
No honest-conclusion/budget-gap-bridge framing skill exists/attached; the PDF
lacks the SI-15 "estimates, verify locally" cost disclaimer near cost figures.

### L4. Lint & deprecations
11 pre-existing ruff findings remain (E402 import placement in `main.py`, 2× B904
`raise ... from`, B008 `File()` default, F841 unused vars). Codebase-wide
`datetime.utcnow()` is deprecated — migrate to `datetime.now(datetime.UTC)`.

---

## Cross-cutting themes (worth a design decision)

* **Gates broadly under-enforce.** Most stage gates check only `status` +
  `user_final_verdict`, delegating correctness to the LLM/user instead of
  validating computed invariants. Consider a consistent "gate = validate the
  spec's postconditions" policy.
* **Deterministic math is bypassed.** `tools/` calculators exist, but stages
  fabricate numbers (scope ballpark, reality-check). Route all numeric outputs
  through the tools per Constitution Principle 9.
* **Silent schema drift.** Pydantic models declare no `model_config`, so
  `extra="ignore"` silently drops mis-named kwargs (this hid H3-class bugs).
  Consider `extra="forbid"` (at least in tests) to surface them, plus a test that
  round-trips each stage through `_create_default_stage_object` +
  `_run_mock_extraction` to catch field mismatches before runtime.
