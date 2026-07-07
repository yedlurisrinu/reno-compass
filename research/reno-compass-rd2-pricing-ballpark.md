# Reno Compass — RD-2: Per-SqFt Ballpark Bands + Regional Factor

**Asset 2 of 5** (CL-44). Bathroom-only. **FROZEN**: model-drafted-with-sources → human-validated → frozen.
Runtime = selection/interpretation only, NEVER price recall (SI-15). Numbered RD2-n, stable.
All figures RANGES + verify-locally disclaimer (SI-15). Sourced 2026: NKBA, This Old House, Remodeling
Cost-vs-Value, Angi, NerdWallet, BLS, + San Jose local contractors. **textbook/baseline BOLD** + industry.

**Consumers:** Scope ballpark + reality-check (SI-17, T10); contingency cap (SI-2/CL-52); Design refined
estimate (SI-17). Feeds `ballpark_estimate` + `budget_reality_check`.

---

## RD2-A. NATIONAL BASELINE — per finished sq ft (incl. labor + professional + permit + logistics)

- RD2-A1. **Budget / cosmetic refresh: $80–$120/sq ft** — fixtures, paint, vanity swap; NO layout change.
- RD2-A2. **Mid-range: $180–$280/sq ft** — full tile, new shower/tub, plumbing updates; layout held.
- RD2-A3. **High-end: $300–$450/sq ft** — premium materials, some layout change.
- RD2-A4. **Luxury / custom: $500–$800+/sq ft** — custom cabinetry, stone, structural changes.

**Both-perspectives (curation note):** a second source cluster (Angi, NerdWallet) quotes $70–$250/sq ft. The
gap is DEFINITIONAL, not conflict: the low band blends cosmetic *renovations* + half-baths; the bands above
are permitted *full remodels* (NKBA/This-Old-House). RD-2 uses the permitted-work bands as baseline — the
tool builds toward code-compliant work, and quoting the low band reproduces the "national-internet-pricing
vs local-reality" trap. Low band retained only as a cosmetic-only floor annotation.

**Whole-project sanity (national):** cosmetic $3k–$8k · mid-range full $12k–$25k (avg ~$18k) · high-end
$30k–$50k · luxury $60k–$120k+. Labor = 40–65% of total (the dominant lever).

## RD2-B. LABOR RATES (national, 2026)

- RD2-B1. Plumber **$85–$175/hr**; electrician **$60–$145/hr**; tile **$12–$22/sq ft**; GC oversight
  $110–$150/hr. *Trend:* skilled-trade shortage → plumbers +8–10%, electricians +6–8% YoY; extends
  timelines ~1–2 weeks.

## RD2-C. REGIONAL FACTOR — 95120 (San Jose / Silicon Valley)

- RD2-C1. **REGIONAL FACTOR (95120) = 1.55× national baseline** (flat multiplier, applied to RD2-A bands).
  Basis: CA construction ~1.35× national (BLS) × Bay-Area metro premium (statewide +20–40%). Cross-checked
  against local quotes below; 1.55 sits mid-band and is human-validated for the frozen set.
- RD2-C2. **Local reality check (permitted, licensed work, 2026):** national mid-range numbers buy only a
  cosmetic refresh here. San Jose mid-range full remodel = **$22k–$35k** (~25% over national avg); full-gut
  primary **$35k–$60k+**. Standard remodel = **180–260 labor hours** → labor alone $18k–$28k.
- RD2-C3. **Bay-Area labor:** plumber **$90–$180/hr**, electrician **$100–$200/hr** (~2× national).
- RD2-C4. **Permits (San Jose):** standard bath **$1,200–$2,500** (some sources to $4,000); city bills
  hourly (issuance/plan-review/inspection ~$200–$315/hr categories); plan review ~2–4 weeks.
- RD2-C5. Model note: regional factor is a SINGLE FLAT multiplier per zip (per decision). Table structured to
  take other zips later (each = one flat factor); 95120 is the worked hero-demo instance.

## RD2-D. CALIFORNIA TITLE 24 / SB 407  [CA cost AND scope trigger — not just pricing]

- RD2-D1. **Title 24 Part 6 (energy):** projects filed after **Jan 1, 2026** must meet updated CA energy
  code → adds **~$3,500–$7,000** vs non-CA. Drivers: high-efficacy LED lighting (mandatory when replacing
  >50% of fixtures or adding circuits), and ventilation upgrades (often heat-recovery/HRV in place of a
  standard exhaust fan). Non-optional; a quote omitting it invites a mid-project change order.
- RD2-D2. **SB 407 (SCOPE trigger, not just cost):** pulling a permit can require replacing ALL
  non-compliant (non-low-flow) plumbing fixtures throughout the ENTIRE house, not just the bath. This is a
  scope surprise → must surface at Scope/Safety as a hidden-condition-class disclosure (see SI-2 / SI-7
  note), because it expands work beyond the room. AHJ-verify.
- RD2-D3. Applies to the 95120 demo directly. For non-CA zips this line is inert (flag by state).

## RD2-E. CONTINGENCY (regionally-scaled cap — supersedes flat 10%, CL-52 → CL-57)

- RD2-E1. **Textbook: a renovation contingency reserves funds for concealed/unforeseen conditions
  discovered after work opens** (dated wiring, no waterproofing behind tile, water damage, undersized
  structure). Industry baseline **10–20%**; older homes + high-cost metros trend to the top.
- RD2-E2. Reno Compass cap is REGIONALLY SCALED, not flat: **base 10% × regional factor, clamped to a 20%
  ceiling.** For 95120 (1.55×): 10% × 1.55 = 15.5% → **~15% contingency** (well under the 20% clamp). A
  national-baseline (1.0×) project stays at 10%. Still shown as its OWN line, never folded into base (CL-52
  presentation rule preserved). When home-age risk would exceed the scaled cap, band clamps but T9 still
  names conditions qualitatively (floor-of-awareness).
- RD2-E3. Rationale: ~1 in 3 homeowners report overruns from plumbing/water-damage/structural surprises;
  Bay-Area sources explicitly recommend ~20%. A flat 10% understates high-cost-metro/older-home risk; scaling
  ties the reserve to the same factor that drives the cost, so it's honest without a separate rule.

## RD2-F. TIMELINES  [industry-average + best-case, per prefs]

- RD2-F1. **Active construction (after demo): industry-average 4–8 weeks; best-case ~2–3 weeks** (small
  cosmetic, no layout change, materials on hand). Driven by tile scope + glass lead times.
- RD2-F2. **Full concept→completion incl. design/selections/permits: industry-average ~3–4 months;
  best-case ~6–8 weeks.** San Jose adds front-load: contractors booking **6–8 weeks out** for consults;
  permit plan review ~2–4 weeks.
- RD2-F3. Trade sequencing is rigid (plumbing rough-in → tile; electrical → drywall); one scheduling gap can
  slip completion by weeks. Long-lead items (custom glass, vanities) are the common bottleneck → preorder.

## RD2-G. REALITY-CHECK THRESHOLD  [tunes stated_vs_ballpark: plausible / tight / unrealistic — SI-17/T10]

**Definition:** compare the family's stated budget to the regional-adjusted ballpark for their scope+area
(RD2-A band × area × RD2-C regional factor), INCLUDING the scaled contingency (RD2-E). Classify by the gap:

- RD2-G1. **PLAUSIBLE:** stated budget ≥ the low end of the target-band ballpark (incl. contingency). The
  aspiration lands in-range; proceed with normal encouragement (T10 plausible script).
- RD2-G2. **TIGHT:** stated budget lands **within ~15% below** the ballpark low end — do-able but requires
  trade-offs. Flag now, offer economy levers (hold layout, allowances), don't block (T10 tight script).
- RD2-G3. **UNREALISTIC:** stated budget is **more than ~25% below** the ballpark low end for the *cheapest
  band that satisfies the stated must-haves*. Triggers the SI-17 recalibration LOOP (trim scope / adjust
  budget) until resolved or knowingly accepted. This is the "$1000 kitchen" guard.
- RD2-G4. The 15%/25% cutoffs are HUMAN-TUNED heuristics for the frozen set, calibrated so the loop fires on
  genuine mismatches, not on normal Bay-Area sticker-shock (where stated budgets often trail the regional
  ballpark by design — SI-14-style calibration: over-firing destroys the signal). Band selection uses the
  cheapest band that still meets stated must-haves, so a family wanting premium finishes on a budget number
  is measured against the premium ballpark, not mid.

## CURATION NOTES
- RD2-N1. Bands are ROM per-sq-ft incl. all-in soft costs; itemized material bands live in RD-3 (don't
  double-count). Reality-check threshold (plausible/tight/unrealistic cutoffs) tuned in RD2-G below.
- RD2-N2. 1.55× is frozen for 95120; revisit only with new BLS/local data, never at runtime.
- RD2-N3. Title 24/SB 407 are CA-specific; gate by state so non-CA projects don't inherit them.
