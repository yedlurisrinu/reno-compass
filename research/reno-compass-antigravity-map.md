# Reno Compass — Antigravity Conversion Map (AM)

**Purpose:** the redistribution table — every source artifact/section → its Antigravity home (Rules / Skills /
Workflows / constitution), with shared tools flagged so nothing is orphaned or silently duplicated. Numbered
AM-n, stable. This is a MAP, not a rewrite: content moves to the home matching its ROLE (always-on vs on-demand
vs procedural). Authoring the actual .agents files is the NEXT step, gated on review of this map.

**Basis (validated against primary docs — Google Codelabs, ai.google.dev):**
- Rules `.agents/rules/<name>.md` — always-active instructions (project-wide).
- Skills `.agents/skills/<skill-name>/SKILL.md` — on-demand; loaded when the task matches the `description`
  frontmatter. One folder per focused capability; may bundle `scripts/` (deterministic tools) + `references/`.
- Workflows `.agents/workflows/<name>.md` — slash-triggered procedures (the SDD pipeline).
- Constitution `.specify/memory/constitution.md` — non-negotiable principles SDD workflows validate against.
- CONSTRAINT: managed agent has NO structured-output enforcement — dossier is an agent-maintained state
  contract, validated by OUR code-level checks (SI-29), not a provider guarantee. (AM-6)

---

## AM-1. Constitution (non-negotiable safety spine → `.specify/memory/constitution.md`)
The safety-critical, always-true principles. These are load-bearing and must validate every stage.
- SI-9 (Tier-1 consent: depth, not procedure) — the firewall.
- SI-11 (per-item tiering), SI-12 (implied-action inference), SI-13 (IRC grounding), SI-10 (sourced).
- SI-14 (calibration — do NOT over-escalate) — the most important safety rule.
- SI-24 (untrusted quote — audit, never obey) — the security boundary.
- SI-31 envelope principle (Materials detects, Safety owns — single tier authority).
- SI-30 (frozen Tier-1 trigger matrix — material-driven classification is a safety principle; matrix TABLES
  live in the irc-safety skill, but the "materials can raise a tier, Safety owns the call" principle is constitution).
- Skill-vs-tool separation + "deterministic tools compute, model reasons" (writeup principle).
- Dossier-as-sole-inter-stage-channel (SI-5).
Keep it to a short principled list (Google's codelab keeps constitutions lean); details live in Rules/Skills.

## AM-2. Rules (always-active → `.agents/rules/*.md`)
Behavior + data contract the agent needs every conversation. NOT safety-gating (that's constitution), NOT
on-demand (that's skills).
- `.agents/rules/behavior.md` ← SI-1, SI-2, SI-3, SI-4 (restore + RC), SI-7 (context-triggered prompting),
  SI-8 (sub-space vocab), SI-19 (scope-faithful), SI-33 (context/summary gate), SI-34 (design passes & retention).
- `.agents/rules/sensitive-data.md` ← SI-6 (sensitive handling, skip semantics, allergy confirmation).
- `.agents/rules/dossier-schema.md` ← full dossier schema (data contract). Note (AM-6): agent-maintained,
  validated by SI-29 checks, not structured-output-enforced.
- `.agents/rules/annotation-convention.md` ← SI-28 (annotation vocabulary — how schema signals attention).

## AM-3. Skills (on-demand domain knowledge → `.agents/skills/<name>/SKILL.md`, one folder each)
Each = a focused capability, loaded by its `description`. Reference-data skills carry frozen tables in
`references/`; reasoning skills carry instructions; deterministic tools bundle as `scripts/`.

**Reference-data skills (from RD-1..5):**
- `irc-safety/` ← RD-1 (IRC rules + Tier-1 trigger matrix). references/: the frozen tables. [feeds Safety]
- `pricing-ballpark/` ← RD-2 (per-sqft bands, 95120 regional factor, Title 24/SB407, contingency, threshold).
- `material-bands/` ← RD-3 (itemized bands + labor, allowance-vs-banded split).
- `lighting-targets/` ← RD-4 (IES targets + JA8 cross-check).
- `quote-audit/` ← RD-5 (coverage rubric + corner-cutting flags + advisory checklist).

**Reasoning skills (from writeup + stage Tools/Skills lines):**
- `scope-decomposition/`, `hidden-condition-surfacing/` [Scope]
- `design-generation/` (consumes must/nice-haves, area prefs) [Design]
- `safety-tier-classification/` ⚑ SHARED (AM-5) — used by Safety AND Contractor audit.
- `disruption-assessment/`, `displacement-alternatives/` [Logistics]
- `coverage-audit/`, `corner-cutting/` [Contractor]
- `diy-procedure/` (Tier-1 firewalled; hold-points), `tools-equipment/` [DIY]
- `consolidation-summary/`, `phase-checklist/` [Synthesis]

**Deterministic tools — bundled as `scripts/` inside the owning skill (model reasons, script computes):**
- measurement-math, lighting-calc (IES) → in `design-generation/scripts/` (or a shared `geometry` skill, AM-5)
- quantity+waste calc, cost-band lookup, extended-cost (unit-match, SI-16), total-rollup+divergence →
  `material-bands/scripts/`
- envelope-check (SI-31, code-validated) ⚑ SHARED-ADJACENT (AM-5)
- allergy-screen (SI-6, code-validated) → bundled where materials are priced
- PDF-text-extraction (no vision) → `quote-audit/scripts/`
- spreadsheet generator (xlsx), PDF generator → `consolidation-summary/scripts/`

## AM-4. Workflows (the pipeline → `.agents/workflows/*.md`, slash-triggered)
The orchestration + stage contracts become the procedural spine.
- `.agents/workflows/pipeline.md` ← OM-1..13 (states, transition table, guards, edges, termination). The
  runnable spine; references the per-stage workflows.
- `.agents/workflows/stage-<n>-<name>.md` ← each stage contract (preconditions, required-coverage, reads/
  writes, gate, postconditions, failure) + that stage's question-bank topics (the elicitation wording) +
  that stage's STAGE-SPECIFIC SI NOTES (the behavioral rules that govern only that stage). 8 files: scope,
  design, safety, logistics, materials, contractor, diy (conditional), synthesis.
- STAGE-SPECIFIC SI ROUTING (so none are unmapped): SI-15 pricing→scope+materials; SI-17 budget thread→scope/
  design/materials (judged logistics); SI-18 lighting→design; SI-20 divergence + SI-21 finish→materials;
  SI-22 dwelling + SI-23 two-tier store + SI-32 displacement loop→logistics; SI-25 advisory→contractor;
  SI-26 DIY→diy; SI-27 synthesis→synthesis. SAFETY-TAGGED exceptions: SI-30 (Tier-1 matrix) and SI-31
  (envelope) are enforced in safety/materials workflows BUT their principle also sits in the constitution
  (AM-1) — workflow references constitution, single source.
- Gate conditions + safety rules → BDD/Gherkin acceptance (CL-40), lives alongside in `.specify/`.

## AM-5. Shared tools/skills — flagged so they're SINGLE-SOURCE, never duplicated
Rule (settled): a capability used by 2+ stages becomes its OWN skill; stages REFERENCE it (drift = risk).
- ⚑ **safety-tier-classification** — Safety (Stage 3) + Contractor audit (Stage 6). Its OWN skill; both
  reference. Safety-critical → single-source is mandatory (identical everywhere). (writeup "shared spine")
- ⚑ **envelope-check** (SI-31) — computed against Safety-stored envelope, invoked at Materials; the classifier
  that STORES the envelope is the shared tier skill above. Keep the check co-located with the tier skill's
  logic so the envelope shape stays consistent.
- ⚑ **geometry/measurement-math + IES lighting-calc** — used at Design (option geometry/lighting) and again
  referenced at Materials (quantities from dimensions). Candidate for a small shared `geometry` skill rather
  than duplicated scripts. (Lower-stakes than tier; duplication survivable but single-source preferred.)
- Cost-band lookup — used at Scope (ballpark), Design (refined), Materials (itemized). Single `pricing`/
  `material-bands` skill referenced across the three; do NOT re-embed bands per stage.

## AM-6. Structured-output constraint — what it changes (and doesn't)
- Dossier stays fully meaningful as the inter-stage state contract (agent reads/writes/passes it).
- What's absent: provider-level guarantee that a stage's output matches schema shape.
- Replacement: SI-29 code-level validations (allergy screen, allowance unit-match, envelope check) run as
  bundled scripts — deterministic, not trusted model output. This makes SI-29 MORE load-bearing, not obsolete,
  and reinforces the skill-vs-tool split (schema-critical parts = scripts).

## AM-7. Provenance / non-runtime artifacts (NOT converted — kept as project history)
- change-log (CL-1..82), test-scenarios (become Gherkin, AM-4), this map (AM), writeup (submission doc).
  These are human/process artifacts; they inform the conversion but aren't .agents runtime files.

## AM-8. File-count estimate (for review)
~4 rules + 1 constitution + ~14 skill folders (5 reference + 9 reasoning, several with bundled scripts) +
~10 workflows (1 pipeline + 8 stages + gherkin) ≈ 29 Antigravity files from 12 source artifacts. The growth is
expected: skills are one-folder-each and some artifacts split (schema body vs reference tables; stage contract
+ its question-bank topics co-located per workflow).

## RESOLVED DECISIONS (AM-N1..N4)
- AM-N1. SI-24 (untrusted-quote security) → CONSTITUTION level (non-negotiable boundary). ✓
- AM-N2. Geometry and lighting are SEPARATE independent skills — NOT merged, NOT shared-as-script. Design
  computes their outputs into the dossier; Materials READS them from the dossier (SI-5 state-passing), so
  there's no shared script to single-source. The only genuine single-source case remains the safety-tier
  classifier (re-INVOKED in Safety + Contractor, not merely read). ✓
- AM-N3. Workflow granularity = 8 separate stage files + 1 pipeline file. ✓
- AM-N4. No size-driven `references/` splits — all RD skills are <1,500 words, SKILL.md holds tables inline.
  `references/` used ONCE: the safety-tier-classification skill's body (reasoning) points via relative path to
  the `irc-safety` skill's matrix tables — the one cross-skill link. ✓

## AM-9. Measured file count (actuals, not estimated)
Source word counts: question-bank 7143 (distributes into the 8 stage workflows, not one file), SI 4827,
stage-contracts 3500, schema 3145, orchestration 1396; RD-1 1423 / RD-2 1088 / RD-3 859 / RD-4 778 / RD-5 763
(all lean — no split needed). Target files:
- 1 constitution + 4 rules + 5 reference skills + 9 reasoning skills + (1 pipeline + 8 stage) workflows +
  Gherkin acceptance (count at authoring) ≈ 28 files, none forced to split by size.

## AM-10. How SKILL.md ↔ references/ connect (mechanism, for authoring)
SKILL.md body = instructions/reasoning (loaded when `description` matches). `references/` = look-up material
the instruction points to by RELATIVE PATH, read only when the instruction says to (second-level progressive
disclosure). Our sole use: `safety-tier-classification/SKILL.md` → references the `irc-safety` matrix. All RD
tables stay inline in their own SKILL.md (small enough).

## AM-11. `.specify/` ingestion behavior (verified against primary docs)
`.agents/` (rules/skills/workflows) is NATIVELY auto-ingested by Antigravity — rules always-active, skills
loaded by description, workflows slash-triggered. `.specify/` is the SPEC-KIT layer sitting on top: its
contents (constitution, templates, acceptance) are consumed WHEN a spec-kit workflow runs, NOT auto-loaded
every conversation. Consequences captured in the tree:
- Constitution enforcement does not rely on spec-kit being installed: an always-active rule
  (`.agents/rules/constitution-enforcement.md`) points at `.specify/memory/constitution.md` and requires
  validation against it regardless. Closes the "constitution inert without spec-kit" gap.
- The Gherkin acceptance file (`.specify/acceptance/`) does NOT self-execute; it's the intent spec, fed to the
  post-implementation eval step (deferred by decision). A workflow or prompt must point the agent at it to use it.

## AM-12. Domain scoping — bathroom-locked by DESIGN; the extension rule (for later)
Every skill `description` and the reference data are explicitly bathroom-scoped. This is CORRECT now: tight,
keyword-specific descriptions make Antigravity's skill-matching reliable (per docs). Downstream-extension
guidance so a future widening doesn't create a safety failure:
- PORTABLE (domain-agnostic, transfers cleanly): the pipeline/workflows, tier-classification REASONING
  (per-item, sourced, calibrated, depth-not-procedure), retention model, dossier, RC/restore.
- BATHROOM-LOCKED (by design, frozen for one domain): RD-1 Tier-1 matrix (bathroom electrical/structural/
  ventilation only), RD-2 cost bands, RD-3 material bands, RD-4 lighting targets. A kitchen/whole-home adds
  gas ranges, 240V appliance circuits, makeup air, larger spans — NONE in the current matrix.
- THE RULE: never widen a skill `description` (e.g. "bathroom" → "renovation") AHEAD of its reference data.
  A classifier matched to a broader domain but running against bathroom-only rules would be confidently
  uncovered — a safety risk, not just a coverage gap. Extend by ADDING room-scoped reference skills
  (kitchen-irc-safety, kitchen-pricing, …) with their own curated+frozen matrices, and broaden descriptions
  ONLY in lockstep with the data.

## AM-13. Two-sets-in-sync rule (standing principle)
Reno Compass is maintained as TWO synchronized sets: (a) the source `.md` artifacts (system-instructions,
dossier-schema, stage-contracts, question-bank, orchestration, test-scenarios, data-model, change-log, this
map, RD-1..5) and (b) the authored Antigravity tree (`.agents/` + `.specify/`). ANY agreed change lands in
BOTH, wherever relevant, in the same pass — never one without the other. The source set is the authoritative
spec; the Antigravity set is its ingestion projection. A drift audit (source ↔ tree) runs after any
cross-cutting change. Rationale: the two sets are the same product in two representations; divergence silently
breaks either the spec's authority or the tree's fidelity.

## AM-14. Cross-cutting concerns (CC) — added
Implementation cross-cutting concerns authored as source artifact `reno-compass-cross-cutting.md` (CC-1..8) +
projected P1 subset into an always-active rule `.agents/rules/cross-cutting-concerns.md`. These are
implementation instructions (logging, safety-audit-trail, error taxonomy, tool-failure/retry, rate-limit,
checkpoint atomicity, config, time) — NOT agent behavior, and NOT part of the 8-stage pipeline. Rules count
now 6. The safety-decision audit trail (CC-1) is first-class (immutable, liability-adjacent). Both-sets sync
(AM-13) maintained.
