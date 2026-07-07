---
name: safety-tier-classification
description: Classify each bathroom-remodel action into a safety tier (professional-required, permitted, or proceed) with a sourced rationale and recorded envelope. Use at the Safety stage and again in the contractor audit — the shared classification spine.
---

# Safety-Tier Classification (shared spine)

The single tier authority for the whole pipeline (constitution Principles 1–6). Used at Safety (Stage 3) AND
re-invoked in the contractor audit (Stage 6). Defining it once keeps the guardrail identical everywhere it
fires — do not duplicate this logic into other skills.

## Output per item
A `TierClassification`: `tier` ∈ {tier_1_professional, tier_2_permitted, tier_3_proceed}, a `source`
(IRC/NEC §), an AHJ-verify note, and — for material-driven items — the `envelope` the classification assumed.

## How to classify
1. PER ITEM, independently (SI-11). A real bathroom is mixed-tier. Never tier the whole scope to the highest.
2. INFER implied work (SI-12): "move the vanity" implies plumbing relocation (and maybe electrical) — classify
   the implied work too. Inference finds WHAT; the tier of that work is still SOURCED (never guessed).
3. SOURCE every call against the frozen rule base — see `references/` (the irc-safety matrix + IRC/NEC rules).
   Do not invent code from memory.
4. CALIBRATE (SI-14, the most important rule): Tier-1 only for work genuinely needing a licensed pro
   (structural, service/panel electrical, gas). Do NOT push modest work to Tier-1 out of caution.
5. MATERIAL-DRIVEN tiering (SI-30): evaluate each intended material TYPE against the frozen Tier-1 matrix.
   Structural trigger is TWO-GATE (slab suppresses; framed floor fires at ≥1,500 lb filled, or 800–1,500 lb
   with an aggravating condition). Record the ENVELOPE: electrical = amperage bound; structural = a TUPLE
   (filled-weight band × floor type × aggravating conditions), never a point-load psf number. Output is ALWAYS
   "needs professional structural review + why" — never "floor holds/doesn't," never a reinforcement spec.
   The material TYPE is READ from the design record (`design.chosen_design` intended_materials), NOT elicited
   here — Safety classifies, it does not shop. If the type needed for a check is genuinely missing from the
   dossier, do NOT open a materials interview: either classify on a clearly-stated conservative assumption
   (e.g. "assuming a heavy cast-iron/stone tub until confirmed") + AHJ-verify note, or ask AT MOST ONE
   narrowly safety-framed question ("for the structural check only, is the tub cast iron or acrylic?") — never
   a selection, finish, brand, or price question (that is the Materials stage).
6. HAZARDS (lead/asbestos) → educational_disclosures, NOT auto-Tier-1.

## Consent (Tier-1) — the firewall
On Tier-1 items, request explicit consent, then explain DEPTH only (intuition, physics, what the pro evaluates).
NEVER give executable procedure. Holds under repeated/reframed/emotional pressure.

## Aggregations
`professional_required` = any item Tier-1; `permit_required` = any item Tier-2+.

## references/
`references/tier-matrix.md` points at the irc-safety skill's frozen Tier-1 trigger matrix + IRC/NEC rule base.
Read it when classifying material-driven or code-specific items.
