"""Unit tests for the deterministic helper functions in ``main``.

These exercise the pure request-shaping helpers (proceed/affirmation matchers,
per-stage gate-reason explanations, quick-reply chips, input hints, the DIY /
contractor decision mappers, and the state-summary/diff logging) directly,
without spinning up the HTTP layer. Endpoint wiring is covered separately in
``tests/integration/test_endpoint_coverage.py``.
"""

import os

os.environ["STORAGE_LOCAL_FALLBACK"] = "true"
os.environ["MOCK_VERTEX_AI"] = "true"

import pytest

from domain.dossier import (
    DiyPlanningStage,
    DiyProcedure,
    Dossier,
    DossierEnvelope,
    MaterialLineItem,
    ProjectBody,
    PropertyContext,
    SectionStatus,
    TierClassification,
)
from main import (
    _CONFIRM_INPUT_HINT,
    _CONTRACTOR_DIY_NO,
    _CONTRACTOR_DIY_YES,
    _DIY_ITEM_CAN,
    _DIY_ITEM_CANT,
    _DIY_ITEM_INPUT_HINT,
    _apply_contractor_diy_choice,
    _apply_diy_item_decision,
    _gate_missing_reasons,
    _get_agent_for_stage,
    _get_dossier_state_summary,
    _input_hint_for,
    _is_affirmation,
    _is_proceed_intent,
    _log_dossier_state_change,
    _quick_replies_for,
    _stage_ready_to_confirm,
    get_client_safe_state,
)

# Reuse the validated stage builders from the orchestrator gate tests (same
# directory — importable under pytest's default prepend import mode).
from tests.unit.test_orchestrator_gates import (
    make_contractor,
    make_design,
    make_logistics,
    make_materials,
    make_safety,
    make_scope,
)


def _dossier(current_stage, **stages):
    """Builds a dossier at ``current_stage`` with the given stage objects."""
    project = ProjectBody(**stages)
    env = DossierEnvelope(dossier_id="test", current_stage=current_stage)
    return Dossier(envelope=env, project=project)


def _tier2_class(item="Move vanity plumbing"):
    return TierClassification(
        item=item,
        tier="tier_2_permitted",
        source="IRC",
        rationale="Permit required, DIY-able with a hold-point.",
    )


# --------------------------------------------------------------------------- #
# Intent / affirmation matchers
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "msg,expected",
    [
        ("Let's proceed to the next stage", True),
        ("move on please", True),
        ("I'm ready", True),
        ("I have a dog", False),
        ("", False),
        (None, False),
    ],
)
def test_is_proceed_intent(msg, expected):
    assert _is_proceed_intent(msg) is expected


@pytest.mark.parametrize(
    "msg,expected",
    [
        ("yes", True),
        ("Sounds good", True),
        ("looks right", True),
        ("yes, but change the tub", False),
        ("what about tile?", False),
        (None, False),
    ],
)
def test_is_affirmation(msg, expected):
    assert _is_affirmation(msg) is expected


# --------------------------------------------------------------------------- #
# _gate_missing_reasons — one path per stage branch
# --------------------------------------------------------------------------- #


def test_gate_reasons_scope_no_scope_object():
    assert _gate_missing_reasons(_dossier("scope"), "scope") == ["your project details"]


def test_gate_reasons_scope_lists_each_missing_field():
    scope = make_scope(
        budget_target=-1.0,
        budget_ceiling=-1.0,
        stated_goal="TBD",
        budget_reality_resolved=False,
        special_considerations=None,
        property_context=PropertyContext(
            zipcode="-1",
            dwelling_type="independent_house",
            occupancy="owner_occupied",
            renovation_area=-1.0,
        ),
    )
    reasons = _gate_missing_reasons(_dossier("scope", scope=scope), "scope")
    joined = " ".join(reasons)
    assert "target budget" in joined
    assert "budget ceiling" in joined
    assert "main goal" in joined
    assert "zip code" in joined
    assert "square footage" in joined
    assert "allergies" in joined
    assert "reality-check" in joined


def test_gate_reasons_scope_complete_is_empty():
    assert _gate_missing_reasons(_dossier("scope", scope=make_scope()), "scope") == []


def test_gate_reasons_design():
    design = make_design(chosen_design=None, rooms=[])
    reasons = _gate_missing_reasons(_dossier("design", design=design), "design")
    assert any("design option" in r for r in reasons)
    assert any("room measurements" in r for r in reasons)


def test_gate_reasons_safety_tier1_and_permit():
    tier1 = TierClassification(
        item="Move a load-bearing wall",
        tier="tier_1_professional",
        source="IRC",
        rationale="Structural.",
        depth_consent=None,
    )
    safety = make_safety(classifications=[tier1], permit_required=True, user_permit_consent=False)
    reasons = _gate_missing_reasons(
        _dossier("safety_permit", safety_permit=safety), "safety_permit"
    )
    assert any("Tier-1" in r for r in reasons)
    assert any("permit" in r for r in reasons)


def test_gate_reasons_logistics_displacement():
    lg = make_logistics(disruption={"can_live_through_it": False}, chosen_displacement=None)
    reasons = _gate_missing_reasons(
        _dossier("logistics_feasibility", logistics_feasibility=lg), "logistics_feasibility"
    )
    assert any("stay" in r for r in reasons)


def test_gate_reasons_logistics_can_live_unanswered():
    lg = make_logistics(disruption={})
    reasons = _gate_missing_reasons(
        _dossier("logistics_feasibility", logistics_feasibility=lg), "logistics_feasibility"
    )
    assert any("live in the home" in r for r in reasons)


def test_gate_reasons_materials_unscreened():
    item = MaterialLineItem(
        material="Tile",
        category="Surfaces",
        quantity=10.0,
        unit="sqft",
        room_ref="bath",
        pricing_mode="allowance",
        waste_factor_pct=10.0,
        extended_cost={"low": 100.0, "high": 100.0},
        allergy_screened=False,
        envelope_check="within",
    )
    materials = make_materials(items=[item])
    reasons = _gate_missing_reasons(_dossier("materials", materials=materials), "materials")
    assert any("allergy screening" in r for r in reasons)


def test_gate_reasons_contractor_all_branches():
    safety = make_safety(classifications=[_tier2_class()])
    contractor = make_contractor(
        advisory_checklist=[], quote_provided=True, coverage_check=[], wants_diy=None
    )
    d = _dossier("contractor_validation", contractor_validation=contractor, safety_permit=safety)
    reasons = _gate_missing_reasons(d, "contractor_validation")
    joined = " ".join(reasons)
    assert "advisory checklist" in joined
    assert "audit of your contractor quote" in joined
    assert "yourself or use contractors" in joined


def test_gate_reasons_diy_no_procedures_and_undecided():
    safety = make_safety(classifications=[_tier2_class()])

    diy_empty = DiyPlanningStage(status=SectionStatus(state="in_progress"), procedures=[])
    d1 = _dossier("diy_planning", diy_planning=diy_empty, safety_permit=safety)
    assert any("DIY procedures" in r for r in _gate_missing_reasons(d1, "diy_planning"))

    diy_undecided = DiyPlanningStage(
        status=SectionStatus(state="in_progress"),
        procedures=[
            DiyProcedure(item="Move vanity plumbing", tier="tier_2_permitted", user_feasible=None)
        ],
    )
    d2 = _dossier("diy_planning", diy_planning=diy_undecided, safety_permit=safety)
    assert any("decision on each DIY item" in r for r in _gate_missing_reasons(d2, "diy_planning"))


# --------------------------------------------------------------------------- #
# Quick replies + input hints
# --------------------------------------------------------------------------- #


def test_quick_replies_empty_when_complete():
    d = _dossier("complete", scope=make_scope())
    assert _quick_replies_for(d) == []
    assert _input_hint_for(d) is None


def test_quick_replies_confirm_chip_at_scope_boundary():
    d = _dossier("scope", scope=make_scope())
    assert _quick_replies_for(d) == ["Yes, proceed"]
    assert _input_hint_for(d) == _CONFIRM_INPUT_HINT


def test_quick_replies_contractor_diy_choice():
    safety = make_safety(classifications=[_tier2_class()])
    contractor = make_contractor(wants_diy=None)
    d = _dossier("contractor_validation", contractor_validation=contractor, safety_permit=safety)
    assert _quick_replies_for(d) == [_CONTRACTOR_DIY_YES, _CONTRACTOR_DIY_NO]


def test_quick_replies_and_hint_diy_active_item():
    diy = DiyPlanningStage(
        status=SectionStatus(state="in_progress"),
        active_item="Move vanity plumbing",
        procedures=[DiyProcedure(item="Move vanity plumbing", tier="tier_2_permitted")],
    )
    d = _dossier("diy_planning", diy_planning=diy)
    assert _quick_replies_for(d) == [_DIY_ITEM_CAN, _DIY_ITEM_CANT]
    assert _input_hint_for(d) == _DIY_ITEM_INPUT_HINT


# --------------------------------------------------------------------------- #
# DIY / Contractor decision mappers
# --------------------------------------------------------------------------- #


def test_apply_contractor_choice_wrong_stage():
    d = _dossier("scope", scope=make_scope())
    assert _apply_contractor_diy_choice(d, "I'll do it myself") is False


def test_apply_contractor_choice_opt_out_and_in():
    safety = make_safety(classifications=[_tier2_class()])
    contractor = make_contractor(wants_diy=None)
    d = _dossier("contractor_validation", contractor_validation=contractor, safety_permit=safety)
    assert _apply_contractor_diy_choice(d, _CONTRACTOR_DIY_NO) is True
    assert d.project.contractor_validation.wants_diy is False
    assert _apply_contractor_diy_choice(d, _CONTRACTOR_DIY_YES) is True
    assert d.project.contractor_validation.wants_diy is True


def test_apply_diy_item_decision_paths():
    safety = make_safety(classifications=[_tier2_class()])

    def build(msg):
        diy = DiyPlanningStage(
            status=SectionStatus(state="in_progress"),
            procedures=[
                DiyProcedure(
                    item="Move vanity plumbing", tier="tier_2_permitted", user_feasible=None
                )
            ],
        )
        d = _dossier("diy_planning", diy_planning=diy, safety_permit=safety)
        return d, _apply_diy_item_decision(d, msg)

    d, res = build("Can I do this without a permit?")
    assert res == "refine"
    assert d.project.diy_planning.procedures[0].refine_count == 1

    d, res = build(_DIY_ITEM_CANT)
    assert res == "decided"
    assert d.project.diy_planning.procedures[0].user_feasible is False

    d, res = build(_DIY_ITEM_CAN)
    assert res == "decided"
    assert d.project.diy_planning.procedures[0].user_feasible is True


def test_apply_diy_item_decision_wrong_stage():
    d = _dossier("scope", scope=make_scope())
    assert _apply_diy_item_decision(d, _DIY_ITEM_CAN) is None


# --------------------------------------------------------------------------- #
# Ready-to-confirm, state summary/diff, safe state, agent factory
# --------------------------------------------------------------------------- #


def test_stage_ready_to_confirm():
    assert _stage_ready_to_confirm(_dossier("scope", scope=make_scope()), "scope") is True
    incomplete = make_scope(budget_target=-1.0, stated_goal="TBD", budget_reality_resolved=False)
    assert _stage_ready_to_confirm(_dossier("scope", scope=incomplete), "scope") is False
    # Missing stage object -> not ready.
    assert _stage_ready_to_confirm(_dossier("scope", scope=make_scope()), "design") is False


def test_state_summary_none_and_populated():
    assert _get_dossier_state_summary(None) == {}
    summary = _get_dossier_state_summary(_dossier("scope", scope=make_scope()))
    assert summary["current_stage"] == "scope"
    assert summary["stages"]["scope"]["state"] == "in_progress"
    assert summary["stages"]["design"]["state"] == "not_started"


def test_log_state_change_all_branches():
    before = _get_dossier_state_summary(_dossier("scope", scope=make_scope()))
    after = _get_dossier_state_summary(_dossier("design", scope=make_scope()))
    # Initial branch (empty before).
    _log_dossier_state_change("reno_s_x", "init", {}, after)
    # Diff branch (stage changed).
    _log_dossier_state_change("reno_s_x", "advance", before, after)
    # No-change branch.
    _log_dossier_state_change("reno_s_x", "noop", before, before)


def test_get_client_safe_state():
    state = get_client_safe_state(_dossier("scope", scope=make_scope()))
    assert state["current_stage"] == "scope"
    assert isinstance(state["conversation"], list)


def test_get_agent_for_stage_valid_and_invalid():
    d = _dossier("scope", scope=make_scope())
    agent = _get_agent_for_stage("scope", d)
    assert agent.__class__.__name__ == "ScopeAgent"
    with pytest.raises(ValueError):
        _get_agent_for_stage("nonsense_stage", d)
