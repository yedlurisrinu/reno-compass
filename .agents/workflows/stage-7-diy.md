---
description: DIY planning stage (conditional): one eligible item at a time — tools + procedure, questions, then an atomic can-do / hand-to-pro decision. Tier-1 firewalled.
---

# Workflow — Stage 7: diy

Stage-specific SI notes: SI-26 DIY. Full behavior: constitution + rules. Orchestration: pipeline workflow.

## Stage contract

## STAGE 6.5 — DIY PLANNING   [CONDITIONAL — runs only if DIY-eligible work exists AND the family chose to self-perform]

**Purpose:** Walk the family through the work they *could* do themselves — **all non-Tier-1 items
(Tier-3 proceed + Tier-2 permitted)** — **one item at a time**. For each item present the required
tools and the step-level procedure, answer any questions, then let the family make an **atomic**
decision on that single item: do it themselves, or hand it to a professional. Feed the confirmed DIY
plan into Synthesis. NEVER produce procedure for Tier-1 (professional-only) work.

**Preconditions:** `contractor_validation.status == completed` AND the DERIVED predicate holds — the
non-Tier-1 set over `safety_permit.classifications` (every Tier-2 and Tier-3 item) is non-empty AND the
family did NOT choose contractors-for-everything at the Contractor stage (`contractor_validation.wants_diy`
is not False). Computed at entry so it can't go stale (CL-78) — not a stored `applicable` flag. If empty,
or if `wants_diy is False`, the stage is SKIPPED and control passes to Synthesis. `current_stage == "diy_planning"`.

**DIY eligibility (IMPORTANT — changed):** eligibility is the WHOLE non-Tier-1 set. A Tier-2 item is
DIY-able *with a permit* — it is eligible on its own; there is no separate prior "self-perform consent"
gate. Whether the family actually self-performs it is the per-item decision made HERE, in the loop.

**One item per loop:** the app pins ONE eligible item as the active item and hands it to you. Produce
tools + procedure for THAT item only. Do NOT list, preview, or ask about any other eligible item — they
are handled in later turns. When the active item is decided, the app advances to the next one and hands
it to you. This keeps the family focused and avoids confusion as progress accumulates.

**Atomic per item:** the decision is for the WHOLE item (the Safety bundle) — all of it or none of it.
No partial hand-off inside one item (e.g. "I'll demo but you tile the same item"). Bundle granularity is
fixed by the tiered Safety evaluation and is never split here.

**Required-coverage (per active item):**
1. See the FULL classified set for correct sequencing; write procedure ONLY for the active non-Tier-1 item.
   Weave Tier-1 items in as `hold_points` ("wait for the licensed [trade] here") — NO how-to for them, ever.
2. For a Tier-2 active item, the procedure MUST include the permit/inspection hold-points and be explicit
   that a permit is required.
3. Provide the tools/equipment for the active item (with rent-or-buy note).
4. Answer the family's questions / refine the active item's procedure to their experience.
5. The family decides the active item: **can do it** → self-perform; **can't / prefer a pro** → recorded as
   their choice and reclassified to professional scope (surfaced in Synthesis as an addition to the
   contractor's scope). Either way, NO Safety tier change and NO cascade — tier reflects code necessity,
   only WHO does the work changed (SI-26).

**Reads:** `safety_permit.classifications` (FULL set — non-Tier-1 = procedure targets, Tier-1 = sequence anchors),
`contractor_validation.wants_diy`, `design.chosen_design`, `materials.line_items`.
**Writes:** `diy_planning` — `procedures[]` (per eligible item: `steps`, `hold_points`, `timeline`, `tools[]`,
and the per-item `user_feasible` / `reclassify_to_professional` decision), `active_item` (app-managed).
**Tools/Skills:** DIY-procedure skill (non-Tier-1 only; Tier-1 firewalled); tools/equipment skill.
**Gate:** EVERY eligible (non-Tier-1) item has a procedure whose per-item decision is recorded
(`user_feasible` is not null); at least one procedure exists; `user_final_verdict`.
**Postconditions:** `diy_planning.status = completed`; per-item DIY procedures + decisions ready for Synthesis.
**Failure/Refusal:**
- NEVER procedure for Tier-1 / professional-required work (Principle 1 firewall, absolute).
- Family opting to hire out an item → recorded as a personal choice; NOT a tier change, NOT a cascade.
- Never expose internal control tags or reference codes to the family.
**SI refs:** Principle 1 / SI-9 (Tier-1 firewall), SI-26 (DIY planning: refine not reclassify).

---


## Elicitation / topics

## STAGE 7 — DIY PLANNING   (CONDITIONAL — one eligible item at a time; refine-not-reclassify)

Runs only when the derived non-Tier-1 set is non-empty AND `wants_diy` is not False (CL-78; not a stored
flag). All-professional project, or the family chose contractors-for-everything → stage SKIPPED (TS-8).
Assume known (SI-5): `safety_permit.classifications[]`, `design.chosen_design`, `materials.*`. Refs: SI-26
(refine-not-reclassify), Principle 1 / SI-9 (Tier-1 firewall), RD-1/RD-3 (procedure grounding, tool costs).
Per prefs: industry-average + best-case timelines, tool rent-vs-buy economy.

Loop, per active item: Y1 procedure + tools for THIS item · Y2 questions / refine · Y3 atomic decision.
After the last item is decided: Y4 confirm the assembled DIY plan.

---

### Y1. Active-item procedure + tools  [present → refine; SI-26 + Principle 1 firewall]
**Intent:** for the ONE active non-Tier-1 item the app has pinned, present the tools and the step-level
procedure. Partition {Tier-1 = sequence anchors} vs {this item = procedure target}.
**Seed:** "Let's look at [swap the vanity]. Here's what you'll need and the step sequence. Tell me your
experience level and I'll tighten it."
**Tier-2 active item:** the procedure MUST carry the permit/inspection hold-points and state plainly that a
permit is required. This is what makes Tier-2 DIY-able rather than professional-only.
**Full-scope visibility, firewalled generation (Principle 1):** you SEE Tier-1 items for correct sequencing
but write NO procedure for them — they appear ONLY as `hold_points` ("wait here for your licensed electrician
to finish rough-in before you tile").
**Good-answer cue:** one `procedures[]` entry for the active item (item, tier ∈ {tier_2, tier_3}, steps,
`tools[]`, `hold_points` where sequencing/permit requires, a timeline). Do NOT emit entries for other items.

### Y2. Questions / refine  [present; SI-26; capped]
**Intent:** answer the family's questions on the active item's tools or procedure; incorporate refinements.
**Seed:** "Any questions on the tools or the steps here? Happy to adjust the sequence to how you like to work."
**Follow-ups (SI-26):** family alters a step order → INCORPORATE and tighten; this REFINES, does NOT reclassify.
**Cap:** after ~3 refine passes on the same item, gently steer toward the decision so the loop keeps moving.

### Y3. Atomic per-item decision  [the SI-26 personal-choice path]
**Intent:** the family decides THIS item — do it themselves, or hand it to a professional. Whole-item, atomic.
**Seed:** "Feeling good to take this one on yourselves, or would you rather hand it to a pro? No judgment —
some are just easier to buy out."
**Follow-ups (SI-26/TS-7):** hand-to-pro → recorded as the family's choice (`reclassify_to_professional`); the
item moves to professional scope and is surfaced in Synthesis under the contractor's scope — but this is NOT a
tier change and NOT a cascade. Then the app advances to the next eligible item (Y1 again).
**Good-answer cue:** the active procedure's `user_feasible` set true (self-perform) or false + `reclassify_to_professional` (hand off).
**Notes:** the family makes this decision via the one-tap options ("I can do this one myself" / "I have a
question / want to refine this" / "I can't — assign this to a professional"). Never surface any internal tag.

### Y4. Confirm the assembled DIY plan  [the gate]
**Intent:** once EVERY eligible item has a decision, summarise and confirm — no new item, no re-opening.
**Seed:** "Here's your DIY plan: you'll self-perform [x, y]; [z] goes to your contractor. Ready to lock it in?"
**Good-answer cue:** every eligible item decided; procedures + tools recorded; `user_final_verdict`.

---

### GATE (DIY Planning)
CONDITIONAL — skipped if the derived non-Tier-1 set is empty or `wants_diy is False` (TS-8). Else: each eligible
(non-Tier-1) item walked one at a time with procedure + tools, Tier-1 firewalled to hold-points (Y1); questions
answered/refined (Y2); each item decided atomically as self-perform or handed to a professional (Y3); at least
one procedure exists; gate opens + `user_final_verdict` (Y4).
**On restore (RC):** unchanged → re-confirm + skip topics; changed → reopen + cascade downstream (Synthesis only).

---
