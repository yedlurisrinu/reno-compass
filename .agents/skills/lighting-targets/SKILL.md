---
name: lighting-targets
description: Provide IES illuminance targets per bathroom zone and California Title 24 JA8 cross-checks. Use when specifying lighting for a design or recommending finishes against available light.
---

# Reno Compass — RD-4: IES Lighting Targets + CA Efficacy Cross-Check

**Asset 4 of 5** (CL-44). Bathroom-only. **FROZEN**: model-drafted-with-sources → human-validated → frozen.
Runtime = selection/interpretation only (SI-18). Numbered RD4-n, stable. Sourced: IES Lighting Handbook
(10th ed.) via published references, IES Illuminance Selector, CA Energy Commission 2025 Title 24 / JA8.
**textbook/standard BOLD** + industry.

**Two axes, kept separate (the cross-check that matters):** IES sets the ILLUMINANCE TARGET (how much light a
task needs). Title 24 / JA8 constrains the PRODUCT (efficacy/CRI/CCT/controls you're allowed to install in
CA). They don't conflict — you hit the IES target USING a JA8-compliant fixture. RD-4 gives both so Design
picks a target and Materials picks a compliant product.

**Consumers:** Design per-room lighting_requirements (SI-18); Materials finish/fixture recommendation (SI-21);
CA compliance flag (RD2-D1). Feeds `lighting_requirements` per room.

---

## RD4-A. IES ILLUMINANCE TARGETS — by bathroom zone  [the "how much light" axis]

**Textbook: illuminance is measured in footcandles (fc) = lumens per sq ft (1 fc = 10.764 lux); IES publishes
average-maintained fc targets per task.** Bathroom is mixed-task — general vs vanity differ sharply.

- RD4-A1. **General / ambient (overall room): ~30 fc.** Circulation-safe, shadow-free base layer.
- RD4-A2. **Vanity / grooming (task, at the face — VERTICAL illuminance): ~70–80 fc.** Highest-need zone;
  the reason a single ceiling light is never enough. *Industry:* achieve with sconces flanking the mirror OR
  mirror-integrated light for shadowless, cross-lit faces — not just overhead (overhead alone casts
  under-eye/chin shadows).
- RD4-A3. **Shower/tub (task within wet zone): ~30 fc**, via a wet-location-listed (damp/wet-rated) recessed
  downlight (ties RD1-D3 GFCI). *Industry:* windowless/enclosed showers read darker — add a dedicated fixture.
- RD4-A4. **Accent (optional): highlights niche/architecture; not a task minimum.**

**Lumen buildup (the tool's compute, SI-18):** target_lumens = zone_area(sq ft) × target_fc, for an 8-ft
ceiling. Higher ceiling → scale up proportionally. Worked example (80 sq ft bath): general 80 × 30 = **2,400
lm**; vanity task 10 sq ft × 80 = **800 lm** → **~3,200 lm total.** Dark/matte walls absorb → add 10–20%;
light walls reflect → reduce.

## RD4-B. LIGHT QUALITY — CRI + CCT  [applies everywhere; stricter in CA]

- RD4-B1. **CRI (color-rendering index): use ≥90 for grooming/task** (accurate skin tone, makeup, color
  matching). *Industry:* general spaces tolerate 80+, but vanity should be 90+.
- RD4-B2. **CCT (correlated color temperature): 2700K–4000K for bathroom.** Warmer (2700–3000K) = spa/relax;
  neutral (3500–4000K) = crisp grooming. Tunable-white fixtures span both (morning-crisp / evening-warm).
- RD4-B3. **Layer three types:** ambient (base), task (vanity/shower), accent (optional). A single fixture
  cannot serve all three — the per-room requirement should specify the layers present.

## RD4-C. CALIFORNIA TITLE 24 / JA8  [the "what product is allowed" axis — 95120 demo]

- RD4-C1. **2025 Energy Code (permits on/after Jan 1, 2026): ALL residential fixtures must be JA8-compliant
  (high-efficacy).** For alterations, only fixtures you actually change must comply — untouched existing
  fixtures may stay (Ch. 9 alterations rule). New/modified lighting + its controls must fully comply.
- RD4-C2. **JA8 requires (per fixture): high efficacy (LED ~80–100+ lm/W), CRI ≥90, CCT 2700–4000K,
  dimmable, low flicker, instant/qualified start, rated life.** *Convenient overlap:* JA8's CRI≥90 + CCT
  2700–4000K MATCH the IES quality targets (RD4-B) — so a JA8 product satisfies both axes at once.
- RD4-C3. **Controls (2025, mandatory): bathrooms require at least one luminaire on an occupancy/vacancy
  sensor** (auto-off when empty). *Note:* lighting integral to bath vanity mirrors and exhaust fans is
  EXEMPT from the general efficacy standard (RD4-C uses this — a mirror-integrated vanity light is exempt,
  but a separate sconce is not).
- RD4-C4. **Recessed downlights (e.g. shower can):** must be airtight/IC-rated (ICAT), non-screw-base, and
  the source JA8-2025-**E** (elevated-temperature) rated for enclosed use.
- RD4-C5. **Verify product listing** in the CEC MAEDbS database before install; a HERS-verified item may be
  required (missing verification = top inspection-fail cause). AHJ/CEC-verify.

## RD4-D. INSTALL TIMELINES  [industry-average + best-case, per prefs]

- RD4-D1. **Fixture swap (like-for-like, existing wiring): avg a few hours; best-case <1 hr.**
- RD4-D2. **New vanity sconces / added fixture (new box + wiring on existing circuit): avg ~half-day per
  location; best-case ~2 hrs** where wall is open (gut). Tier-2 (electrician, no panel work).
- RD4-D3. **New circuit / panel work: Tier-1** (RD1-A) — schedule with the electrical rough-in, not standalone.

## CURATION NOTES
- RD4-N1. IES targets are AVERAGE-MAINTAINED design values, not code minima (code rarely within 10% of IES).
  The tool presents them as design guidance + "verify with a lighting pro for exact layout" (beam angle,
  reflectivity, glare not in the simple formula).
- RD4-N2. JA8/Title 24 apply only in CA — gate by state (like RD2-D). Non-CA projects use IES targets +
  general CRI/CCT guidance without the JA8 product constraint.
- RD4-N3. Fixture-count/lumen math is a deterministic TOOL (SI-18), not model recall; this table is its
  reference. Revisit only with new IES/CEC data, never runtime.
