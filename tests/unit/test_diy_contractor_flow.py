"""Unit tests for the per-item DIY / all-or-none Contractor decision flow.

Covers the three pieces that make the flow work:
  * base.py — seeding one DIY skeleton per eligible (non-Tier-1) Safety item, the
    one-item-at-a-time active pointer, and the active-item procedure merge.
  * main.py — the deterministic chip → decision mappers.
  * orchestrator.py — the Synthesis split into DIY scope vs contractor additions.
"""

import os

os.environ.setdefault("MOCK_VERTEX_AI", "true")
os.environ.setdefault("STORAGE_LOCAL_FALLBACK", "true")

from agents.diy import DiyAgent
from domain.dossier import (
    ContractorValidationStage,
    DiyPlanningStage,
    DiyProcedure,
    Dossier,
    DossierEnvelope,
    ProjectBody,
    SafetyPermitStage,
    SectionStatus,
    TierClassification,
)
from orchestrator import populate_synthesis


def _tc(item: str, tier: str) -> TierClassification:
    return TierClassification(item=item, tier=tier, source="src", rationale="why")


def _dossier(stage: str, classifications, diy=None, contractor=None) -> Dossier:
    project = ProjectBody(
        safety_permit=SafetyPermitStage(
            status=SectionStatus(state="completed"), classifications=classifications
        ),
        contractor_validation=contractor,
        diy_planning=diy,
    )
    env = DossierEnvelope(dossier_id="diy-test", current_stage=stage)
    return Dossier(envelope=env, project=project)


# --------------------------------------------------------------------------- #
# base.py — seeding + one-item-at-a-time pointer
# --------------------------------------------------------------------------- #


def test_seed_skeletons_covers_non_tier1_only_and_pins_first_active():
    classifications = [
        _tc("Move drain", "tier_2_permitted"),
        _tc("Structural beam", "tier_1_professional"),  # firewalled — never seeded
        _tc("Repaint", "tier_3_proceed"),
    ]
    diy = DiyPlanningStage(status=SectionStatus(state="in_progress"))
    d = _dossier("diy_planning", classifications, diy=diy)
    agent = DiyAgent(d)

    active = agent._seed_diy_skeletons(diy)

    items = {p.item for p in diy.procedures}
    assert items == {"Move drain", "Repaint"}  # Tier-1 excluded
    assert all(p.user_feasible is None for p in diy.procedures)
    # Active item follows Safety order: the Tier-2 drain move comes first.
    assert active == "Move drain"
    assert diy.active_item == "Move drain"
    # Tier carried through for the permit hold-point path.
    assert next(p for p in diy.procedures if p.item == "Move drain").tier == "tier_2_permitted"


def test_seed_skeletons_is_idempotent_and_advances_active_after_decision():
    classifications = [_tc("Move drain", "tier_2_permitted"), _tc("Repaint", "tier_3_proceed")]
    diy = DiyPlanningStage(status=SectionStatus(state="in_progress"))
    d = _dossier("diy_planning", classifications, diy=diy)
    agent = DiyAgent(d)

    agent._seed_diy_skeletons(diy)
    assert len(diy.procedures) == 2
    assert diy.active_item == "Move drain"

    # Decide the first item -> active pointer advances to the next pending one.
    next(p for p in diy.procedures if p.item == "Move drain").user_feasible = True
    active = agent._seed_diy_skeletons(diy)
    assert len(diy.procedures) == 2  # no duplicates
    assert active == "Repaint"

    # Decide the last item -> nothing pending, active clears.
    next(p for p in diy.procedures if p.item == "Repaint").user_feasible = False
    assert agent._seed_diy_skeletons(diy) is None
    assert diy.active_item is None


def test_apply_diy_procedures_fills_active_item_only_and_preserves_decisions():
    classifications = [_tc("Move drain", "tier_2_permitted"), _tc("Repaint", "tier_3_proceed")]
    diy = DiyPlanningStage(status=SectionStatus(state="in_progress"))
    d = _dossier("diy_planning", classifications, diy=diy)
    agent = DiyAgent(d)
    agent._seed_diy_skeletons(diy)  # active = Move drain

    # A prior decision that must never be clobbered by the merge.
    repaint = next(p for p in diy.procedures if p.item == "Repaint")
    repaint.user_feasible = True

    raw = {
        "procedures": [
            {
                "item": "Move drain",
                "tier": "tier_2_permitted",
                "steps": ["Shut off water", "Reroute the P-trap"],
                "hold_points": ["Permit inspection before closing the wall"],
                "tools": [{"tool": "Pipe wrench", "purpose": "Loosen fittings"}],
            },
            # An extra entry for a different item must be ignored (one item per loop).
            {"item": "Repaint", "steps": ["SHOULD NOT LAND"]},
        ]
    }
    agent._apply_diy_procedures(diy, raw)

    drain = next(p for p in diy.procedures if p.item == "Move drain")
    assert drain.steps == ["Shut off water", "Reroute the P-trap"]
    assert drain.hold_points == ["Permit inspection before closing the wall"]
    assert drain.tools and drain.tools[0].tool == "Pipe wrench"
    # The non-active item's authored steps were ignored and its decision preserved.
    assert repaint.steps == []
    assert repaint.user_feasible is True


def test_apply_diy_procedures_matches_reworded_item_name():
    # The extraction LLM often rewords the item name and echoes several procedures from
    # history. The merge must still land on the active item via token overlap.
    classifications = [
        _tc("Relocate the drain line", "tier_2_permitted"),
        _tc("Repaint", "tier_3_proceed"),
    ]
    diy = DiyPlanningStage(status=SectionStatus(state="in_progress"))
    d = _dossier("diy_planning", classifications, diy=diy)
    agent = DiyAgent(d)
    agent._seed_diy_skeletons(diy)  # active = Relocate the drain line

    raw = {
        "procedures": [
            {"item": "Repaint walls", "steps": ["Tape", "Prime", "Paint"]},  # decoy w/ steps
            {
                "item": "Drain line relocation",
                "steps": ["Pull permit", "Reroute P-trap"],
            },  # reworded active
        ]
    }
    agent._apply_diy_procedures(diy, raw)

    drain = next(p for p in diy.procedures if p.item == "Relocate the drain line")
    assert drain.steps == ["Pull permit", "Reroute P-trap"]
    # The decoy did not leak onto the active item.
    assert "Tape" not in drain.steps


# --------------------------------------------------------------------------- #
# main.py — deterministic chip → decision mappers
# --------------------------------------------------------------------------- #


def test_contractor_choice_sets_wants_diy_and_reports_proceed():
    import main

    classifications = [_tc("Repaint", "tier_3_proceed")]
    cv = ContractorValidationStage(status=SectionStatus(state="in_progress"))
    d = _dossier("contractor_validation", classifications, contractor=cv)

    assert main._apply_contractor_diy_choice(d, "Use contractors for everything") is True
    assert cv.wants_diy is False

    cv.wants_diy = None
    assert main._apply_contractor_diy_choice(d, "I'll do the eligible work myself") is True
    assert cv.wants_diy is True

    # A non-decision message leaves it untouched.
    cv.wants_diy = None
    assert main._apply_contractor_diy_choice(d, "What does the quote miss?") is False
    assert cv.wants_diy is None


def test_contractor_choice_ignored_off_stage_and_without_eligible_work():
    import main

    # Off-stage: mapper is a no-op even with a matching phrase.
    cv = ContractorValidationStage(status=SectionStatus(state="in_progress"))
    d = _dossier("materials", [_tc("Repaint", "tier_3_proceed")], contractor=cv)
    assert main._apply_contractor_diy_choice(d, "Use contractors for everything") is False
    assert cv.wants_diy is None

    # On-stage but no eligible (non-Tier-1) work: the choice is moot, no-op.
    cv2 = ContractorValidationStage(status=SectionStatus(state="in_progress"))
    d2 = _dossier(
        "contractor_validation", [_tc("Structural beam", "tier_1_professional")], contractor=cv2
    )
    assert main._apply_contractor_diy_choice(d2, "Use contractors for everything") is False
    assert cv2.wants_diy is None


def test_diy_item_decision_can_cant_refine_target_active_item():
    import main

    classifications = [_tc("Move drain", "tier_2_permitted"), _tc("Repaint", "tier_3_proceed")]
    diy = DiyPlanningStage(
        status=SectionStatus(state="in_progress"),
        procedures=[
            DiyProcedure(item="Move drain", tier="tier_2_permitted"),
            DiyProcedure(item="Repaint", tier="tier_3_proceed"),
        ],
    )
    d = _dossier("diy_planning", classifications, diy=diy)

    # "can't" is checked before "can" so "I can't do this" is never a false can-do.
    assert main._apply_diy_item_decision(d, "I can't — assign this to a professional") == "decided"
    drain = next(p for p in diy.procedures if p.item == "Move drain")
    assert drain.user_feasible is False
    assert drain.reclassify_to_professional is True

    # Next active item is Repaint. A refine bumps the counter without deciding.
    assert main._apply_diy_item_decision(d, "I have a question / want to refine this") == "refine"
    repaint = next(p for p in diy.procedures if p.item == "Repaint")
    assert repaint.refine_count == 1
    assert repaint.user_feasible is None

    # Then a can-do decision on the same (still-active) item.
    assert main._apply_diy_item_decision(d, "I can do this one myself") == "decided"
    assert repaint.user_feasible is True
    assert repaint.reclassify_to_professional is False

    # Everything decided -> no active item -> mapper is a no-op.
    assert main._apply_diy_item_decision(d, "I can do this one myself") is None


def test_typed_question_is_never_read_as_a_decision():
    import main

    classifications = [_tc("Move drain", "tier_2_permitted")]
    diy = DiyPlanningStage(
        status=SectionStatus(state="in_progress"),
        procedures=[DiyProcedure(item="Move drain", tier="tier_2_permitted")],
    )
    d = _dossier("diy_planning", classifications, diy=diy)
    drain = diy.procedures[0]

    # A question that contains "can" / "can't" must be treated as a refine, not a
    # decision — the item stays pending so the agent answers before any commitment.
    assert main._apply_diy_item_decision(d, "Can I do this without pulling a permit?") == "refine"
    assert drain.user_feasible is None
    assert drain.reclassify_to_professional is False
    assert drain.refine_count == 1

    assert main._apply_diy_item_decision(d, "I can't decide — is this hard to do?") == "refine"
    assert drain.user_feasible is None
    assert drain.refine_count == 2


def test_diy_quick_replies_are_two_commitments_plus_input_hint():
    import main

    classifications = [_tc("Move drain", "tier_2_permitted")]
    diy = DiyPlanningStage(status=SectionStatus(state="in_progress"))
    d = _dossier("diy_planning", classifications, diy=diy)
    DiyAgent(d)._seed_diy_skeletons(diy)  # pins an active item

    chips = main._quick_replies_for(d)
    assert chips == ["I can do this one myself", "I can't — assign this to a professional"]
    # No standalone "refine / question" chip — questions are typed.
    assert not any("question" in c.lower() or "refine" in c.lower() for c in chips)
    # The input hint invites free-text questions while an item is under discussion.
    assert main._input_hint_for(d) == main._DIY_ITEM_INPUT_HINT

    # Once every item is decided, the DIY loop reaches its confirm boundary: a single
    # "Yes, proceed" chip plus the type-to-change hint (no "Not yet" chip anymore).
    diy.procedures[0].user_feasible = True
    diy.active_item = None
    assert main._quick_replies_for(d) == ["Yes, proceed"]
    assert main._input_hint_for(d) == main._CONFIRM_INPUT_HINT


# --------------------------------------------------------------------------- #
# orchestrator.py — Synthesis split
# --------------------------------------------------------------------------- #


def test_synthesis_splits_diy_scope_from_contractor_additions():
    classifications = [_tc("Move drain", "tier_2_permitted"), _tc("Repaint", "tier_3_proceed")]
    diy = DiyPlanningStage(
        status=SectionStatus(state="completed"),
        procedures=[
            DiyProcedure(item="Repaint", tier="tier_3_proceed", user_feasible=True),
            DiyProcedure(
                item="Move drain",
                tier="tier_2_permitted",
                user_feasible=False,
                reclassify_to_professional=True,
            ),
        ],
        user_final_verdict=True,
    )
    d = _dossier("synthesis", classifications, diy=diy)

    populate_synthesis(d)
    synthesis = d.project.synthesis
    assert synthesis.diy_scope == ["Repaint"]
    assert synthesis.contractor_scope_additions == ["Move drain"]
