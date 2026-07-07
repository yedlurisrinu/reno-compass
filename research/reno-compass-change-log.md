# Reno Compass — Change Log (CL)

Decision-history and resolved design decisions. Kept out of the system-instruction file (which is
pure behavioral instruction). Terse by design; enrich later if needed. Numbered CL-n, stable.

---

## Schema / data-model decisions
- CL-1. project_type free text; RoomElement.category guided enum + "other".
- CL-2. measurements: keep user-supplied + agent-derived (audit). schema_version single global.
- CL-3. chosen_design = immutable object (full copy at confirmation); options[] retained alongside (trim deferred).
- CL-4. conversation captured per-stage in dossier; SectionStatus tracks pipeline progress only.
- CL-5. likelihood field removed (weight hidden conditions via home_age instead).
- CL-6. quote: text + PDF only; audit reasons over extracted text (no vision).
- CL-7. hand_orientation: room-level, optional. sub_spaces: SubSpace object. preferences: global + area-scoped.
- CL-8. budget: target + ceiling. timing captured in Scope; weather = reasoning, not stored data.
- CL-9. pricing: curated tier-band table (basic/mid/premium) + regional factor; model-assisted offline
  curation, frozen; runtime = selection/interpretation only; allowances for wild-variability finish items.
  Live county-level API (1build-class) = roadmap. No budget figure emitted at Scope beyond ballpark.
- CL-10. phase checklists rolled into Synthesis. special_considerations flagged [SENSITIVE].
- CL-11. lighting_requirements + intended_materials are PER-ROOM (on layout rooms), not option-level;
  global = aggregate of rooms.
- CL-12. materials line_items keyed by room_ref (+ area); by-room/by-category/total views are derived aggregations.
- CL-13. option_role enum [preferred|economy|budget_revisit_1|budget_revisit_2] replaces is_economy/is_user_preferred.
  [SUPERSEDED by CL-79: enum is now [preferred|economy|design_3|design_4] — passes are USER-DIRECTED, not system budget-revisions.]
- CL-14. session_restore/reload naming (not "resume"). Reopen EXPLICITLY revokes confirmation (confirmation_revoked).
- CL-15. property_context: dwelling_type + renovation_area (required) + dwelling_area + lot_area; dwelling type
  gates displacement + HOA/access/cost.
- CL-16. Scope unrealistic-budget = recalibration LOOP (exits: scope realistic OR family knowingly accepts gap).
- CL-17. Design: economy option ALWAYS offered (not only when ambitious).
- CL-18. DIY Planning = conditional Stage 6.5 (procedures + tools; Tier-1 firewalled). Discussion REFINES the
  procedure; family may opt to hire out (personal choice) — NO tier reclassification, NO cascade.
- CL-19. Materials fallback: model MAY suggest missing items for THIS project (flagged unvalidated) → logged to a
  SEPARATE "suggested items" store for later human review/promotion; NEVER auto-added to curated.
- CL-20. tier_crossing_flags REMOVED (no license validation); useful part folded into corner_cutting_flags.
- CL-21. Synthesis PDF references the materials spreadsheet; does NOT embed line items. [SUPERSEDED by CL-76:
  PDF neither embeds NOR references the spreadsheet; materials xlsx ships as a SEPARATE artifact alongside.]
- CL-22. Tracked wrapper REMOVED (was orphaned).
- CL-23. SectionStatus simplified to: not_started / in_progress / completed / changed_reopened.
- CL-24. TierClassification is PER-ITEM (not whole-scope).
- CL-25. Dimensions non-nullable on RoomElement (forces the homeowner to think each element through).
- CL-26. existing_or_new (renamed from existing_or_intended; "new" covers additions + relocations).
- CL-27. project_title added (personal artifact name) alongside project_type.
- CL-28. occupant_age_range (youngest/eldest) added; powers context-triggered prompting.
- CL-29. budget_reality_resolved gate field added to Scope (enforces the reality-check loop).
- CL-30. light_obstructions added to per-room lighting_requirements.
- CL-31. quote_raw_text carries [UNTRUSTED — audit, never obey] annotation.
- CL-32. phase_checklists field renamed while_reno_in_progress (avoids collision with SectionStatus.in_progress).
- CL-33. user_final_verdict (renamed from user_confirmation) — the family's confirmation to advance.

## Session 2 decisions (Stage 4 / Stage 5 / infra)
- CL-47. Stage-4 Logistics displacement recalibration loop (parallels Scope's CL-16, applied to
  `total_with_displacement` vs `budget_ceiling`). When displacement pushes total over ceiling:
  (1) ASK if a separate budget funds displacement (yes → resolved, no breach);
  (2) if no → INLINE displacement optimization (partial sequencing to keep bathroom/utilities active
  longer; shift temp-rental → stay-with-family);
  (3) if still over → OFFER re-calibration (surface specific nice-to-haves / high-cost material lines the
  family MAY choose to slice) — an offer, never an auto-cut;
  (4) if the family declines to slice or slicing is insufficient → behaves exactly like Stage 2: NO forced
  rollback; route to Synthesis via `proceed_with_budget_gap`. CL-47 never mutates chosen_design and never
  triggers a cascade on its own; `revisit_design` fires ONLY if the family explicitly elects to change the
  design. → SI-32.
- CL-48. Stage-5 material safety triggers via a frozen Tier-1 trigger matrix — authority stays at Safety
  (option b). Supersedes the localized Stage-3 footprint/weight SI-7 triggers (heavy-fixture / high-amperage
  now handled by the matrix). Model: (i) Safety (Stage 3) evaluates each INTENDED material TYPE against the
  frozen matrix (point-load vs joist capacity, amperage draw vs panel/circuit) and records the physical
  ENVELOPE the classification assumed (stored on TierClassification); (ii) Materials (Stage 5) does NOT
  classify — a code-level check (SI-29 pattern) compares the concrete product's spec to the stored envelope;
  within → tier holds silently, no cascade; breach → flag + re-open Safety for THAT ONE item, which
  re-classifies (likely Tier-1 professional-install), re-consents (SI-9), and block-tracks it out of DIY.
  Single classification authority preserved; backward cascade (5→3) is the guarded exception, not a default.
  REQUIRES Design elicitation to probe intended material types to matrix fidelity (natural-vs-engineered
  stone, slab thickness/weight class, fixture amperage). → SI-30 (Safety), SI-31 (Materials), schema
  TierClassification.envelope; Design question-bank probe pending (Stage 2 draft).
- CL-49. Context-window token mitigation + conversational summary gate. On stage `completed`, raw
  `list[ConversationTurn]` is archived to deep storage (Firestore/Bigtable-class); active working memory
  carries forward only a crisp summarized-Markdown string of core design decisions (maximizes context
  caching across 7+ sequential stages). SAFETY CARVE-OUT (mirrors SI-4 restore rule): safety classifications,
  consent state, and tier-matrix envelopes are ALWAYS read from the structured dossier, NEVER from the
  summary string. The summary is a prompt-conditioning convenience for design continuity, NOT a second state
  channel — dossier remains the sole inter-stage source of truth for anything safety- or number-critical.
  → SI-33.
- CL-50. `zipcode` added to `property_context` (REQUIRED) — drives the regional cost factor (SI-15/CL-9).
  Operationally necessary for pricing, so captured plainly with a one-line "why," NOT tagged [SENSITIVE]:
  a zip is a COARSE region, not an exact address, so it carries no precise-location risk. Asked EXPRESSIVELY
  (explain the why + "just the zip, nothing more precise") — turns a data-ask into a trust moment; a
  demonstrable aspect for the demo (the "informed, not anxious" posture in miniature). → schema
  property_context; T2 question bank.
- CL-51. T1 WHY-probe extended with a resale motive ("...or putting the house up for sale?") alongside
  problem-driven and aspiration-driven framings. Question-bank-only; no schema change (stated_goal free text).
- CL-52. RESOLVED (D1): Scope ballpark INCLUDES a home-age-weighted contingency band, option (a) — but
  CAPPED at 10% of ballpark and shown as its OWN line (base + contingency), never folded in (avoids a padded/
  tight-looking base). When true risk exceeds 10%, the band caps while T9 still names conditions qualitatively
  (cap = floor-of-awareness). → SI-2, SI-17, schema ballpark_estimate.contingency, T9/T10 question bank.
- CL-53. RESOLVED (F2): topic-dependent gate coverage. Non-sensitive topics (T1,T2,T5,T6,T7,T8) MUST be
  answered — no skip (no-shortcuts spine). Sensitive/optional topics (T3 ages, T4 special_considerations) may
  be declined: field 3-state = value (answered) / `"skipped"` (declined) / `null` (not-yet-asked). Gate
  satisfied on answered-or-skipped; `null` still requires the agent raise it once; a skip is never re-asked
  (SI-6). Sensitive questions are signposted optional at ask-time. accessibility/health/pets skip = no
  constraint (proceed); a skipped age just doesn't fire SI-7 triggers. Fixes the null=both-unasked-and-
  declined overload that would have re-asked declined sensitive Qs. → SI-6, SI-29, schema
  occupant_age_range + special_considerations, Scope GATE + T3/T4 question bank.
- CL-54. RESOLVED (allergies carve-out to CL-53): allergies has NO resting `"skipped"` state — a skip there
  would let the tool stamp a material screened=true without screening (a physical false all-clear the tool
  itself causes). On decline, ONE confirmation ("proceed as though no known allergies?") resolves it to an
  explicit empty list `[]` = confirmed-none (family vouched), which screens legitimately as clear. Asked once,
  never looped. Other three sensitive fields keep their `"skipped"` resting state. → SI-6, SI-29, schema
  special_considerations.allergies, T4 question bank.
- CL-55. RESOLVED: structural Tier-1 trigger is a TWO-GATE tuple, not a point-load number (RD1-F). Gate 1
  floor type (slab suppresses); Gate 2 framed → ≥1,500 lb filled fires regardless, 800–1,500 lb fires only
  with an aggravating condition (span>12ft / upper floor / old joists). Output = "professional structural
  review + intuition why" (SI-9), never an adequacy verdict or reinforcement spec. TierClassification.envelope
  refined: electrical form (amperage) vs structural form (filled_weight_band × floor_type ×
  aggravating_conditions). Reason: floor capacity needs an engineer (species/grade/Fb/E/span/condition the
  tool can't see); a single psf figure = false precision, and a flat 1,000 lb trigger over-fires on normal
  freestanding tubs (SI-14). → SI-30, schema envelope, RD1-F.
- CL-56. Reference curation started (CL-44), one artifact per asset (RD-1..RD-5), bathroom-only, national
  baseline + regional factor. RD-1 (IRC bathroom rules + Tier-1 matrix) FROZEN: electrical (GFCI-all,
  20A/#12, AFCI-AHJ-flag), scald 120°F, clearances (lav 15″, WC 15″/21″, shower 30×30/900sq-in, finished-
  surface), ventilation (50/20 CFM outdoors), waterproofing (slope-to-drain + membrane), structural two-gate
  (CL-55), permit-trigger summary (AHJ-flagged). Sourced 2021 IRC + NEC + ASSE + industry practice; textbook-
  bold + industry, both-perspectives per prefs. Pending: RD-2 per-sqft ballpark bands, RD-3 itemized material
  bands, RD-4 IES lighting targets, RD-5 standard-quote checklist; + Scope reality-check threshold tuning.
- CL-57. SUPERSEDES CL-52's flat 10% cap: contingency cap is REGIONALLY SCALED — base 10% × regional factor,
  clamped at 20% (RD2-E). 95120 (1.55×) → ~15%; national baseline → 10%. Presentation rule from CL-52 kept
  (own line, never folded; floor-of-awareness when clamped). Reason: San Jose data shows ~1-in-3 overruns and
  local practice recommends ~20%; flat 10% understates high-cost-metro/older-home risk; scaling ties the
  reserve to the same factor driving cost. → SI-2, SI-17, schema ballpark_estimate.contingency, RD2-E.
- CL-58. CA Title 24 / SB 407 captured (RD2-D). Title 24 Part 6 (post-Jan-1-2026 filings) adds ~$3.5k–$7k
  (high-efficacy LED, HRV ventilation). SB 407 is a SCOPE trigger: pulling a permit can force house-wide
  non-low-flow fixture replacement — surfaced as a hidden-condition-class disclosure (SI-2), AHJ-verify,
  gated by state. → SI-2, RD2-D.
- CL-59. RD-2 (per-sqft ballpark bands + regional factor) FROZEN. National baseline bands (budget/mid/high/
  luxury per-sqft, permitted-work definition; low $70–250 band noted cosmetic-only), labor rates, 95120 flat
  regional factor 1.55× (CA 1.35 × Bay-Area premium), permits, Title 24/SB 407 (CL-58), regionally-scaled
  contingency (CL-57), timelines (avg 4–8wk construction / 3–4mo full; best-case 2–3wk / 6–8wk). Sourced
  NKBA/This-Old-House/Cost-vs-Value/BLS/San-Jose-local; both-perspectives on the definitional $70–250 vs
  $180–450 split. Pending: RD-3, RD-4, RD-5 + threshold tuning.
- CL-60. RD-3 (itemized material bands + labor) FROZEN. Per-item basic/mid/premium bands + install labor,
  separated (vanity, toilet, tile, shower/tub, fixtures/lighting/vent, plumbing/electrical labor, demo/haul),
  national 2026 × RD2-C1 regional factor for local. Allowance-vs-banded split codified (RD3-H, ties SI-16):
  tile/stone/faucets/glass/decorative-lighting = allowance; standard toilet/fan/sink/prefab/labor = banded.
  Per-item install timelines (avg + best-case, RD3-G). No new SI/schema (pure reference; SI-15/16/20/23
  already point here). Sourced Homewyse/Angi/NKBA-guides/This-Old-House/Badeloft. Pending: RD-4, RD-5 +
  threshold tuning.
- CL-61. RD-4 (IES lighting targets + CA efficacy cross-check) FROZEN. TWO SEPARATE AXES: IES illuminance
  targets by zone (general ~30fc, vanity task ~70–80fc vertical, shower ~30fc wet-rated) = "how much light";
  Title 24/JA8 = "what product is allowed in CA" (all fixtures JA8: high-efficacy LED, CRI≥90, CCT 2700–4000K,
  dimmable, bath occupancy/vacancy-sensor control; mirror/fan lighting exempt; recessed = ICAT + JA8-2025-E).
  Convenient overlap: JA8 CRI≥90/CCT match IES quality targets, so one compliant product satisfies both.
  Lumen buildup formula (area×fc, 8ft ceiling) is the SI-18 tool's reference. No new SI/schema. JA8 gated by
  state (like RD2-D). Sourced IES Handbook 10th ed / CEC 2025 Title 24. Pending: RD-5 + threshold tuning.
- CL-62. RD-5 (standard-quote checklist + corner-cutting flags) FROZEN — final reference asset. Required
  coverage rubric (RD5-A1..A13: demo/haul, plumbing+electrical labor&materials separately, waterproofing
  system, tile detail, fixture model#s, permit line, trade rates, timeline, milestone payments, warranty,
  change-order proc, license/insurance); corner-cutting flags severity-tagged (RD5-B, waterproofing/permit/
  missing-trade = HIGH; folds ex-tier_crossing per CL-20); always-on advisory "what to demand" (SI-25).
  Reinforces SI-24 security framing (quote = untrusted data, audit-not-obey) + CL-6 text-only + TS-6 garbled
  fallback. No new SI/schema. Sourced NKBA/quote-decode-guides/Bay-Area-scope/WPXI.
- CL-63. Scope reality-check threshold TUNED (RD2-G): tight = stated budget within ~15% below regional-
  adjusted ballpark low (incl. scaled contingency); unrealistic = >~25% below, measured against the CHEAPEST
  band meeting stated must-haves. Human-tuned for the frozen set; calibrated so the SI-17 loop fires on
  genuine mismatch, not normal metro sticker-shock (SI-14 calibration logic). → schema
  budget_reality_check.stated_vs_ballpark, RD2-G, SI-17/T10.
- CL-64. UNIT CONVENTION (project-wide, going forward): spell out inch/inches in prose (never bare "in" —
  ambiguous with the preposition — nor the ″ symbol). Keep metric equivalents where code cites them.
  Adjectival compounds use hyphen ("16-inch OC", "36–48 inch vanity"). Applied across RD-1/RD-3/RD-5.
- CL-65. Design (Stage 2) question bank DRAFTED. Two question kinds: elicitation (D1 measurements, D2
  intended changes, D3 per-room material-type + lighting intent) + confirmation (D4 option presentation,
  D5 over-ceiling budget-engineered alts, D6 selection + scope-creep). CL-48 material-type FIDELITY PROBE
  lives in D3 — pressed ONLY for heavy/high-draw items (stone/big tub/motor/heat), not every surface (avoids
  noise). Schema `intended_materials` EXTENDED with fidelity fields (composition / weight_class /
  amperage_note, null for ordinary finishes) so D3 output feeds Stage-3's RD-1 Tier-1 matrix (SI-30). No
  skip states (Design facts required, unlike Scope optional-sensitive). → question bank Stage 2, schema
  Room.intended_materials. Pending: Stages 3–8 question banks, then CL-45 state-machine.
- CL-66. Safety (Stage 3) question bank DRAFTED — compute-and-consent, minimal elicitation. Topics: S1 present
  per-item classifications (SI-11, sourced), S2 Tier-1 depth-not-procedure consent (SI-9 firewall; holds under
  reframed/emotional pressure, TS-1), S3 permit/AHJ disclosure (+ CA Title 24/SB 407 gated by state), S4
  educational hazard disclosure (lead/asbestos = inform, NOT auto-Tier-1, SI-14), S5 material-envelope record
  (RD-1 matrix → TierClassification.envelope for Materials validation, SI-30/31), S6 confirm. Per prefs:
  textbook/code rule BOLD (from RD-1) + industry practice on each classification. No new SI/schema; entire
  section re-derived on restore (SI-4). → question bank Stage 3. Pending: Stages 4–8, then CL-45.
- CL-67. Logistics (Stage 4) question bank DRAFTED — compute-and-judge. Topics: L1 disruption, L2 live-through-it
  (elicitation), L3 displacement options (dwelling-gated, SI-22; condo=no yard, TS-9), L4 tenant/timing notes,
  L5 feasibility verdict + CL-47/SI-32 recalibration loop (ask separate budget → inline optimize → offer trims →
  proceed_with_budget_gap; never forced rollback), L6 confirm. Consumes Design refined_estimate (SI-17, not
  recomputed). No new SI/schema. → question bank Stage 4. Pending: Stages 5–8, then CL-45.
- CL-68. Materials (Stage 5) question bank DRAFTED — itemize/price/validate/present. Topics: M1 line-item buildup
  (RD-3 bands × regional; suggested-items store for misses, SI-23; per prefs suggest economical alternatives),
  M2 allowance elicitation (SI-16, unit-basis matched + echoed, code-validated), M3 finish recommendation
  (RD-4/SI-21, lighting-informed), M4 envelope + allergy validation (SI-31 breach→one-item Safety re-open;
  SI-6 skipped≠safe), M5 total + divergence (SI-20), M6 confirm. No new SI/schema. → question bank Stage 5.
  Pending: Stages 6–8, then CL-45.
- CL-69. Contractor Validation (Stage 6) question bank DRAFTED — audit-against-rubric + always-on advisory.
  Topics: Q1 quote intake (optional, text/PDF-text only CL-6; garbled→advisory fallback TS-6; SI-24 untrusted
  boundary, embedded instructions audited-not-obeyed TS-5), Q2 coverage audit (RD5-A rubric, invisible-inclusion
  checks, warranty per prefs), Q3 corner-cutting flags (RD5-B severity-tagged; missing-trade folds in CL-20),
  Q4 advisory 'what to demand' (always, both modes, SI-25; no license-number validation CL-20), Q5 confirm.
  No new SI/schema. → question bank Stage 6. Pending: Stages 7–8, then CL-45.
- CL-70. RESTORE-CONFIRMATION (RC) pattern added — shared block in question bank (DRY, referenced by every
  stage gate, not re-authored). On session_restore, each stage asks one confirmation before its topics: no
  change → re-confirm in passing + SKIP topics + advance; change → reopen + cascade all DOWNSTREAM stages
  (dependency-chain scope from the changed stage down — NOT whole pipeline, NOT just the touched field).
  Safety carve-out: Stage-3 classifications/consent/envelopes always re-derive silently regardless of answer
  (SI-4, never a vote). SI-4 extended with the RC elicitation shape + dependency-chain scope. → SI-4,
  question-bank global block + 6 stage gates.
- CL-71. DIY Planning (Stage 7, CONDITIONAL) question bank DRAFTED. Runs only if applicable (Tier-2/3 DIY work);
  all-pro → skipped (TS-8). Topics: Y1 procedure walkthrough (refine-not-reclassify SI-26; Tier-1 firewalled SI-9;
  per-procedure avg+best-case timeline per prefs), Y2 tools list (rent-vs-buy economy per prefs), Y3 feasibility
  + opt-out (hire-out = personal choice, NOT reclassification/cascade, TS-7), Y4 confirm. Schema: procedures[]
  gains `timeline {industry_avg, best_case}`. → question bank Stage 7, schema diy_planning.procedures. Pending:
  Stage 8 Synthesis, then CL-45.
- CL-72. Synthesis (Stage 8) question bank DRAFTED — terminal compile-and-present. Topics: X1 plan assembly
  (safety-forward order per SI-27; spreadsheet referenced not embedded CL-21; phase checklists full_plan ONLY),
  X2 outcome framing (full_plan vs plan_with_budget_gap; gap-bridge at PDF END, 'gap to bridge' never 'not
  feasible', SI-27), X3 deliver+confirm → current_stage complete. No new SI/schema (schema already matched
  SI-27). QUESTION BANK NOW COMPLETE (all 8 stages). Pending: CL-45 state-machine.
- CL-73. Synthesis checklist/bridge DECOUPLED into two independent gates (supersedes CL-72's outcome-coupling).
  phase_checklists ⟺ `design_accepted` (execution artifact — only when family commits to build); budget_gap_bridge
  ⟺ `has_budget_gap` (independent). Fixes the hole where rejected-all-with-no-gap would wrongly get a checklist
  (old 2-value `outcome` enum couldn't distinguish accepted-no-gap from rejected-no-gap). Simplified per user to
  the single rule: checklist ONLY if a design was accepted, no other condition. `outcome` demoted to derived
  display label. → schema synthesis (design_accepted + has_budget_gap bools), SI-27, question bank Stage 8.
- CL-74. Critique-pass fixes (verification): (a) Synthesis STAGE CONTRACT still gated checklists on the old
  `outcome` enum — stale vs CL-73; corrected to the two independent gates (design_accepted / has_budget_gap).
  (b) Appendix code-validation list had 2 of 3 — added the SI-31 envelope check. Both were live
  inconsistencies (contract contradicted schema/SI). No new behavior; alignment only.
- CL-76. RESOLVED (critique Gap-2): materials xlsx is a SEPARATE deliverable artifact shipped ALONGSIDE the
  Synthesis PDF — the PDF neither embeds line items NOR references a spreadsheet pointer. Supersedes CL-21.
  Also fixes the budget-gap dangle by construction: gap path bypasses Materials, and since the PDF never
  claims a materials reference, nothing dangles. Line items key to design via room_ref/area (CL-12, intact).
  → SI-27, Synthesis stage contract, question bank Stage 8.
- CL-77. RESOLVED (critique Gap-1): `use_economy_option` is a GUIDED MINI-REVISIT, not a dangling verdict.
  [REFINED by CL-79: the switch REPOINTS to the economy option's RETAINED analysis (b-lite), not
  destroy-and-recompute; economy is analyzed when offered at the Logistics loop, so usually already retained.]
  Transition: null chosen_design → re-copy the economy option from retained options[] (CL-3) as new immutable
  chosen_design → cascade Safety/Logistics/Materials changed_reopened. Needed because only chosen_design (the
  preferred option) was ever classified downstream — the economy option was presented at Design but never
  tier-classified/cost-built, so its Safety/Logistics/Materials data must derive on the switch. Economy option's
  per-room intended_materials rides along in the copied option (no separate capture). Distinct from
  revisit_design (full loop to Design) and proceed_with_budget_gap (jump to Synthesis). ALSO corrected the stale
  "no cross-stage back-dependencies" invariant → "strictly linear forward + two guarded backward edges
  (revisit_design cascade; Materials→Safety single-item re-open)". → SI-17, schema verdict, stage-contracts
  (Global Model invariant + orchestration appendix).
- CL-78. RESOLVED (critique Gap-3 + user refinement): DIY stays a separate conditional stage but (a) `applicable`
  becomes a DERIVED predicate over safety_permit.classifications (non-Tier-1 set non-empty), NOT a stored flag —
  removes the staleness Gap-3 flagged; (b) OPTION 1 chosen for procedure generation: the stage receives the FULL
  classified set, partitions {Tier-1 = sequence-anchor only} vs {non-Tier-1 = procedure targets}, and generates
  procedure ONLY for non-Tier-1 — Tier-1 items woven in as `hold_points` ("wait for the licensed trade here"),
  never how-to. Rationale: passing only non-Tier-1 (option 2) blinds the model to Tier-1 items sitting mid-
  sequence (e.g. tile step depends on pro rough-in), producing a procedure that silently assumes pro work done —
  a real safety gap, not just interpretation. Full-scope visibility + firewalled generation makes the pro↔DIY
  handoff explicit. Schema: procedures[] gains `hold_points`; `applicable` → DERIVED. → SI-26, DIY stage
  contract, question bank Y1 + gate, schema diy_planning.
- CL-79. Design-passes + analysis-retention model consolidated into SI-34 (single source of truth). Decisions:
  (1) 4-pass HARD CAP {preferred, economy, design_3, design_4}; design_3/4 USER-DIRECTED (family steers), not
  system budget-revisions — supersedes CL-13 enum naming. (2) b-lite analysis RETENTION: the four downstream
  sections retained keyed by option_role; switching = REPOINT active analysis (no recompute, no loss);
  revisit_design (new geometry) = DISCARD superseded options' analyses — the clean split. Refines CL-77
  (use_economy = repoint, not cascade-destroy). (3) Each option produced gets FULL S/L/M analysis (compare
  complete pictures), bounded by the cap. (4) revisit_design trigger points = Design stage + Materials ONLY
  (cost final/itemized there). (5) Cap exhaustion → choose-existing or proceed_with_budget_gap (terminating).
  (6) `complete` is TERMINAL — restore is in-progress-only, no reopen (fresh run to change). (7) Budget
  `gap_amount` passed to re-design so it engineers TO target, not blind. → SI-34 (new), SI-4/SI-17/SI-19 edits,
  schema (option_role enum, active_option_role + retained_analysis, gap_amount, cascade repoint/discard note,
  terminal-complete), stage contracts (Design/Materials/appendix), question bank (D5/L5), TS-11.
- CL-75. Stage-contracts alignment pass (A+B): (A) wired RD-1..RD-5 identifiers into every stage's frozen-ref
  line + Global Model block (contracts previously named frozen data descriptively with no stable-ID link —
  drift from the one-artifact-per-concern discipline). (B) updated the restore appendix to the RC
  dependency-chain scope (was older "re-walk all" language, out of sync with SI-4/RC). Alignment only, no new
  behavior; makes stage contracts trace cleanly to the reference assets and restore logic they depend on.
- CL-46. Writeup edit — remove stale standalone-entry sentence (do at end). ALSO: Synthesis prose says the
  budget-gap outcome keeps 'phase checklists' — drifts from SI-27 (gap outcome OMITS phase checklists, adds
  bridge instead). Tighten in the same writeup pass. Schema + question bank correctly follow SI-27.

## Superseded / evolution notes
- CL-34. "No budget until Stage 4" was SUPERSEDED by the progressive budget thread (Scope ballpark → Design
  refined → Materials itemized; judged in Logistics).
- CL-35. "No pricing in Design" SUPERSEDED — Design now carries a coarse refined estimate + budget-engineered alts.
- CL-36. Design→Logistics considered as parallel agents; REJECTED in favor of sequential producer/consumer
  (preserves the linear-cascade invariant; avoids convergence-logic complexity).
- CL-37. Standalone-entry for Contractor Validation was floated then DROPPED (no-shortcuts pipeline; everyone
  walks all stages). Writeup still has one stale sentence to remove (pending).

## Deferred / roadmap
- CL-38. Deferred: session_log, customer-correlation, cryptographic tamper-proofing, second design option,
  recent-renovations-touching-area, suggested→curated promotion (manual), tile pattern-waste nuance.
- CL-39. Deferred optimization: revisit trimming options[] once app is stabilized.
- CL-40. Next iteration: BDD/Gherkin acceptance-criteria layer — convert test scenarios first, then gate
  conditions + safety rules (deterministic spine); keep narrative behaviors as prose. Verify Antigravity's
  actual spec-ingestion format before authoring.
- CL-41. RESOLVED: SubSpace.dimensions stays nullable.
- CL-42. RESOLVED: keep use_economy_option (verdict) and economy (option_role) as-is; they mean different things.

## Pending work before code-engineering
- CL-43. Question bank — all 8 stages COMPLETE — all 8 stages drafted (Scope, Design, Safety, Logistics, Materials, Contractor, DIY, Synthesis). Design (Stage 2)
  includes the material-type fidelity probe (D3) so Safety's frozen Tier-1 matrix (CL-48/SI-30) has the type fidelity.
- CL-44. Reference curation — freeze IRC bathroom rules, per-sqft ballparks+labor, itemized bands+labor,
  IES lighting targets, standard-quote checklist; tune the Scope reality-check threshold. STRUCTURE: one
  artifact per asset, RD-1..RD-5, stable IDs, bathroom-only, national baseline + regional factor.
  STATUS: COMPLETE — RD-1..RD-5 all FROZEN (CL-56/59/60/61/62) + threshold tuned (CL-63). Reference curation
  (CL-44) fully closed. Next pending item: Design (Stage 2) question bank, then orchestration state-machine (CL-45).
  Curation precedes the Design question bank (surfaces gaps → validates the design before we build on it).
- CL-80. RESOLVED (final-review timing question): analysis timing for preferred+economy is EAGER, not lazy.
  Safety/Logistics/Materials analyze BOTH preferred and economy as the pipeline runs (both exist from Design
  D4), populating retained_analysis before the Logistics verdict. Reason: judging "does economy come in under
  ceiling?" is a Logistics-level call needing full cost — lazy (compute-on-switch) couldn't tell the family
  "economy lands at $X under ceiling" at judgment time, defeating the comparison. use_economy switch is then a
  pure repoint (economy always already analyzed). design_3/4 (produced on demand later) analyzed when created.
  Also fixed a stale "1–3 labeled options" line in D4 (→ preferred+economy always, further passes at D5 under
  cap). → SI-34, SI-17, OM table (T4/T6) + OM-6, schema retained_analysis, question bank D4.
- CL-45. Orchestration state-machine — BUILT (reno-compass-orchestration.md, OM-1..12): states, transition
  table (T1-T15), guarded non-linear edges (revisit_design discard, use_economy repoint, Materials→Safety
  single-item, budget-gap jump), conditional DIY predicate, retention/cap (SI-34), restore terminal rule,
  termination argument. Pending expansion: BDD/Gherkin layer (CL-40).
- CL-81. OM gap-audit patch (G1-G3): added the two missing SELF-LOOP transitions the state machine was
  guarding-on but not modeling — T1a Scope budget-recalibration loop (SI-17) and T5a Logistics displacement
  loop (SI-32/CL-47, detailed in new OM-13); added T4a explicit RETURN edge for the Materials→Safety
  single-item envelope re-open (T10 was one-way in the table). OM-1 notes the two bounded self-loops.
  Projection-only (rules already decided in SI-17/SI-32/SI-31); no behavior change. G4 RESOLVED (Option 2): restore stays prose (OM-11) + a pointer row R* in the table so a table-first reader
  can't miss it, without enumerating the RC re-walk as rows. G6 (TS mapping) deferred to BDD pass (CL-40);
  G5 error/refusal rows deferred to BDD (OM-N2).
- CL-82. Pre-Antigravity double-scan: fixed one stale phrase — Synthesis gate (question bank X1) said
  "spreadsheet referenced," contradicting CL-76 (materials xlsx ships SEPARATELY, not referenced in-PDF) →
  corrected. Verified clean: no identifier dupes/gaps/dangling; enums consistent (verdict, option_role,
  SectionStatus, tier canonical = tier_1_professional/tier_2_permitted/tier_3_proceed with bare "Tier N" as
  prose shorthand only); cross-stage field names match; `applicable` derived everywhere (no stored remnant);
  OM guard fields all exist in schema; RD internal IDs unique + all FROZEN + all consumed. SI-8/SI-28 are
  cross-cutting authoring conventions (not orphans). NOTE for Antigravity: map prose "Tier N" → canonical enum.
- CL-83. Antigravity conversion MAP created (reno-compass-antigravity-map.md, AM-1..8) — redistribution table:
  every artifact/section → Rules/Skills/Workflows/constitution home. Validated against primary docs (Codelabs,
  ai.google.dev): constitution = safety spine (SI-9/10/11/12/13/14/24/31 + skill-vs-tool + dossier-sole-channel);
  rules = behavior + schema + sensitive + annotation; skills = 5 reference (RD-1..5) + 9 reasoning, one folder
  each, deterministic tools bundled as scripts/; workflows = pipeline (OM) + 8 stage files + gherkin. Shared
  tools flagged single-source (AM-5): safety-tier-classification (Safety+Contractor), envelope-check,
  geometry/lighting, cost-band lookup. Structured-output UNSUPPORTED → dossier validated by SI-29 scripts not
  provider (AM-6). ~29 Antigravity files from 12 sources. Open: AM-N1..N4 for review. NEXT (gated on review):
  author the .agents files.
- CL-84. AM decisions resolved (AM-N1..N4): SI-24→constitution; geometry+lighting = separate skills, dossier
  carries outputs (only tier-classifier is genuinely shared/re-invoked); 8 stage workflows + pipeline; no
  size-driven references/ splits (RDs all <1500 words), references/ used once for tier-classifier→IRC-matrix
  link. Measured count ≈28 files. Map updated (AM-9/AM-10). Ready to author .agents files on explicit go.
- CL-85. Pre-authoring scan (13 artifacts incl. map): FOUND + FIXED — 12 stage-specific SI notes (15,17,18,20,
  21,22,23,25,26,27,30,32) were not explicitly homed in the map; added AM-4 STAGE-SPECIFIC SI ROUTING so each
  routes to its stage workflow, and added SI-30 to the AM-1 constitution set (it is [SAFETY]-tagged). Re-verified:
  all SI-1..34 mapped; constitution now covers every [SAFETY]/[SECURITY] tag (SI-9/10/11/12/13/14/24/30/31 + SI-5
  dossier-channel); all 5 RDs + 8 stages homed; 17 skills (5 ref + 12 reasoning) trace to stage declarations;
  bundled tools = scripts/ under owning skills; identifiers clean (SI34/CL85/OM13/TS11/AM10, no dupes). Map is
  authoring-ready.
- CL-86. Test scenarios TIGHTENED (user: "TS is very light"). Expanded 11 one-line seeds → 41 structured
  scenarios (Setup→Expect→Governing rule), organized into 8 categories (safety, security, budget, design-
  passes, materials, stages, state/restore, hidden-conditions). Coverage: EVERY behavioral SI note now has ≥1
  scenario (was 7/34; non-behavioral SI-28/29/33 excluded by design); every OM transition/edge covered
  (T1a/T5a/T6/T10/T4a/E1/OM-10/OM-11/R*). Safety scenarios ANCHORED to authentic code (NEC 210.8(A) GFCI, NEC
  210.52(D) 6-ft basin rule — web-verified current) so tests assert against real standards, not just internal
  consistency. Original TS-1..11 IDs preserved (TS-10 elderly kept stable); new TS-12..42; no dup IDs. Filled
  previously-untested critical behaviors: allergy skip≠safe (SI-6), allowance unit-mismatch (SI-16), envelope
  breach reopen (SI-31), Materials divergence (SI-20), restore RC both branches (SI-4), use_economy repoint,
  cap exhaustion, revisit_design discard, terminal-complete, dossier-sole-channel. → test-scenarios artifact.
- CL-87. Antigravity .agents tree AUTHORED (one pass, 37 files) per the conversion map. Structure: 1
  constitution (.specify/memory/, 10 principles = safety spine SI-9/10/11/12/13/14/24/30/31 + skill-vs-tool +
  dossier-channel); 4 rules (.agents/rules/: behavior, sensitive-data, dossier-schema, annotation-convention);
  17 skills (.agents/skills/, one folder each: 5 reference RD-1..5 with YAML frontmatter + inline tables, 12
  reasoning; tier-classifier is single-source shared with a references/ pointer to the irc-safety matrix;
  deterministic tools stubbed as scripts/ READMEs = contracts for Antigravity codegen incl. the SI-29
  code-validations); 9 workflows (.agents/workflows/: pipeline = OM projection + 8 stage files = contract +
  question-bank topics + stage-specific SI routing); 1 Gherkin acceptance layer (.specify/acceptance/, ~25
  deterministic scenarios as Given/When/Then, judgment scenarios deferred to post-impl rubric evals per prior
  decision). Verified: every SKILL.md has name+description frontmatter, name==folder, references target exists,
  matrix logic single-source, no empty files. ~25.5k words. Ready for Antigravity ingestion + codegen.
- CL-88. Cross-reference pass on the authored .agents tree — CLEAN with one fix: all 17 skills present + name==
  folder; every skill referenced by name exists; references/ pointer resolves; all 34 SI notes reflected in the
  tree; constitution carries all 9 safety/security tags + 10 principles; every stage workflow has its SI-routing
  line; reference-skill content matches source RD word counts (no truncation); schema transcribed fully;
  pipeline carries all OM transitions (T1-15 + T1a/T5a/T4a/R*); no orphan/dead skills; no skill folder missing
  SKILL.md. FIX: stage-6 contractor workflow + source stage-contract now explicitly name the shared
  safety-tier-classification skill in Tools/Skills (the re-invocation was stated in coverage-audit skill but not
  surfaced in the stage orchestration — single-source safety link now explicit both places). Re-zipped.
- CL-89. Two additions post-cross-ref: (a) always-active rule constitution-enforcement.md points at
  .specify/memory/constitution.md so the safety spine is enforced even without spec-kit workflows running
  (.agents/ auto-ingests; .specify/ is consumed only when a spec-kit workflow runs — verified vs primary docs).
  (b) Map AM-11 (.specify ingestion behavior) + AM-12 (domain scoping is bathroom-locked BY DESIGN; extension
  rule: never widen a skill description ahead of its frozen reference data — a classifier matched broad but
  running bathroom-only rules is confidently uncovered = safety risk; extend by adding room-scoped reference
  skills with their own frozen matrices). Rules now 5. Re-zipped.
- CL-90. Data-model / persistence artifact created (reno-compass-data-model.md, DM-1..12). Load-bearing
  decisions SETTLED: (DM-1) FastAPI-fronted deployment, persistence in that layer not the .agents runtime;
  (DM-2) FOUR stores with distinct trust — dossier (server checkpoint, trusted), vetted RDs (frozen read-only),
  generalized suggested-items store (SI-23 expanded to all RD categories, append-only, untrusted-until-vetted,
  human-review→merge), accounts (deferred); (DM-4 principle) durability tiers — persisted-trusted vs
  persisted-but-re-derived (safety, SI-4) vs archived (SI-33) vs never-persisted; (DM-5) identity-less session
  = client-held token, sliding 72h + absolute 30d TTL, single-writer; (DM-6) recovery via server checkpoint +
  PROMOTED portable export (first-class, save-nudge at risky moments) as the escape hatch for lost-token/
  different-device; SI-4 re-derivation is the tamper defense on untrusted import. Structured-output constraint
  clarified as a tool-boundary (validate-on-write) concern, independent of persistence. OPEN for next pass:
  DM-3 format, DM-4 field table, DM-7 keys, DM-8 versioning, DM-9 load integrity, DM-10 computed policy, DM-11
  at-rest privacy, DM-12 suggested-store shape. Persistence was the previously-flagged unresolved concern.
- CL-91. Dossier persistence mechanism FINALIZED (DM-3, DM-13); suggested-items store DROPPED for demo.
  Mechanism: GCS bucket (S3-equivalent), object key = session token, JSON, checkpoint every ~2 min + on each
  stage-gate, 30-day absolute expiry via GCS lifecycle rule + sliding-72h via last_active timestamp. Session
  token is the single connecting piece for browser (cookie) + API (resent id). TWO RESTORE PATHS (DM-13):
  trusted GCS checkpoint = SEAMLESS resume, no re-walk, BUT safety silently re-derived on load (SI-4 holds,
  invisible to user on unchanged state); untrusted portable import = existing re-walk + RC + cascade behavior
  (unchanged). One invariant across both: safety is always computed, never loaded — a single rule, not
  trust-branching. complete terminal on both. Firestore noted as the upgrade if/when accounts land. Suggested-
  items store remains a forward-looking enhancement (Firestore collection), not in the demo build.
- CL-92. Persistence decision (CL-90/91) CASCADED across both sets + two-sets-in-sync rule recorded (AM-13).
  The two-restore-paths distinction (DM-13) was previously only in the data-model artifact; now reflected in:
  SI-4 (source) + behavior.md (agy mirror); OM-11 (source orchestration) + pipeline.md (agy mirror). Framing:
  TRUSTED GCS checkpoint = seamless resume, no re-walk, safety silently re-derived; UNTRUSTED portable import =
  re-walk + RC + cascade; `complete` terminal on both; single invariant = safety always computed never loaded.
  STANDING RULE (AM-13): every agreed change lands in BOTH the source .md set and the Antigravity tree in the
  same pass; drift audit after cross-cutting changes. Drift audit this pass: only the persistence decision was
  un-cascaded; complete-terminal + safety-invariant were already consistent in both sets. Note: userPreferences
  are working/interaction guidance — the product-relevant ones (textbook-bold safety, avg+best-case timelines,
  fetch-current-prices, economical alternatives) are already baked into constitution/rules/skills in both sets.
- CL-93. Data-model follow-ups CLOSED (DM-4,7,8,9,10,11) + cascaded to schema in both sets (AM-13 sync).
  Decisions: DM-7 explicit stable ids on classifications/line_items/rooms/options (not positional — survives
  reorder; safety-adjacent since a mis-resolved envelope ref could mispair tier); DM-8 semver, reject-with-
  message on MAJOR mismatch / best-effort on MINOR (no migration machinery for demo); DM-9 broken design/
  materials ref → fall to untrusted re-walk (reuses DM-13 path, no repair logic); DM-10 persist computed VALUES
  + recompute on version mismatch (shares DM-8 check); DM-11 sensitive purged with dossier at TTL, export
  complete + user-informed, redaction deferred with accounts. DM-4 field→tier durability table authored against
  live schema. Schema §4 rewritten to two-path load + §4a persistence/stable-id contract; mirrored into
  agy/.agents/rules/dossier-schema.md (regenerated from source). Only DM-12 (suggested store) remains deferred.
  Persistence layer fully specified.
- CL-94. FINAL pre-handoff scan (5 layers). Layers 1-4 CLEAN: architecture invariants hold (linear + guarded
  backward edges, all 4 verdicts wired, sole-channel, single tier authority); design honors architecture (all
  8 gates require user_final_verdict, eager analysis + retention consistent, 4-pass cap no stale remnants);
  orchestration complete (19 OM rows all full, every state has an exit, complete terminal, SI-29 validations
  have script homes); data model covers all 8 sections + two-restore-paths consistent across 4 places + stable
  ids in both schemas. Layer 5 GAP FOUND + FIXED: the test suite (tightened before persistence was finalized)
  had NO scenarios for the DM decisions — added category I, TS-43..49: trusted-GCS-seamless-resume vs
  untrusted-import-re-walk (DM-13, the highest-risk-to-misimplement behavior), safety-re-derives-both-paths,
  schema-version-mismatch (DM-8), broken-ref→re-walk (DM-9), stable-ids-survive-reorder (DM-7), TTL+export-
  recovery (DM-5/6). Cascaded deterministic ones to the Gherkin acceptance layer (both sets, AM-13 sync). TS
  max now 49; identifiers clean across all series (SI34/CL94/OM13/TS49/DM13/AM13). Spec is handoff-ready.
- CL-95 (closes CL-46). Writeup REFRESHED to match the final design (was substantially stale — described an
  earlier architecture). Corrected: design passes = 4-pass hard cap with user-directed iterations (was "system
  generates alternatives"); added the eager-analysis + repoint/discard retention model (was absent); restore =
  two paths trusted-seamless vs untrusted-re-walk (was single "re-walks"); removed false "nothing stored
  server-side" and added the GCS-checkpoint persistence + recovery section; materials spreadsheet ships
  SEPARATELY not embedded (CL-76); synthesis phase-checklists gated on design_accepted; DIY hold-point model
  for Tier-1 sequencing; guarded backward edges described accurately (revisit/repoint/envelope-reopen/gap) with
  the termination claim; envelope (SI-30/31) and safety-always-re-derived surfaced. Added a full forward-looking
  roadmap per user request: accounts/identity, community-reference-loop (suggested-items store), live local
  pricing, multi-domain expansion (with the extend-data-in-lockstep rule), multi-jurisdiction, vision/to-scale,
  export-privacy/redaction. Textbook-bold safety definitions per user preference (header/beam, NEC 210.8 GFCI).
  Empathetic voice preserved. ~2,990 words. Placeholders retained for demo/repo/video links.
- CL-96. Cross-cutting concerns identified + specified (reno-compass-cross-cutting.md, CC-1..8) — the class the
  stage-organized spec under-covered (logging was never discussed in any session; user flagged it). Set:
  CC-1 logging + SAFETY-DECISION AUDIT TRAIL (first-class, immutable, liability-adjacent) + mandatory log-
  boundary redaction of SENSITIVE fields and quote text; CC-2 unified error taxonomy (user-recoverable/
  retryable/degraded/hard-fail); CC-3 tool-failure & retry policy (compute→hard-fail, generation→surface,
  search→degrade never-guess, safety-validation-fails→block-gate); CC-4 LLM observability/cost; CC-5 rate
  limiting (identity-less = no natural throttle); CC-6 checkpoint atomicity (write-new-then-swap) + idempotency;
  CC-7 config/secrets incl. frozen-reference-data VERSION POINTER; CC-8 time/localization. Priority: P1 (CC-1/2/
  3, shape code) before impl; P2 (CC-5/6/7) deployment; P3 (CC-4/8) defer. Projected P1 into always-active rule
  .agents/rules/cross-cutting-concerns.md (rules now 6); registered AM-14; both sets synced (AM-13). Already-
  covered cross-cutting items (persistence, session/TTL, SI-29 validation boundary, SI-24 injection, SI-4 safety
  re-derive) noted as pre-existing, not repeated.
- CL-97. Post-CC five-layer scan — Layers 1-3 CLEAN (CC consistent with sole-channel, gate discipline, skill/
  tool split, single-writer). Layer 4 GAP FOUND + FIXED: CC-1's safety-decision audit trail is a persisted
  store the data model didn't list — added as DM-2 store #5, and RECONCILED a real retention tension (CC-1 says
  the trail outlives the dossier; DM-11 purges sensitive data at TTL) by constraining the trail to safety data
  ONLY (no allergies/health/accessibility) — carrying no sensitive data is what lets it outlive the purge.
  Stated in both DM-2 and CC-1 (+ agy rule mirror). Layer 5 GAP FOUND + FIXED: behaviorally-observable CC
  concerns lacked scenarios — added category J, TS-50 (audit trail outlives dossier, no sensitive data), TS-51
  (no sensitive/quote-text in logs), TS-52 (safety validation that can't run BLOCKS the gate, never default-
  pass); cascaded to Gherkin. Pure-infra CC concerns (log format, rate limit, checkpoint atomicity, config,
  timezone) correctly NOT scenario-tested (code-review verified). TS max 52; identifiers clean (CC8/DM13/TS52/
  CL97/AM14). Both sets synced.
- CL-98. CC coverage boundary annotated (each CC-1..8 tagged SCENARIO or code-review) — 3 scenario-covered
  (CC-1/2/3 via TS-6/50/51/52), 5 code-review-only (CC-4/5/6/7/8, not agent-observable). Writeup: added ONE
  sentence on the safety-decision audit trail to the Safety & guardrails section (on-theme safety/liability
  feature); other CC items deliberately left out as below the writeup's altitude.
- CL-99. Cross-check (user): labeled schematic generation is owned by the design-generation skill, rendered by
  a deterministic block-diagram generator tool. GAP FOUND + FIXED: the tool was named in the source stage-2
  contract but NOT stubbed in agy design-generation/scripts/ (only geometry.py was) — an implementer reading
  the tree's scripts stub would miss it. Added schematic_generator.py contract (labeled, not-to-scale, SVG=
  roadmap, writes schematic_ref) to scripts/README + named it in the SKILL.md scripts line. Source set already
  consistent (contract named the generator); gap was tree-only. Sets re-synced.
- CL-100. Seven-layer pre-handoff scan (new: L7 skills/tools/rules completeness). L0-L6 CLEAN: identifiers
  (SI34/CL100/OM13/TS52/DM13/AM14/CC8, no dupes/dangling); architecture invariants (verdicts, sole-channel,
  single tier authority, terminal, 10 principles); design (gates, eager/retention, cap, economy-always);
  orchestration (19 rows both sets, SI-29 script homes); data model (5 stores, 8-section durability, audit-trail
  reconciliation in 3 places, two-paths in 4 places, stable-ids both schemas); tests (all behavioral SI + OM
  edges + DM decisions covered; TS-32 confirmed as documented renumber -> RETIRED note added); cross-cutting
  (8/8 coverage-tagged, TS-50..52, Gherkin feature). L7 GAPS FOUND + FIXED — three deterministic tools named in
  stage contracts but NOT stubbed in the tree (same failure mode as CL-99): ballpark_cost.py -> pricing-ballpark
  (RD2-G reality-check, SI-17/T1a guard), budget_feasibility.py -> displacement-alternatives (T5/T5a verdict
  guard), lighting_calc.py -> design-generation (SI-18 per-room, AM-N2 Design-computes). All 13 deterministic
  tools now have exactly 1 home (single-source); census 6 rules / 17 skills / 9 workflows / constitution +
  acceptance. Tree re-zipped; both sets synced.
