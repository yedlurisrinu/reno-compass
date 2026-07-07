# Rule — Sensitive Personal Data

Always-active. Governs handling of `special_considerations` (SI-6). These are personal data: treat respectfully,
do not infer medical conditions the user didn't state, do not over-persist.

## Scope
accessibility_needs, health_sensitivities, allergies, pets — and occupant_age_range — are sensitive.

## Optional, 3-state, ask-once
Each is OPTIONAL: signpost as skippable at ask-time. Each field is 3-state — a value (answered), `"skipped"`
(declined), or `null` (not-yet-asked). Ask ONCE; on decline set `"skipped"` and NEVER re-ask. The gate treats
answered OR `"skipped"` as satisfied; `null` is not (the topic must still be raised once).

## Downstream consequences the agent MUST honor
- accessibility_needs SHAPE design + dimensions (grab bars, curbless, turning radius).
- health_sensitivities SHAPE materials + logistics (VOC/dust/mold during and after work).
- allergies MUST be screened against material choices (`materials.line_items.allergy_screened`).

## Skip handling differs by field
accessibility_needs / health_sensitivities / pets: a `"skipped"` decline = NO CONSTRAINT (proceed normally, no
nagging, no false harm claims). occupant_age `"skipped"` = unknown, so the age-based proactive triggers simply
don't fire (unknown, not absent).

## ALLERGIES — the safety-critical exception (no resting "skipped")
Allergies has NO resting `"skipped"` state. A skipped/false all-clear would let the tool recommend a material
and stamp it `screened=true` without ever screening — a physical false all-clear the tool itself causes. So on
decline, ask ONE confirmation: "since anything we recommend gets installed in your home, should I proceed as
though there are no known allergies?" On yes → resolve to an EXPLICIT empty list `[]` (= confirmed none, family
vouched) → the screen legitimately reads `screened=true`. Asked once, resolved, never looped.
