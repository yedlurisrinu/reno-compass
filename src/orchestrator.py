"""Pipeline orchestrator and Gherkin transition coordinator.

This module implements the Directed Acyclic Graph (DAG) stage transition rules,
guard conditions, backward invalidation cascades (E1..E4), design pass caps,
and restore/re-walk workflows for the Reno Compass application.
"""

from datetime import datetime

from config.config import is_project_type_supported
from domain.dossier import Dossier

# The canonical stage sequence in the DAG
STAGES = [
    "scope",
    "design",
    "safety_permit",
    "logistics_feasibility",
    "materials",
    "contractor_validation",
    "diy_planning",
    "synthesis",
]


def diy_eligible_items(dossier: Dossier) -> list[str]:
    """Returns the distinct Safety items eligible for DIY (all non-Tier-1 work).

    DIY eligibility is the whole non-Tier-1 set — Tier-3 (proceed freely) plus
    Tier-2 (permitted; DIY-able WITH a permit hold-point). The per-item decision
    of whether the family will actually self-perform is made in the DIY-Planning
    loop (``DiyProcedure.user_feasible``), NOT gated by a prior consent flag.
    Tier-1 (professional-only) is firewalled out here — never a DIY procedure.

    Args:
        dossier: The current session dossier.

    Returns:
        list[str]: Ordered, de-duplicated non-Tier-1 item names.
    """
    safety = dossier.project.safety_permit
    if not safety or not safety.classifications:
        return []

    items: list[str] = []
    seen: set[str] = set()
    for c in safety.classifications:
        if c.tier in ("tier_2_permitted", "tier_3_proceed") and c.item not in seen:
            seen.add(c.item)
            items.append(c.item)
    return items


def should_skip_diy_planning(dossier: Dossier) -> bool:
    """Evaluates if the DIY planning stage should be skipped.

    Rules (new per-item flow):
    * Skip if there is no non-Tier-1 (Tier-2/Tier-3) work at all.
    * Skip if the user chose contractors for everything at the Contractor stage
      (``wants_diy is False``) — the all-or-none gate into DIY.

    Args:
        dossier: The current session dossier.

    Returns:
        bool: True if DIY stage should be skipped.
    """
    if not diy_eligible_items(dossier):
        return True

    contractor = dossier.project.contractor_validation
    if contractor and contractor.wants_diy is False:
        return True

    return False


def get_next_stage_key(dossier: Dossier, current_stage: str) -> str | None:
    """Calculates the next stage in the linear DAG, handling conditional skipping.

    Args:
        dossier: The session dossier.
        current_stage: The current active stage key.

    Returns:
        The next stage key or None if we are at synthesis/complete.
    """
    if current_stage == "complete":
        return None

    try:
        idx = STAGES.index(current_stage)
    except ValueError:
        return None

    if current_stage == "synthesis":
        return "complete"

    next_idx = idx + 1
    next_stage = STAGES[next_idx]

    # Rule (OM-5): Conditional skip of DIY Planning
    if next_stage == "diy_planning":
        if should_skip_diy_planning(dossier):
            return "synthesis"

    return next_stage


def reopen_stage_and_cascade(dossier: Dossier, target_stage: str) -> None:
    """Triggers the E1/E2 cascade invalidating all downstream stages in the DAG.

    Args:
        target_stage: The stage to reopen (e.g. 'design').
    """
    if target_stage not in STAGES:
        return

    target_idx = STAGES.index(target_stage)

    # 1. Mark target stage as changed_reopened
    project = dossier.project
    target_obj = getattr(project, target_stage, None)
    if target_obj:
        target_obj.status.state = "changed_reopened"
        target_obj.status.confirmed_at = None
        target_obj.status.confirmation_revoked = True

    # 2. Reset and clear all stages downstream from the target stage
    for idx in range(target_idx + 1, len(STAGES)):
        downstream_stage = STAGES[idx]
        # Skip clearing if the field is not present yet
        if not getattr(project, downstream_stage, None):
            continue

        # Get status to preserve depends_on configuration
        old_obj = getattr(project, downstream_stage)
        deps = old_obj.status.depends_on if old_obj and old_obj.status else []

        # Re-initialize downstream stage payload to empty/not started
        # This prevents stale calculations from polluting the dossier
        from domain.dossier import (
            ContractorValidationStage,
            DiyPlanningStage,
            LogisticsFeasibilityStage,
            MaterialsStage,
            SafetyPermitStage,
            SynthesisStage,
        )

        stages_init = {
            "safety_permit": SafetyPermitStage,
            "logistics_feasibility": LogisticsFeasibilityStage,
            "materials": MaterialsStage,
            "contractor_validation": ContractorValidationStage,
            "diy_planning": DiyPlanningStage,
            "synthesis": SynthesisStage,
        }

        if downstream_stage in stages_init:
            new_stage_instance = stages_init[downstream_stage]()
            new_stage_instance.status.state = "not_started"
            new_stage_instance.status.depends_on = deps
            setattr(project, downstream_stage, new_stage_instance)


def _find_classification_for_material(safety_permit, material_name: str):
    """Finds the Safety classification matching a materials line item (by item name)."""
    if not safety_permit or not material_name:
        return None
    for c in safety_permit.classifications:
        if c.item == material_name or material_name in c.item:
            return c
    return None


def _breach_reconsented(safety_permit, material_name: str) -> bool:
    """True once a breached material's Safety item is reclassified AND re-consented."""
    c = _find_classification_for_material(safety_permit, material_name)
    return bool(c and c.reclassified_from_materials and c.depth_consent is not None)


def reopen_safety_for_material_breach(dossier: Dossier) -> bool:
    """Single-item Safety re-open on a Materials envelope breach (SI-31 / T10 / OM-9 / E3).

    For every materials line item flagged ``breach_reopened_safety``, reopen Safety for
    THAT ONE item — reclassify to professional-install and require fresh re-consent, set
    ``reclassified_from_materials`` — WITHOUT cascading downstream (control stays at
    Materials). Materials never reclassifies; it only detects (Principle 6).

    Args:
        dossier: The session dossier.

    Returns:
        True if any breach still awaits re-consent (the Materials gate must stay closed).
    """
    from domain.dossier import TierClassification

    materials = dossier.project.materials
    safety = dossier.project.safety_permit
    if not materials or not materials.line_items:
        return False

    unresolved = False
    for item in materials.line_items:
        if item.envelope_check != "breach_reopened_safety":
            continue
        if not safety:
            unresolved = True
            continue

        target = _find_classification_for_material(safety, item.material)
        if target is None:
            target = TierClassification(
                item=item.material,
                tier="tier_1_professional",
                source="Materials envelope breach (SI-31): professional review required.",
                rationale=(
                    "Selected product exceeds the stored safety envelope; reclassified "
                    "for professional install."
                ),
                depth_consent=None,
                reclassified_from_materials=True,
            )
            safety.classifications.append(target)
        elif not target.reclassified_from_materials:
            target.reclassified_from_materials = True
            target.tier = "tier_1_professional"
            target.depth_consent = None  # requires fresh re-consent

        # Single-item reopen: flag Safety reopened WITHOUT a downstream cascade.
        safety.status.state = "changed_reopened"
        safety.status.confirmation_revoked = True
        if target.depth_consent is None:
            unresolved = True

    return unresolved


def populate_synthesis(dossier: Dossier) -> None:
    """Derives the terminal Synthesis fields and records the artifact reference.

    Synthesis is a MIRROR (SI-27) — it computes nothing new, only consolidates:
    design acceptance, the budget-gap outcome, phase checklists (iff a design was
    accepted, CL-73), the gap bridge (iff a gap), and pdf_ref/generated_at (H8/H9).
    """
    from domain.dossier import BudgetGapBridge, PhaseChecklists, SynthesisStage

    project = dossier.project
    synthesis = project.synthesis or SynthesisStage()

    design = project.design
    design_accepted = bool(design and design.chosen_design)
    synthesis.design_accepted = design_accepted

    logistics = project.logistics_feasibility
    over_ceiling = bool(
        design and design.chosen_design and design.chosen_design.refined_estimate.over_ceiling
    )
    has_gap = (
        logistics is not None and logistics.verdict == "proceed_with_budget_gap"
    ) or over_ceiling
    synthesis.has_budget_gap = has_gap
    synthesis.outcome = "plan_with_budget_gap" if has_gap else "full_plan"

    if has_gap:
        gap_amount = 0.0
        if design and design.chosen_design and design.chosen_design.refined_estimate.gap_amount:
            gap_amount = design.chosen_design.refined_estimate.gap_amount
        synthesis.budget_gap_bridge = BudgetGapBridge(
            gap_amount=gap_amount,
            bridge_options=[
                "Phase the work over time as budget allows.",
                "Self-perform eligible non-professional items to reduce labor.",
                "Shift finishes toward economy bands without changing the layout.",
            ],
        )
    else:
        synthesis.budget_gap_bridge = None

    # Phase checklists ONLY when a design was accepted (execution artifact, CL-73).
    if design_accepted:
        synthesis.phase_checklists = PhaseChecklists(
            before_demolition=["Order long-lead materials first.", "Confirm permits filed."],
            after_demolition=["Inspect for hidden conditions before closing walls."],
            while_reno_in_progress=[
                "Keep waterproofing before tile.",
                "Hit inspection milestones.",
            ],
            wrap_up=["Final inspection sign-off before final payment."],
        )
    else:
        synthesis.phase_checklists = None

    # Mirror the per-item DIY decisions (SI-27). Items the user confirmed they will
    # self-perform (user_feasible=True) become the DIY scope; items they opted out of
    # (user_feasible=False) are surfaced as additions to the contractor's scope so they
    # are never silently dropped. If DIY was skipped entirely, both lists stay empty.
    diy = project.diy_planning
    diy_scope: list[str] = []
    contractor_additions: list[str] = []
    if diy and diy.procedures:
        for proc in diy.procedures:
            if proc.user_feasible is True:
                diy_scope.append(proc.item)
            elif proc.user_feasible is False:
                contractor_additions.append(proc.item)
    synthesis.diy_scope = diy_scope
    synthesis.contractor_scope_additions = contractor_additions

    # H9: record that the deliverable PDF is available (bytes rendered on download).
    synthesis.pdf_ref = "reno_compass_blueprint.pdf"
    synthesis.generated_at = datetime.utcnow()

    project.synthesis = synthesis


def evaluate_stage_gate(dossier: Dossier, stage: str) -> bool:
    """Validates the mathematical and logic gates of a stage before allowing progress.

    Enforces:
    * Stated budget checks (T1a).
    * Materials envelope checks (T10).
    * Allergy screening checks (SI-6).

    Args:
        dossier: The session dossier.
        stage: The stage to check.

    Returns:
        bool: True if all gate conditions are satisfied.
    """
    project = dossier.project

    if stage == "scope":
        scope = project.scope
        if not scope:
            return False
        # Product-scope boundary: an out-of-scope project type (e.g. a kitchen remodel)
        # can never advance. The agent is instructed to decline it conversationally;
        # this is the deterministic backstop if a non-supported type is captured anyway.
        if not is_project_type_supported(scope.project_type):
            return False
        # T7: both a valid budget target AND ceiling must be provided (not -1.0 sentinel, > 0)
        if scope.budget_target <= 0.0 or scope.budget_target == -1.0:
            return False
        if scope.budget_ceiling <= 0.0 or scope.budget_ceiling == -1.0:
            return False
        # T1/T2: coherent goal and property context captured (not the -1/TBD defaults)
        if not scope.stated_goal or scope.stated_goal.strip().upper() == "TBD":
            return False
        pc = scope.property_context
        if not pc or pc.zipcode in ("", "-1") or pc.renovation_area <= 0.0:
            return False
        # T4 allergies carve-out: must resolve to a list (answered or confirmed []),
        # never rest at null — a null allergy list must not read as screened-safe (SI-6).
        if scope.special_considerations is None or scope.special_considerations.allergies is None:
            return False
        # T10: budget reality-check must be resolved unconditionally (plausible/tight, or a
        # knowing acceptance of an unrealistic budget). SI-17 recalibration loop stays open otherwise.
        if not scope.budget_reality_resolved:
            return False
        return (
            scope.status.state in ("in_progress", "completed", "changed_reopened")
            and scope.user_final_verdict
        )

    elif stage == "design":
        design = project.design
        if not design or not design.chosen_design:
            return False
        # SI-34: hard 4-pass cap {preferred, economy, design_3, design_4}
        if len(design.options) > 4:
            return False
        # M2/D1: measurements (rooms) must be captured — no real design without them
        if not design.rooms:
            return False
        # M1/CL-17: an economy option is ALWAYS required, not only when ambitious
        if not any(o.option_role == "economy" for o in design.options):
            return False
        return (
            design.status.state in ("in_progress", "completed", "changed_reopened")
            and design.user_final_verdict
        )

    elif stage == "safety_permit":
        safety = project.safety_permit
        if not safety:
            return False
        # No classifications yet = Safety has not actually run. An empty list would pass
        # the per-item loop below VACUOUSLY, letting the gate open the instant the stage
        # is entered (before any safety work exists). A real bathroom always has safety
        # items, so an empty set means "not started", not "nothing to check".
        if not safety.classifications:
            return False
        # Principle 2: every classification carries a source and rationale
        for c in safety.classifications:
            if not c.source or not c.rationale:
                return False
            # H3/SI-9: a Tier-1 item needs depth_consent EXPLICITLY set (True or False).
            # False (family declines the depth explanation) is a valid held state; only
            # None (never asked) keeps the gate closed.
            if c.tier == "tier_1_professional" and c.depth_consent is None:
                return False
        # H4/S3: where a permit is required, capture the family's consent to obtain it
        if safety.permit_required and not safety.user_permit_consent:
            return False
        return (
            safety.status.state in ("in_progress", "completed", "changed_reopened")
            and safety.user_final_verdict
        )

    elif stage == "logistics_feasibility":
        logistics = project.logistics_feasibility
        if not logistics:
            return False
        # M5/L2: the live-through-it determination must be made (not left null)
        if logistics.disruption.get("can_live_through_it") is None:
            return False
        # M5/L3: if the family cannot live through the build, a displacement must be chosen
        if (
            logistics.disruption.get("can_live_through_it") is False
            and not logistics.chosen_displacement
        ):
            return False
        return (
            logistics.status.state in ("in_progress", "completed", "changed_reopened")
            and logistics.user_final_verdict
        )

    elif stage == "materials":
        materials = project.materials
        if not materials:
            return False
        # A materials stage that has done its work must have produced at least one priced
        # line item. Without this, an EMPTY line_items list passes the per-item loop below
        # VACUOUSLY, so the gate looks "ready" the instant the stage is entered and the
        # "Yes, proceed" chip appears before a single material is chosen (mirrors the
        # existing contractor/diy guards).
        if not materials.line_items:
            return False

        for item in materials.line_items:
            # SI-6: an unscreened (or skipped/null) allergy state must never pass as safe
            if not item.allergy_screened:
                return False
            # SI-31/T10: an envelope breach blocks until Safety has re-classified AND
            # re-consented that one item (see reopen_safety_for_material_breach).
            if item.envelope_check == "breach_reopened_safety" and not _breach_reconsented(
                project.safety_permit, item.material
            ):
                return False

        return (
            materials.status.state in ("in_progress", "completed", "changed_reopened")
            and materials.user_final_verdict
        )

    elif stage == "contractor_validation":
        contractor = project.contractor_validation
        if not contractor:
            return False
        # H6/SI-25: the advisory checklist is ALWAYS produced, both modes (quote or not)
        if not contractor.advisory_checklist:
            return False
        # H6/Q2: if a quote was provided, it must have been coverage-audited
        if contractor.quote_provided and not contractor.coverage_check:
            return False
        # All-or-none DIY intent must be decided here whenever eligible (non-Tier-1)
        # work exists — it routes the pipeline (wants_diy=False skips DIY → synthesis).
        # If there is no eligible work, DIY is skipped regardless, so the choice is moot.
        if diy_eligible_items(dossier) and contractor.wants_diy is None:
            return False
        return (
            contractor.status.state in ("in_progress", "completed", "changed_reopened")
            and contractor.user_final_verdict
        )

    elif stage == "diy_planning":
        diy = project.diy_planning
        if not diy:
            return False
        # A DIY stage that was NOT skipped must actually produce at least one
        # procedure. Without this, an empty procedures list passes the loop below
        # vacuously and the stage completes with no DIY plan at all.
        if not diy.procedures:
            return False
        # Verify no Tier-1 how-to procedure was generated (Principle 1 firewall).
        for proc in diy.procedures:
            if proc.tier == "tier_1_professional":  # pragma: no cover - schema-forbidden
                return False
        # Per-item completeness: EVERY eligible (non-Tier-1) Safety item must have a
        # procedure whose per-item decision has been made (user_feasible is not None —
        # can-do=True or opted-out=False). A pending (None) item keeps the gate closed.
        eligible = set(diy_eligible_items(dossier))
        decided = {p.item for p in diy.procedures if p.user_feasible is not None}
        if not eligible.issubset(decided):
            return False
        return (
            diy.status.state in ("in_progress", "completed", "changed_reopened")
            and diy.user_final_verdict
        )

    elif stage == "synthesis":
        synthesis = project.synthesis
        if not synthesis:
            return False
        # H9/X1: a PDF must be generated (pdf_ref set) before the terminal transition.
        if not synthesis.pdf_ref:
            return False
        # OM-2/X3: even the terminal transition requires the family's final verdict.
        return (
            synthesis.status.state in ("in_progress", "completed") and synthesis.user_final_verdict
        )

    return False


def advance_pipeline(dossier: Dossier) -> bool:
    """Attempts to advance the current session stage key to the next DAG node.

    Args:
        dossier: The session dossier.

    Returns:
        bool: True if stage advanced successfully.
    """
    current = dossier.envelope.current_stage

    # 1. A completed terminal stage cannot be advanced (SI-34)
    if current == "complete":
        return False

    # 2. SI-31/T10: reopen Safety for any single-item Materials envelope breach before gating.
    if current == "materials":
        reopen_safety_for_material_breach(dossier)

    # 3. Evaluate stage-gate constraints
    if not evaluate_stage_gate(dossier, current):
        return False

    # 3. Mark current stage as confirmed/completed in envelope
    project = dossier.project
    stage_obj = getattr(project, current, None)
    if stage_obj:
        stage_obj.status.state = "completed"
        stage_obj.status.confirmed_at = datetime.utcnow()

    # 4. Advance to next key
    next_stage = get_next_stage_key(dossier, current)
    if next_stage:
        dossier.envelope.current_stage = next_stage

        if next_stage == "synthesis":
            # H8/H9: derive the mirror fields + artifact ref on entry to Synthesis.
            populate_synthesis(dossier)
            project.synthesis.status.state = "in_progress"
        else:
            # Initialize next stage status if not started
            next_obj = getattr(project, next_stage, None)
            if next_obj and next_obj.status.state == "not_started":
                next_obj.status.state = "in_progress"

        return True

    return False


def request_design_revisit(dossier: Dossier) -> bool:
    """Triggers the E1 loop transition to Design stage.

    Decrements remaining design passes under the 4-pass cap (SI-34).

    Args:
        dossier: The current session dossier.

    Returns:
        bool: True if design revisit was successfully registered.
    """
    design = dossier.project.design
    if not design:
        return False

    # Cap calculation: count existing options
    if len(design.options) >= 4:
        # Cap exhausted! Cannot generate more passes (OM-10)
        return False

    # Proceed with E1 invalidation cascade
    reopen_stage_and_cascade(dossier, "design")
    # M3/SI-34: a new-geometry revisit DISCARDS superseded options' retained analyses.
    design.retained_analysis = {}
    dossier.envelope.current_stage = "design"
    return True
