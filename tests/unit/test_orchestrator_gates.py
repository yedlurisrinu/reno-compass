"""Regression tests for tightened stage gates, cascades, and the ballpark calculator.

Covers the HIGH/MEDIUM conformance fixes and maps to the acceptance scenarios
(TS-n) in .specify/acceptance/reno-compass.feature.md. Each gate test builds a
minimal PASSING stage, then breaks one field to assert the gate closes.
"""

import pytest

from domain.dossier import (
    BallparkContingency,
    BallparkEstimate,
    BudgetRealityCheck,
    ChosenDesign,
    ContractorValidationStage,
    CoverageCheckItem,
    DesignOption,
    DesignStage,
    Dimensions,
    DiyPlanningStage,
    DiyProcedure,
    Dossier,
    DossierEnvelope,
    LogisticsFeasibilityStage,
    MaterialLineItem,
    MaterialsStage,
    MaterialTotal,
    ProjectBody,
    PropertyContext,
    RefinedEstimate,
    Room,
    SafetyPermitStage,
    ScopeStage,
    SectionStatus,
    SpecialConsiderations,
    TierClassification,
)
from orchestrator import (
    diy_eligible_items,
    evaluate_stage_gate,
    populate_synthesis,
    reopen_safety_for_material_breach,
    request_design_revisit,
    should_skip_diy_planning,
)
from tools.pricing_ballpark import assess_budget_reality, compute_ballpark, contingency_pct


def _dossier(stage_key, stage_obj, current_stage=None):
    project = ProjectBody(**{stage_key: stage_obj})
    env = DossierEnvelope(dossier_id="test", current_stage=current_stage or stage_key)
    return Dossier(envelope=env, project=project)


# --------------------------------------------------------------------------- #
# Batch 2 — RD-2 ballpark + reality-check calculator (H1, TS-2)
# --------------------------------------------------------------------------- #


def test_ballpark_regional_multiplier_and_contingency_cap():
    bp = compute_ballpark(80, "95120", tier="mid")
    # 80 sqft x $180 low x 1.55 regional factor
    assert bp["low"] == pytest.approx(22320.0)
    assert bp["regional_factor"] == 1.55
    # contingency 10% x 1.55 = 15.5%, under the 20% cap
    assert bp["contingency"]["pct_of_ballpark"] == pytest.approx(15.5)
    assert bp["contingency"]["capped"] is False


def test_contingency_is_clamped_to_twenty_percent():
    # A hypothetical 2.5x region would be 25% before the clamp.
    assert contingency_pct(2.5) == 0.20


def test_national_baseline_has_ten_percent_contingency():
    bp = compute_ballpark(80, None, tier="mid")
    assert bp["regional_factor"] == 1.0
    assert bp["contingency"]["pct_of_ballpark"] == pytest.approx(10.0)


def test_compute_ballpark_rejects_nonpositive_area():
    with pytest.raises(ValueError):
        compute_ballpark(0, "95120")


def test_budget_reality_thresholds():
    bp = compute_ballpark(80, "95120", tier="mid")
    low = bp["reality_basis_low"]  # ~25779.6
    assert assess_budget_reality(low + 1, low)[0] == "plausible"
    assert assess_budget_reality(0.80 * low, low)[0] == "tight"
    assert assess_budget_reality(0.50 * low, low)[0] == "unrealistic"


# --------------------------------------------------------------------------- #
# Factories that build gate-PASSING stages
# --------------------------------------------------------------------------- #


def make_scope(**over):
    s = ScopeStage(
        status=SectionStatus(state="in_progress"),
        project_title="Bath",
        project_type="bathroom",
        property_context=PropertyContext(
            zipcode="95120",
            dwelling_type="independent_house",
            occupancy="owner_occupied",
            renovation_area=80.0,
        ),
        special_considerations=SpecialConsiderations(allergies=[]),
        stated_goal="Refresh the main bathroom",
        budget_target=40000.0,
        budget_ceiling=45000.0,
        ballpark_estimate=BallparkEstimate(
            low=22320.0,
            high=34720.0,
            basis_note="RD-2",
            contingency=BallparkContingency(
                low=3459.6, high=5381.6, pct_of_ballpark=15.5, capped=False
            ),
        ),
        budget_reality_check=BudgetRealityCheck(stated_vs_ballpark="plausible", note="ok"),
        budget_reality_resolved=True,
        user_final_verdict=True,
    )
    for k, v in over.items():
        setattr(s, k, v)
    return s


def _refined(**over):
    base = dict(
        low=19000.0,
        high=22000.0,
        includes_professional=True,
        includes_permit=True,
        over_ceiling=False,
    )
    base.update(over)
    return RefinedEstimate(**base)


def make_design(**over):
    est = _refined()
    d = DesignStage(
        status=SectionStatus(state="in_progress"),
        rooms=[
            Room(
                label="Bath",
                dimensions=Dimensions(length=10.0, width=8.0, height=8.0, unit="ft"),
                derived_area=80.0,
                derived_volume=640.0,
            )
        ],
        options=[
            DesignOption(
                label="P",
                option_role="preferred",
                description="p",
                value_proposition="v",
                layout={},
                refined_estimate=est,
            ),
            DesignOption(
                label="E",
                option_role="economy",
                description="e",
                value_proposition="v",
                layout={},
                refined_estimate=_refined(low=14000.0, high=17000.0),
            ),
        ],
        chosen_design=ChosenDesign(
            chosen_label="P", option_role="preferred", layout={}, refined_estimate=est
        ),
        user_final_verdict=True,
    )
    for k, v in over.items():
        setattr(d, k, v)
    return d


def make_safety(classifications=None, **over):
    s = SafetyPermitStage(
        status=SectionStatus(state="in_progress"),
        classifications=classifications if classifications is not None else [],
        user_final_verdict=True,
    )
    for k, v in over.items():
        setattr(s, k, v)
    return s


def make_logistics(**over):
    lg = LogisticsFeasibilityStage(
        status=SectionStatus(state="in_progress"),
        disruption={
            "offline_utilities": ["water"],
            "offline_duration_estimate": "1-2 wks",
            "can_live_through_it": True,
        },
        feasible_within_target=True,
        feasible_within_ceiling=True,
        verdict="proceed",
        user_final_verdict=True,
    )
    for k, v in over.items():
        setattr(lg, k, v)
    return lg


def make_materials(items=None, **over):
    m = MaterialsStage(
        status=SectionStatus(state="in_progress"),
        line_items=items
        if items is not None
        else [
            MaterialLineItem(
                material="Ceramic Tile",
                category="Surfaces",
                quantity=100.0,
                unit="sqft",
                room_ref="bath",
                pricing_mode="allowance",
                waste_factor_pct=10.0,
                extended_cost={"low": 500.0, "high": 500.0},
                allergy_screened=True,
                envelope_check="within",
            )
        ],
        final_total=MaterialTotal(
            low=500.0, high=500.0, allowance_portion=500.0, diverges_from_refined=False
        ),
        user_final_verdict=True,
    )
    for k, v in over.items():
        setattr(m, k, v)
    return m


def make_contractor(**over):
    c = ContractorValidationStage(
        status=SectionStatus(state="in_progress"),
        advisory_checklist=["Get 3-5 bids"],
        user_final_verdict=True,
    )
    for k, v in over.items():
        setattr(c, k, v)
    return c


# --------------------------------------------------------------------------- #
# H2 — Scope gate
# --------------------------------------------------------------------------- #


def test_scope_gate_passes_when_complete():
    assert evaluate_stage_gate(_dossier("scope", make_scope()), "scope") is True


def test_scope_gate_blocks_unsupported_project_type():
    # Product-scope boundary: a kitchen (or any non-bathroom) project can never advance,
    # even with an otherwise-complete, confirmed scope.
    d = _dossier("scope", make_scope(project_type="kitchen remodel"))
    assert evaluate_stage_gate(d, "scope") is False
    # A supported type (including a "master bath" shorthand) still passes.
    assert evaluate_stage_gate(_dossier("scope", make_scope(project_type="master bath")), "scope")


def test_scope_gate_blocks_missing_budget_ceiling():
    assert evaluate_stage_gate(_dossier("scope", make_scope(budget_ceiling=-1.0)), "scope") is False


def test_scope_gate_blocks_unresolved_budget_reality():
    assert (
        evaluate_stage_gate(_dossier("scope", make_scope(budget_reality_resolved=False)), "scope")
        is False
    )


def test_scope_gate_blocks_null_allergies():
    # TS-24 spirit: a null allergy list must never satisfy the gate (SI-6).
    scope = make_scope(special_considerations=SpecialConsiderations(allergies=None))
    assert evaluate_stage_gate(_dossier("scope", scope), "scope") is False


def test_scope_gate_blocks_placeholder_goal_and_area():
    assert evaluate_stage_gate(_dossier("scope", make_scope(stated_goal="TBD")), "scope") is False
    bad_pc = PropertyContext(
        zipcode="-1", dwelling_type="condo", occupancy="rental", renovation_area=-1.0
    )
    assert (
        evaluate_stage_gate(_dossier("scope", make_scope(property_context=bad_pc)), "scope")
        is False
    )


# --------------------------------------------------------------------------- #
# M1 / M2 — Design gate
# --------------------------------------------------------------------------- #


def test_design_gate_passes_when_complete():
    assert evaluate_stage_gate(_dossier("design", make_design()), "design") is True


def test_design_gate_blocks_without_economy_option():
    # M1/CL-17: economy is always required.
    only_preferred = [make_design().options[0]]
    assert (
        evaluate_stage_gate(_dossier("design", make_design(options=only_preferred)), "design")
        is False
    )


def test_design_gate_blocks_without_measurements():
    assert evaluate_stage_gate(_dossier("design", make_design(rooms=[])), "design") is False


# --------------------------------------------------------------------------- #
# H3 / H4 — Safety gate
# --------------------------------------------------------------------------- #


def _tier1(depth_consent):
    return TierClassification(
        item="new panel circuit",
        tier="tier_1_professional",
        source="NEC 210.11",
        rationale="dedicated circuit",
        depth_consent=depth_consent,
    )


def test_safety_gate_tier1_declined_depth_is_valid():
    # H3: depth_consent=False (family declines the explanation) is a valid held state.
    assert (
        evaluate_stage_gate(
            _dossier("safety_permit", make_safety([_tier1(False)])), "safety_permit"
        )
        is True
    )


def test_safety_gate_tier1_unset_consent_blocks():
    # H3: depth_consent=None (never asked) keeps the gate closed.
    assert (
        evaluate_stage_gate(_dossier("safety_permit", make_safety([_tier1(None)])), "safety_permit")
        is False
    )


def test_safety_gate_blocks_on_empty_classifications():
    # Vacuous-pass guard: with NO classifications the per-item loop runs zero times, so
    # without this guard the gate would open the instant Safety is entered (before any
    # safety work exists). An empty set means "not started", never "nothing to check".
    s = make_safety([])  # user_final_verdict=True by factory default
    assert evaluate_stage_gate(_dossier("safety_permit", s), "safety_permit") is False
    # One valid classification (source + rationale, non-Tier-1) opens the gate.
    s.classifications = [
        TierClassification(
            item="repaint", tier="tier_3_proceed", source="n/a", rationale="cosmetic"
        )
    ]
    assert evaluate_stage_gate(_dossier("safety_permit", s), "safety_permit") is True


def test_safety_gate_requires_permit_consent_when_permit_required():
    # H4: permit required but no consent -> blocked. A valid classification is present so
    # the ONLY variable under test is permit consent (an empty classification set is a
    # separate blocker — see test_safety_gate_blocks_on_empty_classifications).
    valid = TierClassification(
        item="repaint walls", tier="tier_3_proceed", source="n/a", rationale="cosmetic"
    )
    s = make_safety([valid], permit_required=True, user_permit_consent=False)
    assert evaluate_stage_gate(_dossier("safety_permit", s), "safety_permit") is False
    s2 = make_safety([valid], permit_required=True, user_permit_consent=True)
    assert evaluate_stage_gate(_dossier("safety_permit", s2), "safety_permit") is True


# --------------------------------------------------------------------------- #
# H5 — Materials envelope breach -> single-item Safety reopen (TS-25)
# --------------------------------------------------------------------------- #


def _breach_dossier():
    item = MaterialLineItem(
        material="Heavy Slab Counter",
        category="Surfaces",
        quantity=1.0,
        unit="each",
        room_ref="bath",
        pricing_mode="allowance",
        waste_factor_pct=0.0,
        extended_cost={"low": 3000.0, "high": 3000.0},
        allergy_screened=True,
        envelope_check="breach_reopened_safety",
    )
    counter = TierClassification(
        item="Heavy Slab Counter",
        tier="tier_3_proceed",
        source="RD-1",
        rationale="within envelope",
        depth_consent=None,
        reclassified_from_materials=False,
    )
    d = Dossier(
        envelope=DossierEnvelope(dossier_id="t", current_stage="materials"),
        project=ProjectBody(
            materials=make_materials(items=[item]), safety_permit=make_safety([counter])
        ),
    )
    return d, item, counter


def test_materials_gate_blocks_on_empty_line_items():
    # Vacuous-pass guard (the "Yes, proceed at materials entry" bug): with NO line items
    # the per-item loop runs zero times, so without this guard the gate would report
    # "ready" the moment Materials is entered and advance with no material chosen.
    m = make_materials(items=[])  # user_final_verdict=True by factory default
    assert evaluate_stage_gate(_dossier("materials", m), "materials") is False
    # A single screened, within-envelope line item opens the gate at the real boundary.
    assert evaluate_stage_gate(_dossier("materials", make_materials()), "materials") is True


def test_material_breach_reopens_safety_for_one_item():
    d, _, _ = _breach_dossier()
    unresolved = reopen_safety_for_material_breach(d)
    assert unresolved is True
    c = d.project.safety_permit.classifications[0]
    # Materials did NOT reclassify; Safety did, and requires fresh re-consent.
    assert c.reclassified_from_materials is True
    assert c.tier == "tier_1_professional"
    assert c.depth_consent is None
    # Downstream is NOT cascaded — only Safety flipped to changed_reopened.
    assert d.project.safety_permit.status.state == "changed_reopened"


def test_materials_gate_blocked_until_breach_reconsented():
    d, _, _ = _breach_dossier()
    reopen_safety_for_material_breach(d)
    assert evaluate_stage_gate(d, "materials") is False
    # Re-consent the reclassified item -> gate opens.
    d.project.safety_permit.classifications[0].depth_consent = True
    assert evaluate_stage_gate(d, "materials") is True


# --------------------------------------------------------------------------- #
# H6 — Contractor gate
# --------------------------------------------------------------------------- #


def test_contractor_gate_requires_advisory_checklist():
    assert (
        evaluate_stage_gate(
            _dossier("contractor_validation", make_contractor()), "contractor_validation"
        )
        is True
    )
    assert (
        evaluate_stage_gate(
            _dossier("contractor_validation", make_contractor(advisory_checklist=[])),
            "contractor_validation",
        )
        is False
    )


def test_contractor_gate_requires_coverage_when_quote_provided():
    c = make_contractor(quote_provided=True, coverage_check=[])
    assert (
        evaluate_stage_gate(_dossier("contractor_validation", c), "contractor_validation") is False
    )
    c2 = make_contractor(
        quote_provided=True,
        coverage_check=[CoverageCheckItem(required_item="Demo", present_in_quote=True, note="ok")],
    )
    assert (
        evaluate_stage_gate(_dossier("contractor_validation", c2), "contractor_validation") is True
    )


# --------------------------------------------------------------------------- #
# M5 — Logistics gate
# --------------------------------------------------------------------------- #


def test_logistics_gate_requires_live_through_it_determination():
    lg = make_logistics(
        disruption={
            "offline_utilities": [],
            "offline_duration_estimate": "",
            "can_live_through_it": None,
        }
    )
    assert (
        evaluate_stage_gate(_dossier("logistics_feasibility", lg), "logistics_feasibility") is False
    )


def test_logistics_gate_requires_displacement_when_cannot_live_through():
    lg = make_logistics(
        disruption={
            "offline_utilities": ["water"],
            "offline_duration_estimate": "3 wks",
            "can_live_through_it": False,
        },
        chosen_displacement=None,
    )
    assert (
        evaluate_stage_gate(_dossier("logistics_feasibility", lg), "logistics_feasibility") is False
    )
    lg.chosen_displacement = "Stay with family"
    assert (
        evaluate_stage_gate(_dossier("logistics_feasibility", lg), "logistics_feasibility") is True
    )


# --------------------------------------------------------------------------- #
# M4 — DIY-skip predicate (TS-8)
# --------------------------------------------------------------------------- #


def _skip_dossier(classifications):
    return _dossier("safety_permit", make_safety(classifications))


def test_diy_skipped_when_all_professional():
    d = _skip_dossier([_tier1(True)])
    assert should_skip_diy_planning(d) is True


def test_diy_not_skipped_with_tier3():
    c = TierClassification(
        item="repaint", tier="tier_3_proceed", source="n/a", rationale="cosmetic"
    )
    assert should_skip_diy_planning(_skip_dossier([c])) is False


def test_diy_tier2_eligible_regardless_of_legacy_self_perform_consent():
    # New per-item flow: Tier-2 (permitted work) is DIY-eligible on its own — the
    # decision to self-perform is made per-item inside the DIY loop, NOT gated by the
    # legacy diy_self_perform_consent flag (which was never populated in practice).
    t2 = TierClassification(
        item="vanity move",
        tier="tier_2_permitted",
        source="IRC",
        rationale="drain relocation",
        diy_self_perform_consent=False,
    )
    d = _dossier("safety_permit", make_safety([t2], permit_required=True, user_permit_consent=True))
    assert should_skip_diy_planning(d) is False
    assert diy_eligible_items(d) == ["vanity move"]


def test_diy_skipped_when_user_wants_contractors_for_everything():
    # All-or-none: even with eligible Tier-2/Tier-3 work, wants_diy=False skips DIY.
    t2 = TierClassification(
        item="vanity move", tier="tier_2_permitted", source="IRC", rationale="drain relocation"
    )
    d = _skip_dossier([t2])
    d.project.contractor_validation = ContractorValidationStage(
        status=SectionStatus(state="in_progress"), wants_diy=False
    )
    assert should_skip_diy_planning(d) is True
    d.project.contractor_validation.wants_diy = True
    assert should_skip_diy_planning(d) is False


def test_diy_gate_requires_at_least_one_procedure():
    """A non-skipped DIY stage cannot complete with an empty procedures list."""
    empty = DiyPlanningStage(
        status=SectionStatus(state="in_progress"),
        procedures=[],
        user_final_verdict=True,
    )
    assert evaluate_stage_gate(_dossier("diy_planning", empty), "diy_planning") is False

    # With a real Tier-3 procedure the gate opens.
    empty.procedures = [
        DiyProcedure(
            item="wall painting",
            tier="tier_3_proceed",
            steps=["Tape edges", "Prime", "Paint"],
            hold_points=[],
        )
    ]
    assert evaluate_stage_gate(_dossier("diy_planning", empty), "diy_planning") is True


# --------------------------------------------------------------------------- #
# M3 — Design revisit discards retained analysis
# --------------------------------------------------------------------------- #


def test_design_revisit_discards_retained_analysis():
    design = make_design(retained_analysis={"preferred": {"stale": "analysis"}})
    d = _dossier("design", design, current_stage="materials")
    assert request_design_revisit(d) is True
    assert d.project.design.retained_analysis == {}
    assert d.envelope.current_stage == "design"


# --------------------------------------------------------------------------- #
# H8 / H9 — Synthesis derivation + terminal gate (TS-29)
# --------------------------------------------------------------------------- #


def _synth_dossier(design_accepted=True, gap=False):
    design = make_design()
    if not design_accepted:
        design.chosen_design = None
    logistics = make_logistics(verdict="proceed_with_budget_gap" if gap else "proceed")
    project = ProjectBody(design=design, logistics_feasibility=logistics)
    return Dossier(
        envelope=DossierEnvelope(dossier_id="t", current_stage="synthesis"), project=project
    )


def test_synthesis_accepted_no_gap():
    # TS-29 row 1: accepted + no gap -> checklist present, bridge absent.
    d = _synth_dossier(design_accepted=True, gap=False)
    populate_synthesis(d)
    s = d.project.synthesis
    assert s.design_accepted is True
    assert s.has_budget_gap is False
    assert s.outcome == "full_plan"
    assert s.phase_checklists is not None
    assert s.budget_gap_bridge is None
    assert s.pdf_ref and s.generated_at is not None


def test_synthesis_accepted_with_gap():
    # TS-29 row 2: accepted + gap -> checklist present, bridge present.
    d = _synth_dossier(design_accepted=True, gap=True)
    populate_synthesis(d)
    s = d.project.synthesis
    assert s.has_budget_gap is True
    assert s.outcome == "plan_with_budget_gap"
    assert s.phase_checklists is not None
    assert s.budget_gap_bridge is not None


def test_synthesis_rejected_no_checklist():
    # TS-29 row 3: rejected + no gap -> checklist absent, bridge absent.
    d = _synth_dossier(design_accepted=False, gap=False)
    populate_synthesis(d)
    s = d.project.synthesis
    assert s.design_accepted is False
    assert s.phase_checklists is None
    assert s.budget_gap_bridge is None


def test_synthesis_gate_requires_pdf_and_final_verdict():
    d = _synth_dossier(design_accepted=True, gap=False)
    populate_synthesis(d)
    s = d.project.synthesis
    s.status.state = "in_progress"
    # pdf_ref set by populate, but no final verdict yet -> blocked
    assert evaluate_stage_gate(d, "synthesis") is False
    s.user_final_verdict = True
    assert evaluate_stage_gate(d, "synthesis") is True
    # Missing PDF -> blocked even with a verdict
    s.pdf_ref = None
    assert evaluate_stage_gate(d, "synthesis") is False
