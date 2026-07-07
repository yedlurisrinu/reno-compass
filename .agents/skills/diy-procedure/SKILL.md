---
name: diy-procedure
description: Generate and refine step-level DIY procedures for non-Tier-1 bathroom work, with Tier-1 dependencies woven in only as hold-points. Use at the conditional DIY Planning stage.
---

# DIY Procedure

Produce step-level procedure for the work the family will do themselves — refine-not-reclassify (SI-26), with
the Tier-1 firewall absolute (constitution Principle 1).

## Full-scope visibility, firewalled generation (SI-9 / CL-78)
The stage receives the FULL classified item set and partitions {Tier-1 = sequence-anchor only} vs {non-Tier-1 =
procedure targets}. Generate procedure ONLY for non-Tier-1 items. The model SEES Tier-1 items for correct
SEQUENCING but writes NO how-to for them — they appear ONLY as `hold_points` ("wait for the licensed [trade]
here before the next DIY step"). This is stronger than hiding them: it makes the pro↔DIY handoff explicit
instead of silently assuming the pro work already happened.

## Eligibility = ALL non-Tier-1 (Tier-2 + Tier-3)
Every Tier-2 (permitted) and Tier-3 (proceed) item is DIY-eligible. A Tier-2 item is DIY-able *with a permit*
— its procedure MUST include the permit/inspection hold-points and state plainly that a permit is required.
There is NO separate prior "self-perform consent" gate; whether the family actually does an item is decided
per item in the DIY loop (`user_feasible`).

## One item at a time
The app pins ONE active item and hands it to you. Produce tools + procedure for THAT item only — never list or
preview the others. The decision is atomic for the whole item (all of it or none of it); no partial hand-off
within one Safety bundle. When decided, the app advances to the next item.

## How to reason
- "Applicable" is a DERIVED predicate: does the non-Tier-1 set contain anything AND did the family not choose
  contractors-for-everything at the Contractor stage? If either fails, the stage is skipped.
- Family alters a step by experience → INCORPORATE and tighten; this REFINES, it does NOT reclassify the tier.
- Family opts to hire an item out → recorded as THEIR personal choice (`reclassify_to_professional`); the item is
  surfaced in Synthesis under the contractor's scope. NOT a tier change, NOT a cascade.
- Each procedure carries a timeline: industry-average + best-case, and its own `tools[]`.

## Output
One `procedures[]` entry for the ACTIVE item only (item, tier ∈ {tier_2, tier_3}, steps, hold_points, timeline,
tools[], and the per-item `user_feasible` / opt-out decision).
