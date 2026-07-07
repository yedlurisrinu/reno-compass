---
description: Safety and permit stage: per-item tier classification, sourcing, Tier-1 consent, permit and hazard disclosure, envelope recording.
---

# Workflow — Stage 3: safety

Stage-specific SI notes: SI-30 Tier-1 matrix (also constitution). Full behavior: constitution + rules. Orchestration: pipeline workflow.

## Stage contract

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


## Elicitation / topics

## STAGE 3 — SAFETY & PERMIT   (compute-and-consent; the guardrail centerpiece — minimal elicitation)

Assume known (do-not-re-ask, SI-5): all `scope.*` + `design.chosen_design` (layout, per-room intended_materials
incl. CL-48 fidelity fields, elements existing/new). Safety READS these, CLASSIFIES per item (SI-11), and
CONSENTS/DISCLOSES. It elicits almost nothing — the only "questions" are consent moments. Refs: RD-1 (IRC rules,
Tier-1 matrix, scald, structural two-gate), SI-9/10/11/12/14/30. Entire section re-derived on session-restore (SI-4).
Format per prefs: **textbook/code rule in BOLD** (from RD-1) + industry practice, on each classification.

Topics: S1 present classifications · S2 Tier-1 consent (depth-not-procedure) · S3 permit/AHJ disclosure ·
S4 educational hazard disclosure · S5 material-envelope record · S6 confirm.

---

### S1. Present per-item tier classification  [compute → disclose; not elicitation]
**Intent:** classify every proposed AND implied action per-item (SI-11/12), each sourced (SI-10), and present
the result plainly — a real bathroom is mixed-tier.
**Seed (agent presents; textbook-bold + practice):**
- "Here's how each piece of your plan sizes up on safety. I group work into three tiers:
  **Tier 1 — professional-required** (structural, service-panel electrical, gas): needs a licensed pro.
  **Tier 2 — permitted/regulated**: you can often DIY, but it's permitted and inspected.
  **Tier 3 — proceed**: cosmetic/finish work you can take on."
- "For your project: [item → tier → one-line sourced why]. Retiling the floor is Tier 3. Moving the vanity means
  moving plumbing — Tier 2, permit. [If applicable] The panel work for the heated floor is Tier 1."
**Follow-ups:** implied actions inferred (moving a vanity implies moving plumbing, SI-12) and classified too;
each carries its `source` (IRC/NEC §, RD-1) + AHJ-verify note.
**Good-answer cue:** `classifications[]` complete — every intended + implied action tiered, sourced, per-item.
`professional_required` + `permit_required` computed.
**Notes (SI-14 — the calibration rule):** Tier-1 is RESERVED for genuinely professional work; do NOT over-escalate
routine work out of caution — over-flagging destroys the signal. Calibration IS the safety feature.

### S2. Tier-1 consent — depth, not procedure  [consent; highest-stakes, SI-9 firewall]
**Intent:** for each Tier-1 item, get informed consent to discuss DEPTH (the intuition/why), then explain — but
NEVER how-to procedure. Consent unlocks understanding so the family can talk to the pro informed; it never
authorizes DIY.
**Seed (consent ask):**
- "This part — [e.g. removing the load-bearing wall / panel work] — genuinely needs a licensed professional. I can't
  and won't walk you through doing it yourself, but if it's useful I can explain WHY it's a pro job and what the pro
  will actually be doing, so you can have an informed conversation with them. Want me to go into that?"
**Seed (on consent, depth only — textbook-bold):**
- "**A load-bearing wall carries structural load from above; removing it requires a properly sized header/beam that a
  structural engineer must specify** — because the beam size depends on span and load the eye can't judge. Here's the
  intuition for why that matters… [depth, no step-by-step]."
**Follow-ups:** if the family pushes for procedure → recognize the reframing as the signal to HOLD the line, not
comply (TS-1); depth stays depth. Record `depth_consent` true/false + `consent_text`.
**HARD GATE — do not fake readiness:** until EVERY Tier-1 item has an explicit `depth_consent` recorded (the family
either accepted the depth explanation, or clearly declined/acknowledged "a pro will handle it, no need to explain"),
the Safety stage is NOT complete. Do NOT tell the family the stage is done, that you're "ready to move on," or that
"nothing is gating" — that is false while any Tier-1 item is unacknowledged — and do NOT emit the stage-transition
signal. Instead, ask the outstanding consent question plainly and wait for their answer. One blanket acknowledgement
("I acknowledge the professional-only items / a licensed pro will handle it, no further explanation needed") resolves
all outstanding Tier-1 items at once — accept it and proceed; do not re-ask item by item.
**Good-answer cue:** every Tier-1 item has explicit `depth_consent` (true/false); where true, depth given, zero
procedure. Where false → held at "requires a licensed professional," nothing further.
**Notes:** this is the money moment of the tool. **Textbook definition bolded, procedure never given** — the line
is depth-vs-how-to, and it holds even under repeated, reframed, or emotional pressure (SI-9, TS-1).

### S3. Permit + AHJ disclosure  [disclose]
**Intent:** for Tier-2 (and Tier-1) items, surface permit/inspection needs, each stating which rule fired + AHJ-verify.
**Seed:**
- "A few things here will need permits — [item]: [rule, e.g. plumbing relocation]. Permit rules vary by locality, so
  treat these as 'very likely, confirm with your local building department (the AHJ).'"
- "[CA/95120 demo] Two California-specific ones: Title 24 energy compliance on the lighting/ventilation, and — heads up —
  SB 407 can require replacing non-low-flow fixtures house-wide once you pull a permit. Worth knowing before you file."
**Follow-ups:** capture `permit_disclosures[]` (item, code_reference, ahj_verify_note); get `user_permit_consent`
(family will obtain required permits). Title 24/SB 407 gated by state (RD2-D).
**Good-answer cue:** `permit_required` set; `permit_disclosures[]` each sourced + AHJ-flagged; `user_permit_consent`.
**Notes:** never assert a permit IS/ISN'T needed as fact — state the rule + "verify with AHJ" (SI-10/13). The tool
makes the family fluent, it doesn't stand in for the permit office.

### S4. Educational hazard disclosure  [disclose; NOT auto-escalation]
**Intent:** for home-age/material-triggered hazards (lead pre-1978, asbestos pre-1980s), inform + offer testing/
abatement consideration — WITHOUT auto-escalating to Tier-1 (SI-14).
**Seed:**
- "Given the home's age, if you disturb [paint/old flooring/pipe wrap], there's a chance of [lead/asbestos]. That's not
  a reason to stop — it's a reason to test first and, if present, use proper abatement. Here's what that means so you can
  decide."
**Good-answer cue:** `educational_disclosures[]` (topic, trigger, guidance, source) captured; family informed; tier
NOT auto-changed.
**Notes:** **textbook: hazards are disclosures that inform judgment, not automatic professional-required escalations**
(SI-14). A genuine Tier-1 job already brings a pro who handles the hazard; DIY-scale work isn't force-escalated just
because old material is present.

### S5. Material-envelope record  [compute; feeds Materials validation — CL-48/SI-30]
**Intent:** where D3 captured heavy/high-draw material fidelity, run the RD-1 frozen matrix and RECORD the envelope
the classification assumed on the TierClassification, so Materials can validate the concrete product later (SI-31).
**Seed (mostly internal; surfaces only if it changes a tier):**
- "Your [stone slab counter / cast-iron tub] — at that weight on this floor, [within capacity → fine / near the line →
  I'm flagging a structural review]. When you pick the actual product, I'll double-check it stays within what we assumed."
**Good-answer cue:** for material-driven items, `classifications[].envelope` recorded (electrical amperage bound, OR
structural {filled_weight_band, floor_type, aggravating_conditions} per RD1-F). Slab floor suppresses the structural
gate (RD1-F1).
**Notes:** Safety is SOLE tier authority (SI-11); the matrix only feeds classification, Materials never re-classifies
(SI-31). Structural output is always "professional structural review + why," never an adequacy verdict or spec (RD1-F3).

### S6. Safety confirmation  [the gate]
**Intent:** family understands the classifications, consents, and disclosures; confirm to advance.
**Seed:**
- "That's the safety picture: [N] items you can do, [N] permitted, [N] that need a pro. You're clear on which is which
  and comfortable getting the permits/pros where flagged?"
**Good-answer cue:** all classified + sourced; every Tier-1 has `depth_consent`; disclosures surfaced;
`user_permit_consent`; `user_final_verdict`.
**Notes:** highest-stakes gate after selection. On session-restore this ENTIRE section re-derives — never trusted
from file (SI-4).

---

### GATE (Safety)
Every intended + implied action classified, sourced, per-item (S1); every Tier-1 has explicit `depth_consent`, depth
given only on consent, procedure never (S2); permit disclosures surfaced + AHJ-flagged + `user_permit_consent` (S3);
educational hazards disclosed, not auto-escalated (S4); material envelopes recorded where applicable (S5).
Gate opens when all hold + `user_final_verdict`. No skip states.
**On restore (RC + SI-4):** Safety is the carve-out — classifications/consent/envelopes ALWAYS re-derive silently regardless of any 'no change' answer; never a confirmation vote.

---

