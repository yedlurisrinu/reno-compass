---
description: Scope stage: elicit and structure the renovation goal, property context, priorities, sensitive considerations, and budget horizon.
---

# Workflow — Stage 1: scope

Stage-specific SI notes: SI-15 pricing, SI-17 budget thread. Full behavior: constitution + rules. Orchestration: pipeline workflow.

## Stage contract

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


## Elicitation / topics

## STAGE 1 — SCOPE   (anchor stage; establishes format + SI-7 trigger mechanism)

Assume known coming in: nothing (entry stage).
Writes: `scope.*`. Sensitive block → SI-6 tone. Ballpark reality-check → SI-17. Triggers → SI-7.

---

### T1. Project title + type + underlying goal
**Intent:** a personal title (artifact identity), the project category (drives references), and the real WHY
behind the work — not just the what.
**Seed:**
- "Before we get into details — what would you like to call this project? Something that'll feel like yours on the final plan."
- "Tell me about the space and what you're hoping to do with it."
- "What's really prompting this — is something not working about the space, is it more about how it feels / fits your life, or are you getting it ready to put the house up for sale?"
**Follow-ups:** distinguish problem-driven ("the layout doesn't work") from aspiration-driven ("we've always wanted...");
surface the emotional stakes (family growth, aging in place, resale, long-postponed dream).
**Good-answer cue:** you can state the goal in the family's own terms AND why it matters to them.
**Notes:** this is the empathetic opening — listen for the story, not just the spec.

### T2. Property context
**Intent:** home age, dwelling type, occupancy, occupant count, rental tenants, ZIPCODE (regional pricing), and the three measurement scopes.
**Seed:**
- "Roughly how old is the home? Even a decade is helpful."
- "What's the zip code there? Renovation costs swing a lot by region — labor and materials in one metro can run very
  different from another — so I use it to pull estimates that actually match your area rather than a national average.
  Just the zip, nothing more precise."
- "Is this a house, condo, townhouse, or apartment?"
- "Who lives here — how many people, and is anyone renting?"
- "What's the size of the area you're renovating? And the home overall, if you know it?"
**Follow-ups:** if condo/townhouse → note HOA/shared-wall/access implications may come up later (SI-22); if rental
tenants → note there may be legal notice obligations; if lot size relevant → ask (feeds storage/displacement, SI-22).
**Good-answer cue:** home_age, zipcode, dwelling_type, occupancy, occupant_count, has_rental_tenants, renovation_area set
(dwelling_area / lot_area where known).
**Notes:** zipcode is operationally required (regional factor, SI-15) — a coarse region, not an exact address, so
NOT [SENSITIVE]. Ask EXPRESSIVELY (explain the why + "just the zip, nothing more precise"): turns a data-ask into a
trust moment — a demo aspect. dwelling_type and home_age are high-value — they drive cost, hazards (SI-2), and displacement options.

### T3. Who uses the space (occupant ages)  [SENSITIVE — optional — powers SI-7 triggers]
**Intent:** youngest and eldest occupant ages — because they drive safety/accessibility questions downstream.
**Seed (signpost optional at ask-time):**
- "Who'll be using this space day to day — and are there young children or older adults in the home?"
- "If you're comfortable sharing — this one's optional — roughly the youngest and oldest ages in the household?"
**Good-answer cue:** occupant_age_range.youngest/.eldest set to an age OR to `"skipped"` if declined. Gate is
satisfied either way; `null` (not-yet-asked) is NOT satisfied.
**Notes:** frame around *serving the people who use it*, not data collection. If declined → set `"skipped"`, move
on, NEVER re-ask (SI-6). A `"skipped"` age means the SI-7 age triggers simply don't fire (unknown, not "no").

### T4. Special considerations  [SENSITIVE — optional — SI-6]
**Intent:** accessibility needs, health sensitivities, allergies, pets.
**Seed (signpost optional at ask-time):**
- "A few optional questions — share only what you're comfortable with. Does anyone have mobility, health, or accessibility needs I should design around?"
- "Any sensitivities or allergies — dust, materials, fumes — that should shape what we choose or how work happens?"
  (allergies portion: if declined, don't leave it open — see the confirmation carve-out in Notes.)
- "Any pets we should plan around during the work?"
**Follow-ups:** accessibility → what specifically (grab bars, curbless, wider clearance, seated vanity);
health → respiratory/VOC/mold sensitivity affects materials + how disruptive work can be.
**Good-answer cue:** accessibility_needs / health_sensitivities / pets are each a list OR `"skipped"` (both
satisfy). ALLERGIES is special — a list OR a confirmed empty `[]`; it has no `"skipped"` resting state. `null`
(not-yet-asked / unconfirmed) satisfies none of them.
**Notes (SI-6):** ask respectfully, once, without pressing; set `"skipped"` on decline for accessibility/health/
pets and NEVER re-ask. Do NOT infer conditions not stated. ALLERGIES CARVE-OUT (safety-critical): a skip is NOT
allowed to rest — since anything recommended gets installed, a false all-clear can physically harm. On decline,
ask ONE confirmation ("proceed as though no known allergies?"); on yes, record confirmed empty `[]` (family
vouched → screens legitimately as clear). Asked once, resolved, never looped.

### T5. Preferences — global + area-specific
**Intent:** project-wide style/posture (global_preferences) AND location-precise wants (area_preferences).
**Seed:**
- "Overall, what's the feeling you want — spa-calm, bright and modern, warm and traditional?"
- "Any specific wants for particular spots? Like the shower, the vanity, storage — walk-in vs tub, double sink, a niche?"
**Follow-ups:** for each area want, tag must-have vs nice-to-have.
**Good-answer cue:** global_preferences populated; area_preferences captured per relevant location with priority.

### T6. Must-haves vs nice-to-haves
**Intent:** separate non-negotiables from wishes — the backbone of design fidelity + scope-creep guarding.
**Seed:**
- "If we had to draw a line — what absolutely must happen for this to feel worth it?"
- "And what's on the wish list — lovely if it fits, but you could let go of?"
**Good-answer cue:** must_haves and nice_to_haves clearly separated.
**Notes:** this list is what Design is held faithful to (SI-19) and what the economy option trims from.

### T7. Budget — target + ceiling
**Intent:** the hoping-for number AND the do-not-exceed number.
**Seed:**
- "What budget are you hoping to land around?"
- "And is there a hard ceiling — a number you really don't want to cross?"
**Follow-ups:** if only one number given, gently ask for the other; note phasing is an option if ceiling is tight.
**Good-answer cue:** budget_target and budget_ceiling both set.
**Notes:** feeds the ballpark reality-check (T10). Don't editorialize on the number yet — that's T10's job.

### T8. Intended timing
**Intent:** target window / season, and flexibility.
**Seed:**
- "When are you hoping to start, and is there a deadline driving it — an event, a season, a life change?"
- "How flexible is that timing?"
**Follow-ups:** note seasonal/weather implications for later (Logistics reasons on this; no stored forecast).
**Good-answer cue:** intended_timing.target_window (+ duration_flexibility if given).

### T9. Hidden-condition surfacing  [agent-initiated; raised-and-discussed]
**Intent:** proactively raise likely behind-the-wall risks given home age, so the family plans contingency.
**Seed (agent raises, weighted by home_age per SI-2):**
- "Given the home's around [age], there are a few things that tend to surprise people once walls open — things like
  [dated wiring / no waterproofing behind tile / hidden water damage / older pipes]. Worth keeping a contingency in mind."
**Follow-ups:** discuss which are plausible here; note them as hidden_conditions with a cost-impact note.
**Good-answer cue:** hidden_conditions raised AND acknowledged by the family (discussion, not a yes/no answer);
a home-age-weighted `contingency` band is computed for the ballpark (T10), regionally-scaled (10% × regional factor, clamped 20%; RD2-E) and shown as its own line.
**Notes (SI-2):** weight by home_age — don't imply false precision; frame as foresight, not alarm. The contingency
feeds T10's ballpark but is presented SEPARATELY (never folded in). When home-age risk would exceed the scaled cap, the dollar
band caps but you STILL name the conditions qualitatively — the cap is a floor-of-awareness, not a guarantee.

### T10. Ballpark reality-check + recalibration loop  [SI-17]
**Intent:** ground expectations early; block the "toy case." Ensure budget_reality_resolved before the gate.
**Seed (after ballpark computed — present base + contingency as TWO lines):**
- Plausible: "Good news — the work itself lands around [base range], plus I'd set aside up to [contingency, regionally-scaled]
  for a home this age. Even with that, you're in a realistic range."
- Tight: "This is do-able, but it'll be tight — the work runs about [base range], and for a home this age I'd hold
  up to [contingency] aside. We may need to make some choices. Worth knowing now."
- Unrealistic: "I want to be honest and helpful here: what you're hoping to do typically runs quite a bit more than the
  budget you mentioned. Would you like to look at trimming the scope, or revisit the budget, so we're building toward
  something real?"
**Recalibration loop (unrealistic only):** keep looping — adjust scope or budget — until EITHER it's no longer
unrealistic OR the family explicitly says "I understand, let's proceed anyway." Set budget_reality_resolved accordingly.
**Good-answer cue:** budget_reality_resolved == true (realistic, or knowingly accepted).
**Notes:** kind and honest, never a hard wall or a lecture. This is the "informed, not hopeful or anxious" moment.

---

### SI-7 CONDITIONAL TRIGGERS active in Scope
(fire based on answers above; weave into the conversation, don't batch at the end)
- eldest occupant elderly (T3) + bathroom/flooring in scope → raise slip-resistant flooring, grab-bar backing, curbless entry.
- youngest occupant a child (T3) → raise scald/anti-scald valves, outlet height/placement, sharp edges.
- heavy fixture implied (freestanding tub, stone counter) → flag load-bearing consideration (classified later in Safety).
- wet-area work → raise slope-to-drain + waterproofing expectations.
- any relocation of fixtures → note plumb/level/alignment matter at the new position.
- condo/townhouse (T2) → note HOA approval + work-hour/access constraints may apply (SI-22).

---

### GATE (Scope)
Coverage predicate is topic-dependent (not a flat "covered"):
- **Non-sensitive (T1, T2, T5, T6, T7, T8):** satisfied ONLY when ANSWERED to the good-answer cue. No skip —
  the agent cannot guide a project it doesn't understand (no-shortcuts spine).
- **Sensitive/optional (T3, T4):** satisfied when ANSWERED **or** `"skipped"`. `null` (not-yet-asked) is NOT
  satisfied — the agent must still raise it once. A skipped field never blocks and is never re-asked (SI-6).
- **Agent-obligation (T9, T10):** not family-answerable, so not "declinable" — T9 raised-and-discussed;
  T10 `budget_reality_resolved==true`.
Gate opens when all of the above hold + `user_final_verdict`.
**On restore (RC):** if unchanged, gate re-confirms in passing (topics skipped); if changed, reopen + cascade downstream.

---

