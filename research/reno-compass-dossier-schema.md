# Reno Compass — Dossier Schema (Third Cut)

Tech/API-agnostic data contract. Pseudo-types: `string`,`number`,`int`,`bool`,`timestamp`,`enum[...]`,`list[...]`,`object{...}`.

Field annotations:
- `[computed]`   — deterministic tool output (calculated, never model-guessed)
- `[narrative]`  — model-generated prose / judgment
- `[user]`       — value the user explicitly chose/confirmed
- `[safety]`     — safety-critical; ALWAYS re-derived/re-confirmed on session_restore, never trusted from file
- `[SENSITIVE]`  — personal/health data; handle with care (see SI-6)

Attention convention: short imperative consequence phrases on high-attention fields
(e.g. "SHAPES design", "MUST screen against these") steer the model; `see SI-n` points to the full rule.
Annotations STEER; add code validation only where a miss is harmful.

---

## 1. Envelope
```
Dossier = object {
  envelope: object {
    app_id: string, schema_version: string
    dossier_id: string                             // GENERATE only when absent (fresh); PRESERVE on restore (never recalc)
    created_at: timestamp, last_updated_at: timestamp
    origin: enum[ "fresh", "session_restore" ]     // session_restore = reloaded from uploaded dossier
    current_stage: enum[ "scope","design","safety_permit","logistics_feasibility",
                         "materials","contractor_validation","diy_planning","synthesis","complete" ]
    // diy_planning is CONDITIONAL — present only when DIY-scoped work exists; skipped otherwise (SI-26)
    // On session_restore: current_stage RESET to "scope"; re-walk all stages confirm-or-change (SI-4)
    // EXCEPTION (SI-34): a dossier already at "complete" is TERMINAL — restore does NOT reopen it. Save/restore
    // is a resume-IN-PROGRESS mechanism, not archive-and-reopen; to change a delivered plan, start a fresh run.
  }
  project: ProjectBody
}
```
> session_log / customer-correlation / cryptographic tamper-proofing: roadmap.

---

## 2. Reusable sub-structures

### 2.1 SectionStatus (every stage; drives cascade)
```
SectionStatus = object {
  state: enum[ "not_started","in_progress","completed","changed_reopened" ]
  //  not_started -> in_progress -> completed
  //  completed  -> changed_reopened -> in_progress -> completed
  //  On changed_reopened: ALL downstream sections also -> changed_reopened (propagate); null their timestamps.
  //  NOTE (SI-34): this destroy-and-recompute cascade applies to a genuine CHANGE within a stage or a
  //  revisit_design (new geometry). SWITCHING among already-designed options is NOT this — it REPOINTS the
  //  active analysis to/from design.retained_analysis (no destroy). revisit_design additionally DISCARDS the
  //  superseded options' retained entries. Switch = repoint; change/revisit = invalidate.
  completed_at: timestamp | null            // null when reopened
  confirmed_at: timestamp | null            // when family gave final verdict for THIS stage; null when reopened
  confirmation_revoked: bool                // EXPLICIT: true on reopen — prior verdict no longer holds; re-confirm required
  depends_on:   list[string]                // linear: all prior sections
}
```
> Restore always re-walks from Scope (envelope), so "confirmed_unchanged" / "invalidated_by_upstream"
> are not needed — a section simply stays `completed` and is re-confirmed in passing, or a change flips
> it (and all downstream) to `changed_reopened`. `[safety]` sections re-derive regardless (SI-4).

### 2.2 TierClassification (shared safety spine, PER-ITEM — see SI-9, SI-10, SI-11)
```
TierClassification = object {                 // [safety] one entry PER classified action/item
  item: string
  tier: enum[ "tier_1_professional","tier_2_permitted","tier_3_proceed" ]
  source: string                              // e.g. "IRC §R602" + AHJ-verify note
  rationale: string                           // [narrative]
  depth_consent: bool | null                  // [safety] tier_1 only: consent to depth-not-procedure (SI-9)
  consent_text:  string | null
  envelope: object | null {                    // [safety] bounds this tier was classified WITHIN (SI-30, RD-1).
                                               // Materials code-validates the concrete product against this (SI-31);
                                               // breach re-opens Safety for this one item. null when not material-driven.
    kind: enum[ "electrical","structural","other" ]   // which trigger family this envelope encodes
    max_amperage:   string | null             // electrical: e.g. "≤20A on existing #12 branch, no new circuit"
    // structural is a TUPLE, not a psf number (RD1-F4 / CL-55): a filled-weight band gated by floor type +
    // aggravating conditions. A single point-load figure would be false precision — capacity needs an engineer.
    filled_weight_band: enum[ "under_800","800_1500","over_1500" ] | null   // structural (RD1-F2)
    floor_type: enum[ "slab","framed" ] | null                              // structural gate 1 (RD1-F1)
    aggravating_conditions: list[string] | null   // structural: e.g. ["span_gt_12ft","upper_floor","old_joists"]
    basis: string | null                      // which frozen-matrix threshold fired (RD-1 rule id + source)
  }
  reclassified_from_materials: bool           // [safety] true if this entry was (re)opened by an SI-31 envelope breach
}
```

### 2.3 Dimensions
```
Dimensions = object { length:number, width:number, height:number, unit:string }
```

### 2.4 RoomElement (generic model; type/category inferred — see SI-1)
```
RoomElement = object {
  type: string                                // open, specific: "gfci_outlet","exhaust_fan","vanity_faucet"
  category: enum[ "lighting","plumbing","electrical","hvac",
                  "appliance","surface","storage","fixture","other" ]   // best-fit; "other" last resort (SI-1)
  existing_or_new: enum[ "existing","new" ]   // "new" covers additions AND relocated/changed (new in that state)
  dimensions: Dimensions                       // REQUIRED (non-null) — forces homeowner to think each element through
  placement: string                           // [narrative]
  brand: string | null                        // [user]
  product_description: string | null
  spec_note: string | null                    // capacity/rating (exhaust CFM, outlet amps)
}
```

### 2.5 SubSpace (built-in sub-spaces within a room)
```
SubSpace = object {
  type: string                                // "built_in_closet","crawl_space_access","alcove","linen_nook"
  dimensions: Dimensions | null
  note: string
}
```

### 2.6 AreaPreference (location-scoped preference)
```
AreaPreference = object {
  location: string                            // "shower","vanity","toilet area"
  preference: string                          // "walk-in not tub","rain head","shampoo niche"
  priority: enum[ "must_have","nice_to_have" ]
}
```

### 2.7 LightingRequirements (per-room; Design-stage [computed])
```
LightingRequirements = object {
  natural_light_note: string                  // [user]/[narrative] orientation/exposure
  light_obstructions: string | null           // [user]/[narrative] permanent structures/shades (tree, overhang,
                                               // adjacent building, interior obstruction) affecting natural light
  required_natural_lumens: number             // [computed] (SI-18)
  recommended_window_area: number             // [computed]
  required_artificial_lumens: number          // [computed]
  required_fixture_count: number              // [computed]
}
```

### 2.8 Room
```
Room = object {
  label: string
  dimensions: Dimensions                      // [user] raw + validated
  derived_area: number                        // [computed]
  derived_volume: number                      // [computed]
  hand_orientation: string | null             // [user] room-level; call out primary user + reason; SHAPES layout
  sub_spaces: list[SubSpace]
  area_preferences: list[AreaPreference]       // location-precise wants for this room
  elements: list[RoomElement]                  // existing + new, all categories
  // ---- populated only in a design option's layout (Design stage), null in measured/current rooms: ----
  lighting_requirements: LightingRequirements | null   // PER-ROOM (SI-18); global lighting = aggregate of rooms
  intended_materials: list[object {            // PER-ROOM material TYPE intent (product selection -> Materials)
    surface: string                            // "floor","shower wall","counter"
    material_type: string                      // "porcelain tile","LVP","quartz"
    // ---- CL-48 fidelity fields: populated ONLY for heavy/high-draw items so Stage-3's frozen Tier-1 matrix
    //      (RD-1) can run its structural/electrical envelope. null for ordinary finishes (don't over-ask). ----
    composition: string | null                 // "natural stone" | "engineered/quartz" | "cast iron" | "acrylic" ...
    weight_class: string | null                // slab thickness / est. filled weight → RD1-F structural gate
    amperage_note: string | null               // draw sense for motor/heat items → RD1-A electrical envelope
  }] | null
}
```

### 2.9 ConversationTurn
```
ConversationTurn = object { role: enum["agent","user"], text:string, at:timestamp }
```
> CL-49 / SI-33: on a stage reaching `completed`, its raw `conversation` turns are ARCHIVED to deep storage
> and only a summarized-Markdown string of core design decisions is carried into later prompts (context-cache
> friendly). The summary is a prompt-conditioning aid, NOT a state store. SAFETY CARVE-OUT: safety
> classifications, consent state, and TierClassification.envelope are ALWAYS read from the structured dossier,
> NEVER from the summary. Archival is reversible (full turns retrievable for audit/restore).

---

## 3. Project body

Every stage: `status`, `conversation: list[ConversationTurn]`, final `user_final_verdict: bool` gate.

```
ProjectBody = object {

  // ---- STAGE 1: SCOPE ----
  scope: object {
    status: SectionStatus
    conversation: list[ConversationTurn]
    project_title: string                      // [user] personal name for the project (artifact identity, PDF)
    project_type: string                       // [user] free text; drives reference selection (cost/rules)
    property_context: object {                 // [user]
      home_age: int | null                      // used to weight hidden-condition likelihood (SI-2)
      zipcode: string                           // [user] REQUIRED — drives the regional cost factor (SI-15/CL-9).
                                                // Operationally necessary for pricing; ask plainly with a one-line why.
      dwelling_type: enum[ "independent_house","condo","townhouse","apartment","other" ]
                                                // gates displacement options (yard vs none) + HOA/access/cost (SI-22)
      occupancy: enum[ "owner_occupied","rental","multi_family" ]
      occupant_count: int | null
      occupant_age_range: object {              // [user] powers context-triggered prompting (SI-7); [SENSITIVE] optional
        youngest: int | "skipped" | null         // child-safety triggers; "skipped"=declined, null=not-yet-asked
        eldest:   int | "skipped" | null          // accessibility/slip-resistance triggers; same 3-state semantics
      }                                          // GATE-satisfied when answered OR "skipped" (SI-6; never re-ask a skip)
      has_rental_tenants: bool                  // tenant-occupied work may carry legal notice obligations
      renovation_area: number                   // [user] REQUIRED — the area actually being renovated; drives calcs
      dwelling_area: number | null              // [user] context — total living area (ballpark sanity, disruption)
      lot_area: number | null                   // [user] optional — relevant for storage-unit/exterior decisions (SI-22)
    }
    special_considerations: object {            // [SENSITIVE] optional; handle with care — see SI-6
      // per-field 3-state: list = answered · "skipped" = declined · null = not-yet-asked.
      // GATE-satisfied per field when answered OR "skipped"; agent NEVER re-asks a skipped field (SI-6).
      accessibility_needs: list[string] | "skipped" | null   // grab bars, curbless, turning radius; SHAPES design + dimensions
      health_sensitivities: list[string] | "skipped" | null  // respiratory/VOC/mold; SHAPES materials + logistics
      allergies: list[string] | null             // MUST screen (if answered). NO "skipped" state — a decline is
                                                 // routed through a ONE-TIME confirmation and resolves to an EXPLICIT
                                                 // empty list [] = "confirmed none" (family vouched). [] then screens
                                                 // legitimately as screened=true. null = not-yet-asked/unconfirmed. (SI-6)
      pets: list[string] | "skipped" | null                  // containment + dust/safety during work
    }
    global_preferences: list[string]           // [user] project-wide style/posture
    stated_goal: string                        // [narrative] the why, refined
    must_haves: list[string]                   // [user]
    nice_to_haves: list[string]                // [user]
    budget_target: number                      // [user] hoping-for
    budget_ceiling: number                     // [user] do-not-exceed
    intended_timing: object {                  // [user]
      target_window: string                     // season / target start
      duration_flexibility: string | null
    }
    hidden_conditions: list[object {           // [narrative] weight via home_age (SI-2)
      condition: string, cost_impact_note: string
    }]
    ballpark_estimate: object {                // [computed] per-sq-ft ROM (SI-17); horizon, not verdict
      low: number, high: number, basis_note: string
      contingency: object {                    // [computed] home-age-weighted (SI-2), shown as its OWN line — never
                                               // folded silently into low/high (would make the base look padded/tight)
        low: number, high: number              // dollar band for likely hidden conditions
        pct_of_ballpark: number                // regionally-scaled: 0.10 × regional_factor, clamped ≤0.20
                                               // (RD2-E/CL-57). e.g. 95120 (1.55×)→~0.155. If risk exceeds,
                                               // band clamps but T9 still names conditions (floor-of-awareness)
        capped: bool                           // true when home-age risk would exceed the scaled cap (clamped)
      }
    }
    budget_reality_check: object {             // [computed]+[narrative] ground expectations EARLY (SI-17)
      stated_vs_ballpark: enum[ "plausible","tight","unrealistic" ]   // thresholds tuned in RD2-G:
                                               // tight = within ~15% below ballpark low; unrealistic = >~25% below
                                               // (cheapest band meeting must-haves, incl. scaled contingency)
      note: string                             // kind, honest framing; not a hard stop, a horizon
    }
    budget_reality_resolved: bool              // GATE REQUIRES true (SI-17): true when stated_vs_ballpark != unrealistic
                                               // OR family explicitly accepts the gap. Blocks the "$1000 kitchen" toy case.
    user_final_verdict: bool                   // family's confirmation to advance (reset false on restore/reopen)
  }

  // ---- STAGE 2: DESIGN ----
  design: object {
    status: SectionStatus
    conversation: list[ConversationTurn]
    rooms: list[Room]                          // measured/current state; user dims preserved + derived (audit)
    options: list[object {
      label: string                             // "Design A"
      option_role: enum[ "preferred","economy","design_3","design_4" ]  // 4-pass cap (SI-34); design_3/4 user-directed
      description: string                       // [narrative]
      value_proposition: string                 // [narrative] tied to must/nice-haves + area_preferences
      layout: object { rooms: list[Room] }      // proposed arrangement; EACH room carries its own
                                                // lighting_requirements + intended_materials (per-room, SI-18)
      refined_estimate: object {                 // [computed] ballpark + professional/permit/logistics (SI-17)
        low: number, high: number                // coarse; Materials produces the itemized final
        includes_professional: bool              // reflects Stage-3 professional_required cost
        includes_permit: bool
        over_ceiling: bool                       // [computed] vs scope.budget_ceiling
        gap_amount: number | null                // [computed] magnitude over ceiling (est - ceiling); fed to
                                                 // re-design so the model engineers TO target, not blind (SI-34)
      }
      budget_engineered: bool                    // true if auto-generated to fit budget (SI-17)
      // aggregate lighting/materials across layout.rooms are DERIVED on demand, not stored here.
      schematic_ref: string | null
    }]
    chosen_design: object | null {              // [user] IMMUTABLE full copy of the selected option at confirmation.
                                                // options[] is RETAINED alongside (trim deferred — see change log).
      chosen_label: string                        // which option was chosen
      option_role: enum[ "preferred","economy","design_3","design_4" ]  // role frozen at selection (SI-34)
      layout: object { rooms: list[Room] }        // full spatial detail copied in (incl. per-room lighting + materials)
      refined_estimate: object                    // copied from the chosen option
    }
    user_final_verdict: bool
    active_option_role: enum[ "preferred","economy","design_3","design_4" ]   // which option's analysis is ACTIVE
                                                // now (SI-34). Switching REPOINTS this; the four downstream
                                                // sections below hold the ACTIVE option's analysis. Non-active
                                                // options' analyses are RETAINED (see retained_analysis) — not lost.
    retained_analysis: map<option_role, object {   // [b-lite retention, SI-34] per-option snapshots of the four
                                                // downstream sections, so switching back = repoint, no recompute.
      safety_permit: object                     // snapshot (same shape as top-level safety_permit)
      logistics_feasibility: object
      materials: object
      diy_planning: object | null
    }> | null                                   // EAGER (SI-34): populated for BOTH preferred + economy as the
                                                // pipeline runs S/L/M (both exist from Design), so Logistics can
                                                // judge economy-vs-ceiling. design_3/4 added when produced.
                                                // revisit_design DISCARDS entries for superseded options.
  }

  // NOTE (SI-34): the four sections below (safety_permit … diy_planning) mirror the ACTIVE option's analysis.
  // On switch, the orchestrator swaps the active set from/into design.retained_analysis (repoint, not destroy).
  // Only revisit_design (new geometry) discards retained entries. Reads elsewhere target these active sections.
  safety_permit: object {
    status: SectionStatus
    conversation: list[ConversationTurn]
    classifications: list[TierClassification]   // [safety] (SI-9, SI-10)
    permit_required: bool                        // [computed]
    permit_disclosures: list[object {
      item:string, code_reference:string, ahj_verify_note:string
    }]
    educational_disclosures: list[object {      // [narrative] inform only; do NOT auto-escalate tier (SI-14)
      topic: string                             // "possible lead paint (pre-1978)","possible asbestos"
      trigger: string                           // why raised (home_age + action)
      guidance: string                          // test/abatement consideration; family decides
      source: string | null
    }]
    user_permit_consent: bool
    professional_required: bool                  // [computed] any tier_1
    user_final_verdict: bool
  }

  // ---- STAGE 4: LOGISTICS & FEASIBILITY ----
  logistics_feasibility: object {
    status: SectionStatus
    conversation: list[ConversationTurn]
    disruption: object {
      offline_utilities: list[string]
      offline_duration_estimate: string          // [computed]/[narrative]
      can_live_through_it: bool | null            // [narrative]; consider occupant_count, pets, special_considerations
    }
    displacement_options: list[object {           // [narrative] empathetic alternatives
      option: string                              // what + why + fit, in one narrative; cost_band lets family choose
      cost_band: object{low:number,high:number} | null
    }]
    chosen_displacement: string | null            // [user] if live-through-it is false; its cost feeds verdict
    tenant_obligation_note: string | null         // [narrative] if has_rental_tenants
    weather_timing_note: string | null            // [narrative] implications of intended_timing (no stored forecast)
    // Logistics CONSUMES design.chosen_design.refined_estimate; does NOT recompute the design cost (SI-17).
    total_with_displacement: object { low:number, high:number }   // [computed] refined_estimate + displacement cost
    feasible_within_target:  bool                 // [computed] vs budget_target
    feasible_within_ceiling: bool                 // [computed] vs budget_ceiling
    verdict: enum[ "proceed","use_economy_option","revisit_design","proceed_with_budget_gap" ]   // [computed]+[user] (SI-27)
    // use_economy_option (SI-17): null chosen_design → re-copy economy option from options[] as new immutable
    // chosen_design → cascade Safety/Logistics/Materials changed_reopened (economy was never classified). Guided
    // mini-revisit, NOT a silent swap. revisit_design = full loop to Design; proceed_with_budget_gap = jump to Synthesis.
    user_final_verdict: bool
  }

  // ---- STAGE 5: MATERIALS ---- (product selection)
  materials: object {
    status: SectionStatus
    conversation: list[ConversationTurn]
    finish_recommendation: object {               // [narrative] color/finish vs lighting + prefs
      palette_note:string, rationale:string
    }
    line_items: list[object {
      material:string, category:string, quantity:number, unit:string
      room_ref: string                            // room label this item belongs to (room-specific; enables roll-up)
      area: string | null                         // finer location within room ("shower","floor","vanity") if applicable
      pricing_mode: enum[ "banded","allowance" ]   // explicit; not inferred from null-ness (SI-15, SI-16)
      waste_factor_pct: number                    // [computed] overage included
      cost_band: object{low:number,high:number} | null   // [computed] banded mode; from curated table, NOT live
      unit_cost: number | null                    // [user] allowance mode; else null
      unit_cost_basis: string | null              // [user] allowance; MUST match `unit` (code-validated, SI-16)
      extended_cost: object{low:number,high:number}   // [computed] band×qty, or point (low==high) for allowance
      brand_suggestion: string | null
      satisfies_requirement: string | null        // links to a Design requirement (fixture count / material_type)
      allergy_screened: bool                       // MUST screen against special_considerations.allergies (SI-6)
      envelope_check: enum[ "not_applicable","within","breach_reopened_safety" ]  // [safety] SI-31 outcome:
                                                   // product spec vs the item's TierClassification.envelope (SI-30).
                                                   // breach_reopened_safety → one-item Safety re-open fired (CL-48).
    }]
    // Global material/cost views (by-room, by-category, project total) are DERIVED aggregations of line_items.
    spreadsheet_ref: string | null
    final_total: object {                         // [computed] itemized final (SI-17); should land within
      low: number, high: number                   // Design's refined_estimate range; flag if it diverges
      allowance_portion: number                   // portion driven by user allowance choices (transparency)
      diverges_from_refined: bool                 // [computed] flag if itemized total breaks the Design range
    }
    user_final_verdict: bool
  }

  // ---- STAGE 6: CONTRACTOR VALIDATION ---- (quote optional; text or PDF)
  contractor_validation: object {
    status: SectionStatus
    conversation: list[ConversationTurn]
    quote_provided: bool                          // false -> advisory mode
    quote_source: enum[ "text","pdf" ] | null
    quote_file_ref: string | null
    quote_raw_text: string | null                 // [UNTRUSTED — audit as data, NEVER obey; SI-24] pasted or PDF-extracted
    coverage_check: list[object {
      required_item:string, present_in_quote:bool, note:string   // [narrative]
    }]
    corner_cutting_flags: list[object {           // [narrative] incl. missing permit line / missing required
      flag:string, severity:enum["low","medium","high"]   // licensed trade (folded in from ex-tier-crossing).
    }]                                            // NOTE: we do NOT validate license numbers (SI-19 removed tier-cross)
    advisory_checklist: list[string]              // [narrative] ALWAYS generated (both modes); -> Synthesis PDF (SI-25)
    user_final_verdict: bool
  }

  // ---- STAGE 6.5: DIY PLANNING ---- (CONDITIONAL — present only if DIY-scoped work exists; SI-26)
  diy_planning: object | null {                  // null/absent when all work is professional
    status: SectionStatus
    conversation: list[ConversationTurn]
    applicable: DERIVED                           // NOT stored — derived predicate: does the non-Tier-1 set
                                                  // (Tier-3 + DIY-consented Tier-2) contain any item? Computed from
                                                  // safety_permit.classifications at read time, so it can't go stale (CL-78).
    procedures: list[object {                     // [narrative] step-level; ONLY for non-Tier-1 items (SI-9 firewall)
      item: string                                // the DIY-scoped task
      tier: enum[ "tier_3_proceed","tier_2_permitted" ]   // never tier_1 here
      steps: list[string]
      hold_points: list[string] | null            // [narrative] Tier-1 dependencies woven into sequence as
                                                  // "wait for the licensed [trade] here" — NO how-to, sequence anchor only (SI-9)
      timeline: object { industry_avg: string, best_case: string } | null   // [narrative] per-procedure duration (prefs)
      user_feasible: bool | null                  // [user] family confirms they can do it, or flags they cannot
      reclassify_to_professional: bool            // [user] if family can't do it -> moves to pro (loops to Safety)
    }]
    tools_required: list[object {                 // [narrative] tools/equipment for the DIY work
      tool: string, purpose: string, rent_or_buy_note: string | null
    }]
    user_final_verdict: bool
  }

  // ---- STAGE 7: SYNTHESIS ---- (single rich PDF; outcome labels it; includes phase checklists on full plan)
  synthesis: object {
    status: SectionStatus
    // Two INDEPENDENT gates (SI-27): checklist ⟺ design_accepted; bridge ⟺ has_budget_gap. No coupling.
    design_accepted: bool                         // family committed to a design to execute (gates phase_checklists)
    has_budget_gap: bool                          // gap vs budget_ceiling remains (gates budget_gap_bridge)
    outcome: enum[ "full_plan", "plan_with_budget_gap" ]   // DERIVED display label only (from has_budget_gap); NOT source of truth
    budget_gap_bridge: object | null {          // [narrative] present ⟺ has_budget_gap; at END of PDF, not leading
      gap_amount: number                         // honest gap vs budget_ceiling
      bridge_options: list[string]               // raise budget / phase work / value-engineer / economy option stands
    }
    phase_checklists: object | null {             // [narrative] present ⟺ design_accepted (execution artifact); else null
      before_demolition: list[string]
      after_demolition:  list[string]
      while_reno_in_progress: list[string]
      wrap_up:           list[string]
    }
    pdf_ref: string | null                        // full family-facing PDF; materials xlsx ships SEPARATELY (CL-76)
    generated_at: timestamp | null
  }
}
```

---

## 4. Load / session-restore behavior
TWO PATHS by trust (persistence: data-model DM-13):
- TRUSTED server checkpoint (GCS, server-owned — crash/reconnect/reopen): resume SEAMLESSLY at the point left
  off — NO re-walk, NO confirm-or-change. Steps 4 (safety re-derive) still applies; steps 1-2 (version +
  structural validation) still apply; steps 3/5/6 (RC re-walk) are SKIPPED.
- UNTRUSTED portable import (uploaded/user-held dossier): the full re-walk below.

On an UNTRUSTED `session_restore`:
1. Validate `schema_version` compatibility — SEMVER: MAJOR mismatch → reject with message; MINOR → best-effort
   (DM-8).
2. Structural-validate whole dossier (types, enums, required fields, status consistency). Referential-integrity
   check (DM-9): a broken DESIGN/MATERIALS cross-ref → proceed on this untrusted re-walk (it regenerates refs);
   a broken SAFETY ref self-heals (safety re-derives, step 4).
3. Walk completed sections in dependency order; re-present (stored `conversation`+values) and confirm-or-change:
   - confirm -> stays `completed` (re-confirmed in passing)
   - change  -> `changed_reopened`; null its timestamps; set `confirmation_revoked=true`; mark all downstream
     also -> `changed_reopened` (null their timestamps + set their confirmation_revoked=true too)
4. ALL `[safety]` fields re-derived/re-confirmed regardless, on BOTH paths (SI-4). Material code-validations
   (`envelope_check`, `allergy_screened`) also re-run on load.
5. Reopened/invalidated sections MUST be re-confirmed before their gate reopens (confirmation_revoked).
6. Re-enter at earliest non-confirmed / invalidated section.
7. `diy_planning` is conditional: if a reopened change removes all DIY-scoped work, the stage becomes N/A;
   if it introduces DIY work, the stage activates.

A dossier at `complete` is TERMINAL on BOTH paths — not reopened; a fresh run is required (SI-34).

## 4a. Persistence & identity contract (data-model DM)
- STABLE IDs (DM-7): `classifications[]`, `line_items[]`, `rooms[]`, and `options[]` each carry an explicit
  opaque `id`, stable for the item's lifetime — NOT positional index. Cross-references (envelope re-open T10/
  T4a, `room_ref` rollups, retention by `option_role`) resolve by id, surviving list reorder/removal on revisit.
- `[computed]` values are persisted for fast restore AND recomputed on a schema/reference version mismatch
  (DM-10) — inputs remain in the dossier so recompute is always possible.
- Medium: GCS object keyed by session token, JSON, checkpoint ~2 min + on stage-gate, 30-day TTL (DM-3).
  Sensitive fields purged with the dossier at TTL; portable export is complete, user-informed (DM-11).

---

## 5. Resolved decisions
Moved to `reno-compass-change-log.md` (CL-1…). This file is the data contract only;
design decisions and their history live in the change log.
