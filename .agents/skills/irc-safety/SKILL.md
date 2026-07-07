---
name: irc-safety
description: Classify bathroom-remodel actions against IRC/NEC safety rules and the frozen Tier-1 trigger matrix. Use when determining permit needs, professional-required work, or structural/electrical thresholds for a bathroom renovation.
---

# Reno Compass — RD-1: IRC Bathroom Rules + Tier-1 Trigger Matrix

**Asset 1 of 5** (CL-44 reference curation). Bathroom-only (hero-demo scope). **FROZEN** reference:
model-drafted-with-sources → human-validated → frozen. Runtime role = selection/interpretation only,
NEVER recall/guess (SI-10, SI-15 discipline). Numbered RD1-n, stable.

**Sources basis:** 2021 IRC (Ch. 27 Plumbing, Ch. 39 Power & Lighting, Ch. 15 Exhaust) + NEC 210.8/210.11/
210.52 + ASSE scald standards + industry structural-review practice. All AHJ-VERIFY flagged — local
amendments override. Format per userPreferences: **textbook/code definition in BOLD** + industry practice;
both perspectives where they diverge.

**Consumers:** Safety (Stage 3) classification + Tier-1 matrix (SI-11, SI-30); DIY firewall (SI-9);
Design clearances (Stage 2); SI-7 triggers (scald/slip). Feeds the `envelope` on TierClassification (SI-30/31).

---

## RD1-A. ELECTRICAL  [well-defined; clean matrix thresholds]

- RD1-A1. **All bathroom receptacles must have GFCI protection (NEC 210.8(A)(1)).** The 2020 NEC expanded
  this to all 125–250V receptacles — so even a dedicated 240V circuit (e.g. bathroom heater) requires GFCI.
  *Industry:* GFCI applies within the whole bathroom envelope regardless of distance to sink/tub, AND to any
  receptacle within 6 ft of a tub/shower even just outside the room.
- RD1-A2. **At least one 20-ampere branch circuit must supply bathroom receptacle outlets (NEC 210.11(C)(3)),
  on #12 AWG minimum wire.** *Industry:* a single 20A circuit may serve receptacles in multiple baths, OR
  serve only one bath's receptacles — layout choice; 15A receptacles are allowed on a 20A multi-receptacle
  circuit (NEC 210.21(B)(1)).
- RD1-A3. **AFCI:** required in addition to GFCI for certain circuits in many jurisdictions — genuinely
  AHJ-variable. Treat as FLAG-FOR-LOCAL-VERIFY, not a fixed rule.
- RD1-A4. **Receptacle placement: at least one within 36 inches (914 mm) of the outside edge of each lavatory
  basin (NEC 210.52(D));** not more than 12 inches below the countertop.
- RD1-A5. **Never install a 20A receptacle on a 15A circuit** (fire hazard — wiring overheats before the
  breaker trips). Determinant is wire gauge: 12-gauge → 20A, 14-gauge → 15A.

**MATRIX (electrical → Tier-1):** new dedicated circuit, panel/service-side work, or a fixture whose amperage
forces a new circuit → **Tier-1 (professional-required).** Envelope: "≤20A on existing #12 branch, no new
circuit / no panel work." A fixture drawing beyond the existing circuit + code allowance breaches it (SI-31).
Swapping a GFCI receptacle or fixture on an existing adequate circuit = Tier-2/3 (not panel work).

---

## RD1-B. SCALD PROTECTION  [clean; one number — powers SI-7 child trigger]

- RD1-B1. **Shower and tub-shower valves must be balanced-pressure, thermostatic, or combination type, and
  must limit maximum water temperature to 120°F (49°C)** (IRC P2708.4; device per ASSE 1016; tub fill via
  ASSE 1017/1070 temperature-limiting device set to ≤120°F). *Industry:* set at the valve during rough-in;
  the SI-7 child-scald trigger fires here — anti-scald valve is code, not an upgrade.

---

## RD1-C. FIXTURE CLEARANCES  [clean numbers; Design-stage constraint]

- RD1-C1. **Lavatory (sink): 15 inches minimum from centerline to any side wall, partition, or vanity**
  (IRC P2705.1 item 5).
- RD1-C2. **Water closet (toilet): 15 inches minimum from centerline to any side wall/fixture each side; 21 inches
  minimum clearance in front** (IRC P2705.1).
- RD1-C3. **Shower: minimum finished interior 30 inches × 30 inches AND at least 900 sq inches of cross-sectional area**
  (IRC P2708.1), the 30 inches maintained above the drain to a height of 70 inches.
- RD1-C4. **Inspectors measure FINISHED surfaces — tile, tub apron, and finishes all count against the
  clearance** (not stud-to-stud). *Industry field note:* finish thickness is the #1 way a planned-compliant
  layout fails at final; budget the clearance against finished dimensions, not framing.
- RD1-C5. Grab bars / stanchions: IRC P2726 (+ R307) governs backing/placement where provided. Backing must
  be in-wall during rough-in — the SI-7 elderly trigger raises "add grab-bar backing now even if bars later."

---

## RD1-D. VENTILATION  [clean; Design + Materials]

- RD1-D1. **Bathrooms require natural OR mechanical ventilation (IRC R303.3).** Natural = openable window
  ≥3 sq ft with ≥½ openable. Mechanical = exhaust fan **≥50 CFM intermittent or ≥20 CFM continuous**
  (IRC Ch. 15 / M1507), vented **directly outdoors — never into attic, soffit, or crawl space** (M1505.2).
- RD1-D2. *Industry (both-perspectives):* code is a floor, not a target. HVI recommends ~1 CFM/sq ft (baths
  ≤100 sq ft); real installed airflow often drops to ~25–35 CFM on a "50 CFM" fan due to duct length/bends,
  so designers oversize. Add ~50 CFM for jetted tub, ~25 for steam/multi-head. Windowless bath → mechanical
  effectively mandatory.
- RD1-D3. Fan over a tub/shower → GFCI-protected + damp-rated. (Ties RD1-A1.)

---

## RD1-E. WATERPROOFING  [wet-area; SI-7 wet trigger]

- RD1-E1. **Contact areas where fixtures meet walls/floors must be watertight (IRC P2705.1); showers require
  a watertight receptor/liner sloped to drain** (P2709 — shower lining sloped ¼ in/ft to the weep holes;
  receptor min. depth per code). *Industry:* modern practice = sheet or liquid membrane (e.g. Schluter-Kerdi
  class) behind tile; "no waterproofing behind tile" is the classic older-home hidden condition (SI-2). The
  SI-7 wet-area trigger raises slope-to-drain + membrane expectation. Waterproofing itself is Tier-3 DIY-able,
  but a FAILED existing one discovered on demo is a hidden-condition cost (T9).

---

## RD1-F. STRUCTURAL LOAD  [NOT a clean threshold — two-gate trigger; the load-bearing matrix decision]

**Textbook baseline (BOLD): residential floors are designed for ~40 lbs/sq ft live load plus ~10 psf dead
load. Determining ACTUAL floor joist capacity requires a structural engineer** — it depends on lumber
species, grade, Fb/E values, span, spacing, and condition the tool cannot see. The numbers below decide
ONLY *whether to raise the professional-review flag*, NEVER whether a floor is safe.

**Why weight-alone is wrong (both-perspectives, the calibration point):** the 40 psf figure is a *distributed*
load; heavy fixtures load as *concentrated* points (a clawfoot tub puts most weight on four small feet — the
subfloor can crush locally even if joists are fine). And water dominates: switching cast-iron→acrylic saves
~300 lb, but the water alone is 500+ lb. A filled soaking/spa tub routinely hits 1,000+ lb on its own — so a
flat 1,000 lb trigger would fire on nearly every freestanding tub and destroy the signal (SI-14).

**TWO-GATE STRUCTURAL TRIGGER:**
- RD1-F1. **Gate 1 — floor type.** SLAB → structural trigger does NOT fire (capacity rarely the concern;
  redirect to plumbing-relocation cost — moving a drain through concrete is the real slab cost). FRAMED floor
  → proceed to Gate 2.
- RD1-F2. **Gate 2 — framed floor, filled-weight band × aggravating condition:**
  - **≥ ~1,500 lb filled** (concrete/stone tubs, large cast-iron soakers, long stone-slab vanity runs) →
    **Tier-1 "structural review required" — REGARDLESS of other conditions.** ("clearly heavy" ceiling.)
  - **~800–1,500 lb filled** → **Tier-1 "structural review" ONLY IF an aggravating condition also holds:**
    span > ~12 ft (2×8 @ 16-inch OC tops out ~12–13 ft at 40 psf), upper floor, or home old enough to suspect
    undersized/degraded joists. ("depends" band.)
  - **< ~800 lb filled** → no structural flag (ordinary acrylic on slab or sound framing).
- RD1-F3. **Output is always "this warrants a professional structural review, and here's the intuition why"
  (SI-9 depth-not-procedure) — NEVER "your floor holds / doesn't hold," NEVER a reinforcement spec** (no
  "sister the joists" how-to). Consent unlocks understanding, not DIY structural work.
- RD1-F4. Envelope stored on TierClassification for structural items = a TUPLE, not a psf number:
  `{ filled_weight_band, floor_type, aggravating_conditions[] }` (SI-30/31 refinement — see CL-55).
  Materials (Stage 5) validates the concrete product's filled weight + footprint against this; breach →
  one-item Safety re-open (SI-31).

**Filled-weight estimation aid (industry averages, for band placement — not adequacy):** water ≈ 8.34 lb/gal
(62.4 lb/cu ft); acrylic tub 60–120 lb empty; steel 80–120; solid-surface/stone-resin 150–400; cast iron
300–500+ (clawfoot often >400). Add occupant load. A 70–80 gal fill ≈ 580–670 lb water alone.

---

## RD1-G. PERMIT-TRIGGER SUMMARY  [what typically needs a permit — AHJ-verify all]

- RD1-G1. Electrical: new circuit / panel work → permit + licensed electrician (Tier-1). Like-for-like
  receptacle/fixture swap on adequate existing circuit → often no permit (AHJ-varies).
- RD1-G2. Plumbing: moving/adding drain or supply lines (fixture relocation) → permit (Tier-2, DIY-feasible
  where legal but inspected). Like-for-like fixture swap → often no permit.
- RD1-G3. Structural: any reinforcement / joist modification / load-path change → permit + engineer (Tier-1).
- RD1-G4. Mechanical: new/relocated exhaust duct penetration → often permit (AHJ-varies).
- RD1-G5. **Every permit line is AHJ-flagged: state which rule fired and "verify with your local Authority
  Having Jurisdiction"** (SI-10, SI-13). The tool never asserts a permit is/ isn't needed as fact.

---

## OPEN / CURATION NOTES
- RD1-N1. Shower receptor depth + exact P2709 slope citations pinned to 2021 IRC; if project adopts 2024 IRC,
  re-verify (2024 cycle in progress in several states per sources).
- RD1-N2. Structural bands (800/1,500 lb) are industry-practice review heuristics, human-validated for THIS
  frozen set; not engineering calcs. Revisit only with a structural source, not runtime.
- RD1-N3. AFCI-in-bath and dual-fan-duct rules are AHJ-interpreted — kept as flags, not fixed rules.
