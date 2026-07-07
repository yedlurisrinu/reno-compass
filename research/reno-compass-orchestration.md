# Reno Compass — Orchestration State-Machine (CL-45)

**The 7th artifact — the runnable spine.** Formalizes the pipeline as a state machine: states, transitions,
guards, cascade/retention actions. Pulls together decisions scattered across SI notes; those remain the
behavioral source of truth — this is their transition-table projection. Numbered OM-n, stable.

**References:** stage gates → `reno-compass-stage-contracts.md`; behaviors → `reno-compass-system-instructions.md`
(esp. SI-4 restore, SI-17 budget thread, SI-26 DIY, SI-31 envelope re-open, SI-34 passes/retention);
data shapes → `reno-compass-dossier-schema.md`.

---

## OM-1. States
`scope → design → safety_permit → logistics_feasibility → materials → contractor_validation →
[diy_planning — CONDITIONAL] → synthesis → complete`.
`complete` is TERMINAL (SI-34): no transition leaves it; restore does not reopen it.
Two SELF-LOOPS exist (not new states): `scope→scope` (budget recalibration, T1a) and
`logistics_feasibility→logistics_feasibility` (displacement loop, T5a) — both bounded, both exit on resolve.

## OM-2. Forward transition rule
Every forward transition requires the source stage's GATE satisfied (all required-coverage covered +
`user_final_verdict`). The orchestrator refuses to advance on incomplete info — it does not improvise forward.

## OM-3. Transition table
(Guard = precondition to fire; Action = state mutation on firing.)

| # | From | Trigger | To | Guard | Action |
|---|------|---------|----|----|--------|
| T1 | scope | gate + verdict | design | scope gate; `budget_reality_resolved==true` | advance |
| T1a | scope | budget unrealistic (SI-17) | scope | not yet resolved | RECALIBRATION self-loop: adjust scope/budget; repeat until realistic OR family knowingly accepts → sets `budget_reality_resolved=true`. No forced exit. |
| T2 | design | gate + verdict (option selected) | safety_permit | ≥ preferred+economy presented; one selected → `chosen_design`; scope-creep passed | set `active_option_role`; compute active analysis forward |
| T3 | design | user-directed iteration | design | design passes used < 4 (SI-34 cap) | create `design_3`/`design_4` (user-steered); pass `gap_amount` if budget-driven |
| T4 | safety_permit | gate + verdict | logistics_feasibility | all items classified/sourced (BOTH preferred + economy, eager OM-6); every Tier-1 has `depth_consent`; permit consent | advance |
| T4a | safety_permit | envelope re-open resolved (from T10) | materials | single item re-classified + re-consented | RETURN to materials; resume gate (OM-9) |
| T5 | logistics_feasibility | verdict = `proceed` | materials | `feasible_within_ceiling` OR family accepts | advance |
| T5a | logistics_feasibility | `total_with_displacement` > ceiling (SI-32/CL-47) | logistics_feasibility | not yet resolved | DISPLACEMENT LOOP self-edge: (1) ask separate budget → (2) inline optimize + re-test → (3) offer trims → (4) if unresolved, emit `proceed_with_budget_gap`. Never forced rollback (OM-13) |
| T6 | logistics_feasibility | verdict = `use_economy_option` | materials | economy analyzed eagerly (OM-6) | REPOINT active→economy (reactivate retained analysis — always present); safety re-verify (OM-7) |
| T7 | logistics_feasibility | verdict = `revisit_design` | design | family explicitly elects; passes < 4 | DISCARD superseded retained analyses; draw a pass (OM-6) |
| T8 | logistics_feasibility | verdict = `proceed_with_budget_gap` | synthesis | over ceiling after options, or family declines to trim | JUMP: bypass materials + contractor + diy (OM-8) |
| T9 | materials | gate + verdict | contractor_validation | all items priced/validated (allergy + envelope) | advance |
| T10 | materials | envelope breach (SI-31) | safety_permit (1 item) | product spec > stored envelope | single-item re-open; re-classify + re-consent that item; return via T4a (OM-9) |
| T11 | materials | `revisit_design` (cost final) | design | family finds real total unacceptable; passes < 4 (SI-34) | DISCARD superseded analyses; draw a pass |
| T12 | materials | cap exhausted, family unhappy | (choose-existing) or synthesis | design passes == 4 | route to choose a retained option OR `proceed_with_budget_gap` (OM-10) |
| T13 | contractor_validation | gate + verdict | diy_planning OR synthesis | see OM-5 conditional | advance to diy if DIY predicate holds, else synthesis |
| T14 | diy_planning | gate + verdict | synthesis | procedures refined; each item feasible-or-opted-out | advance |
| T15 | synthesis | gate + verdict | complete | PDF delivered; materials xlsx shipped separately | set `complete` (terminal) |
| R* | any in-progress stage | session_restore | scope (re-entry) | dossier NOT `complete` (terminal rule, OM-11) | NOT enumerated per-stage here — re-entry at scope + per-stage RC re-walk (skip-if-unchanged / reopen-if-changed; safety always re-derived). Full definition: OM-11 |

## OM-4. Backward / non-linear edges (each guarded — the ONLY departures from linear-forward)
- **E1 `revisit_design`** (T7, T11): → design; DISCARD superseded options' retained analyses (SI-34); cascade
  invalidate Safety/Logistics/Materials/DIY for the new geometry; draws one design pass. Triggerable from
  Design (iteration) and Materials (cost final) ONLY — never Safety/Logistics (they run on estimates, SI-34).
- **E2 `use_economy_option`** (T6): → REPOINT, not backward-to-design. Swap `active_option_role` to economy,
  reactivate its retained analysis (always present — economy analyzed eagerly, OM-6). No discard, no re-design (SI-34).
- **E3 Materials→Safety single-item re-open** (T10, CL-48/SI-31): one item only; re-classify + re-consent that
  item; NOT a whole-stage cascade, NOT the whole pipeline.
- **E4 `proceed_with_budget_gap`** (T8): forward jump to Synthesis, bypassing Materials+Contractor+DIY together.

## OM-5. Conditional: diy_planning (T13)
Entered ONLY if the DERIVED predicate holds — the non-Tier-1 set (Tier-3 + DIY-consented Tier-2) over
`safety_permit.classifications` is non-empty (CL-78; not a stored flag). Else control passes straight to
synthesis. On the `proceed_with_budget_gap` jump (E4), diy is bypassed regardless.

## OM-6. Design passes & retention (SI-34)
- HARD CAP 4: {preferred, economy, design_3, design_4}. design_3/4 user-directed.
- Analysis timing = EAGER for preferred + economy (SI-34): S/L/M run against BOTH as the pipeline executes
  (both exist from Design D4), so retained_analysis holds both BEFORE the Logistics verdict — this is what lets
  Logistics judge whether economy comes in under ceiling. design_3/4 (produced later, on demand) analyzed when created.
- Analysis RETAINED per option_role in `design.retained_analysis`; exactly one ACTIVE
  (`design.active_option_role`). SWITCH = repoint active (no recompute/no loss). revisit_design = discard
  superseded entries. Cap exhausted → OM-10.

## OM-7. Safety re-verify on switch
On any option switch (E2, or falling back to a retained option), safety RE-DERIVES to confirm the retained
classification still holds for the now-active option (SI-4/SI-11). Unchanged option → same result (cheap
confirm), never blind trust. Distinct from a genuine change (which invalidates-and-recomputes).

## OM-8. Budget-gap jump (E4)
`proceed_with_budget_gap` → synthesis with the FULL preferred plan; `has_budget_gap=true` → `budget_gap_bridge`
at PDF end (SI-27). Materials/Contractor/DIY bypassed → no materials xlsx on this path; `design_accepted`
reflects whether the family committed (CL-73). Never "not feasible."

## OM-9. Envelope re-open loop (E3)
Materials product spec > stored `TierClassification.envelope` → re-open Safety for THAT ITEM: re-classify
(likely Tier-1 professional-install), re-consent (SI-9), set `reclassified_from_materials`, block-track out of
DIY. Return to Materials. Bounded (one item), not a pipeline cascade.

## OM-10. Cap-exhaustion (T12)
Design passes == 4 and family still wants change → NO further pass (terminating guard). Route: choose among the
retained options (repoint to the chosen one), OR `proceed_with_budget_gap` → synthesis. Graceful framing: the
family had their 4 revisions.

## OM-11. Restore (SI-4 + RC + SI-34 terminal rule)
- TWO PATHS by trust (persistence: data-model DM-13):
  - TRUSTED server checkpoint (GCS) — crash/reconnect/reopen: resume SEAMLESSLY where left off, NO re-walk, NO
    RC loop. Safety silently re-derived on load (identical on unchanged untampered state).
  - UNTRUSTED portable import — reset to scope, re-walk with RESTORE-CONFIRMATION: per stage one confirm; no
    change → re-confirm in passing, skip topics, advance; change → reopen + cascade DOWNSTREAM (dependency-chain
    from the changed stage down).
- BOTH paths: a dossier at `complete` is TERMINAL — restore does NOT reopen it (fresh run required).
- BOTH paths, the single invariant: safety is ALWAYS re-derived, never loaded from file.

## OM-12. Termination argument (why the machine halts)
Forward edges are finite (8 stages). Backward edges are bounded: revisit_design draws from a HARD 4-pass cap
(OM-6); the envelope re-open is single-item and returns (OM-9); the Logistics/CL-47 loop exits on resolve or
`proceed_with_budget_gap`. No unbounded cycle exists → the machine always reaches `complete`.

## OM-13. Logistics displacement loop (T5a; SI-32/CL-47)
Self-edge on `logistics_feasibility` when `total_with_displacement` breaches `budget_ceiling`. Staged, mirrors
the Scope reality-check posture — optimize and offer, NEVER a forced rollback or "not feasible" wall:
1. ASK if a SEPARATE budget funds displacement → yes: resolved, no breach.
2. If no → INLINE optimization (sequencing to keep utilities active longer; temp-rental→stay-with-family;
   cheaper off-site). Re-test against ceiling.
3. If still over → OFFER specific nice-to-have / high-cost trims the family MAY choose. Offer, never auto-cut.
4. If declined/insufficient → emit verdict `proceed_with_budget_gap` (T8) → Synthesis with gap-to-bridge (SI-27).
Loop exits ONLY on resolve (steps 1–3) or the gap verdict (step 4) — bounded, no infinite cycle (OM-12).
CL-47 never mutates chosen_design; `revisit_design` fires only on explicit family choice (T7).

## OPEN / TO-EXPAND
- OM-N1. Guard predicates above are prose; the BDD/Gherkin layer (CL-40) converts these + gate conditions to a
  deterministic acceptance spine. Verify Antigravity spec-ingestion format first.
- OM-N2. Full per-trigger error/refusal rows (malformed input, gate-not-satisfied) to be tabulated in the BDD pass.
