---
description: Design stage: measure, generate preferred+economy options faithful to scope, per-room lighting/materials, refined estimates.
---

# Workflow — Stage 2: design

Stage-specific SI notes: SI-18 per-room lighting, SI-19 scope-faithful, SI-34 passes. Full behavior: constitution + rules. Orchestration: pipeline workflow.

## Stage contract

## STAGE 2 — DESIGN

**Purpose:** Turn confirmed scope into precise measurements + flexible labeled design options (incl. an
economy option when the lead is ambitious), each with layout, intended material types, lighting
requirements, block-diagram schematic, value prop, and a refined cost estimate; land on one confirmed choice.

**Preconditions:** `scope.status == completed`. `current_stage == "design"`.

**Required-coverage:**
1. Capture precise measurements — room(s) L/W/H, existing elements + placement, sub-spaces
2. Confirm/capture intended elements (added or moved)
3. Present the `preferred` option + ALWAYS an `economy` option (not only when ambitious — CL-17). BOTH cover the
   SAME scope — the measured existing bathroom plus ONLY the changes the family explicitly requested — and differ
   solely by finish TIER and cost, never by adding or dropping features
4. Per option: intended material TYPES, lighting requirements, and a value proposition stated in the family's OWN
   goals. Elements the family is keeping are RETAINED and labeled "unchanged," not silently redesigned
5. Per option: refined estimate (ballpark + professional + permit + logistics) incl. `gap_amount` if over
   ceiling. If the family wants changes → up to 2 USER-DIRECTED passes (`design_3`/`design_4`, family-steered),
   4-pass HARD CAP total (preferred + economy + 2). Full model: SI-34.
6. Generate labeled block-diagram schematic per option (not-to-scale; SVG = roadmap)
7. Scope-fidelity guard — an option may contain ONLY the measured existing bathroom + the family's explicitly
   requested changes. Any element they did not ask for is FORBIDDEN, not merely flagged. If code/safety compels an
   addition, raise it as a question and get consent BEFORE including it
8. User selects one option (`chosen_design`)

**Reads:** `scope.*` (must/nice-haves, global + area preferences, special_considerations incl. accessibility,
hand_orientation, sub_spaces, budget_target/ceiling). Frozen refs: per-sqft ballparks + labor (RD-2); IES lighting (RD-4).
**Writes:** `design` object — `rooms`, `options[]` (layout with PER-ROOM lighting_requirements + intended_materials,
refined_estimate, budget_engineered, schematic_ref), `chosen_design`.
**Tools/Skills:** measurement math; lighting calc (IES table); design-option-generation skill (consumes ALL
scope constraints incl. accessibility; options = existing room + requested changes ONLY, no unasked additions);
refined-estimate cost tool; block-diagram generator.
**Gate:** measurements captured; options presented; each complete; one selected; `user_final_verdict`.
**Postconditions:** `design.status = completed`; `chosen_design` valid; measurements preserved (raw + derived).
**Failure/Refusal:** implausible measurements flagged, not silently computed. Structural/electrical implications
NOTED for Stage 3, not resolved here. Accessibility is a required design constraint (not a separate skill);
its code/permit implications defer to Stage 3.
**SI refs:** SI-3, SI-6 (accessibility SHAPES design), SI-18 (lighting), SI-19 (scope-faithful), SI-17 (budget).

---


## Elicitation / topics

## STAGE 2 — DESIGN   (measure → compute → present → confirm; lighter elicitation than Scope)

Assume known coming in (do-not-re-ask, SI-5): everything in `scope.*` — goal, property_context (incl. zipcode,
dwelling_type, home_age, occupant ages), special_considerations, global + area preferences, must/nice-haves,
budget target/ceiling, timing, hidden_conditions, ballpark. Design MEASURES and PROPOSES; it never re-elicits
scope facts.
Writes: `design.rooms` (measured), `design.options[]`, `design.chosen_design`. Refs: RD-2 (estimate), RD-4
(lighting), RD-1 (material-type fidelity feeds Stage-3 matrix). Two question kinds here — ELICITATION (D1–D3)
and CONFIRMATION (D4–D6).

---

### D1. Precise measurements  [elicitation; the core Design input]
**Intent:** room L/W/H, existing elements + placement, sub-spaces — the raw geometry all compute depends on.
**Seed:**
- "Let's get exact. What are the room's dimensions — length, width, and ceiling height, in feet and inches? Measured, not estimated, if you can (e.g. 8 ft 6 inches)."
- "Walk me through what's in there now and roughly where — vanity, toilet, tub/shower, window, door, any built-ins."
- "Any nooks or built-ins — linen closet, alcove, a knee-wall — worth capturing?"
**Follow-ups:** confirm finished-vs-framing basis (RD1-C4 — clearances are measured to finished surface); flag
implausible dims rather than compute silently (SI-3). Each RoomElement needs its own dimensions (non-null, CL-25).
**Good-answer cue:** `rooms[].dimensions` (L/W/H, with `unit` explicitly captured — never assumed) + each
existing `elements[]` with dimensions + placement + `sub_spaces[]` captured. derived_area/volume computed.
**Notes:** this is the one heavy-elicitation topic in Design. Precision here is what makes every downstream
number real; a guessed dimension poisons the estimate and the clearance check. State units in the ask and record
the `unit` on every Dimensions object — mixed/assumed units are a silent-error source (per CL-64: spell out inches).

### D2. Intended changes — elements added / moved  [elicitation]
**Intent:** which elements are new, relocated, or removed vs the measured current state — the delta Design works on.
**Seed:**
- "Of what's there now — what's staying, what's going, and what's moving? (Moving a fixture is a bigger deal than swapping one in place — worth being precise.)"
- "Anything new you want that isn't there today — a second sink, a niche, a linen tower?"
**Follow-ups:** any RELOCATION → mark the new element `existing_or_new = new` and note plumb/level/alignment
matters (SI-7); relocation implies plumbing/electrical moves → NOTED for Stage 3, not resolved here.
**Good-answer cue:** new/moved elements captured as `elements[]` with `existing_or_new` set; relocations flagged.
**Notes:** keeping fixtures in place is the biggest cost lever (RD3-F1) — surface that tradeoff honestly so the
family chooses knowingly, don't steer.

### D3. Per-room material-type + lighting intent  [elicitation — CL-48 fidelity probe lives here]
**Intent:** intended material TYPE per surface AND the fidelity Safety's frozen Tier-1 matrix needs (RD-1);
plus natural-light context for the IES lighting compute (RD-4).
**Seed (material):**
- "For each main surface — floor, shower walls, counter — what material are you picturing?"
- "When it's stone or a heavy fixture, I need a bit more detail so we flag any structural or electrical checks early:
  for a counter or slab, is it natural stone or engineered/quartz, and roughly what thickness? For a standout tub,
  which material — acrylic, cast iron, stone/concrete? For anything with a motor or heat (heated floor, steam, big
  soaking tub), any sense of its power draw?"
**Seed (lighting context):**
- "How's the natural light — which way does the room face, any window, and anything blocking it (tree, overhang, a wall)?"
**Follow-ups (material fidelity → RD-1 matrix):** natural stone / thick slab / cast-iron or stone tub → capture
weight class so Stage-3 can run the two-gate structural check (RD1-F); high-draw appliance → capture amperage
sense so Stage-3 can run the electrical envelope (RD1-A). Design CAPTURES; Safety CLASSIFIES (SI-30) — do not
tier here.
**Good-answer cue:** per-room `intended_materials[]` with `material_type` AND fidelity fields (composition /
weight_class / amperage_note where the item is heavy or high-draw); `lighting_requirements` natural-light inputs
captured. Artificial-lumen/fixture-count are [computed] by the IES tool (RD-4), not asked.
**Notes:** this is the CL-48-critical topic. Fidelity is only pressed for heavy/high-draw items (stone, big tubs,
motors/heat) — NOT every surface; over-asking porcelain-tile weight is noise. Frame as "so we catch a structural
or electrical check early," not spec-collection. Schema: `intended_materials` extended to carry the fidelity
fields (see change log).

---

### D4. Option presentation + value proposition  [confirmation; agent presents, family reacts]
**Intent:** present the `preferred` + `economy` option (always both, SI-19/CL-17) tied to must-haves + area
preferences, each with layout, per-room lighting, intended materials, block-diagram schematic, value prop, and
a refined estimate (RD-2). Further user-directed passes (design_3/4) come at D5 under the 4-cap (SI-34).
**Seed (agent presents, then invites reaction):**
- "Here's what I'd propose. Option A [preferred] — [value prop tied to their must-haves]. Option B [economy] —
  [what it trims and why it still hits the core goal]. Here's a rough layout diagram for each and an estimate range."
- "Which direction pulls you — and what would you change?"
**Follow-ups:** capture reactions as area-preference refinements; if a must-have is unmet, revise before proceeding
(SI-19 scope-faithful). Do NOT pad the option with elements the family didn't ask for — the option is their
existing room + their requested changes ONLY; a code/safety-compelled addition is raised as a question first, never
folded in unasked. Economy option is ALWAYS offered, not only when the lead is ambitious (CL-17).
**Good-answer cue:** `options[]` each with label/option_role, value_proposition, layout (per-room lighting +
materials), schematic_ref, refined_estimate; family has reacted and directed.
**Notes:** this is presentation, not interrogation. The estimate is a RANGE + verify-locally (RD-2/SI-15); don't
false-precise. Timelines given as industry-average + best-case (RD2-F) if asked.

### D5. Over-ceiling handling — economy + user-directed passes  [confirmation; conditional; SI-34]
**Intent:** if the preferred estimate exceeds `budget_ceiling`, the economy option (always present, D4) is the
first fallback; if the family wants to keep iterating, they steer up to 2 more USER-DIRECTED passes
(`design_3`/`design_4`) — 4-pass HARD CAP total.
**Seed:**
- "Option A is above your ceiling. The economy version (Option B) comes in around [range] — want to go with that, or shall we rework it?"
- "Tell me what to change — 'keep the double vanity but drop the heated floor,' say — and I'll rework it. We can do this up to two more times."
**Follow-ups:** each pass is FAMILY-STEERED (not system-guessed); pass the actual `gap_amount` to the rework so
it engineers TO the target (SI-34). Each new option gets full downstream analysis when produced. At the 4th
option, cap reached — the family chooses among what exists (may still be the original preferred).
**Good-answer cue:** where over ceiling → economy offered first; if iterated, `design_3`/`design_4` created
(user-directed, `budget_engineered` reflects budget motivation), each with estimate + `gap_amount` + what-it-trims;
4-pass cap respected.
**Notes:** framing is "gap to bridge," never "not feasible" (SI-17/SI-27/SI-34). Full pass/retention model: SI-34.

### D6. Selection + scope-creep confirmation  [confirmation; the gate]
**Intent:** family selects one option → immutable `chosen_design`; agent confirms no drift beyond stated scope.
**Seed:**
- "Ready to lock one in? Once you choose, I'll freeze it as the plan we carry into safety and materials."
- "Quick check — everything in this option maps to something you asked for; nothing crept in that you didn't want?"
**Follow-ups:** scope-fidelity guard — before freezing, verify every element in the option is either the existing
room or a change the family explicitly requested; anything they did not ask for must be removed (or, if
code/safety-compelled, consented to) — not merely flagged (SI-19). On selection copy the full option into
`chosen_design` (immutable, CL-3).
**Good-answer cue:** one option selected → `chosen_design` set (immutable copy); scope-creep guard passed;
`user_final_verdict`.
**Notes:** selection is the highest-stakes confirmation before the safety spine; make the freeze explicit so the
family knows a later change reopens downstream (cascade).

---

### GATE (Design)
- **Elicitation (D1–D3):** measurements captured (D1, plausible); intended changes captured (D2); per-room
  material-type + lighting intent captured (D3, incl. fidelity fields for heavy/high-draw items).
- **Confirmation (D4–D6):** ≥1 option presented incl. economy (D4); if lead over ceiling, budget-engineered
  alts offered (D5); one option selected → `chosen_design` immutable, scope-creep guard passed (D6).
Gate opens when all hold + `user_final_verdict`. (No skip states here — Design facts are required, unlike Scope's
optional-sensitive topics; a family that won't give measurements can't be given a real design.)
**On restore (RC):** unchanged → re-confirm + skip topics; changed → reopen + cascade downstream.

---

