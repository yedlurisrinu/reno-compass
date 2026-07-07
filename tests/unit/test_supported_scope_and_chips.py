"""Supported-project-scope boundary and decision-boundary chip behavior.

* The agent may only plan configured project types (today: bathroom); the config
  helper and the injected prompt directive enforce that.
* The "Yes, proceed" chip appears ONLY at a stage's decision boundary (all data
  captured, only the confirmation pending) — never during the opening Q&A — and the
  old "Not yet — I'd like to change something" chip is gone (changes are typed).
"""

import os

os.environ.setdefault("MOCK_VERTEX_AI", "true")
os.environ.setdefault("STORAGE_LOCAL_FALLBACK", "true")

import main
from config.config import is_project_type_supported, settings
from domain.dossier import (
    BallparkContingency,
    BallparkEstimate,
    BudgetRealityCheck,
    Dossier,
    DossierEnvelope,
    ProjectBody,
    PropertyContext,
    ScopeStage,
    SectionStatus,
    SpecialConsiderations,
)


def _scope(**over):
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
            basis_note="basis",
            contingency=BallparkContingency(
                low=3459.6, high=5381.6, pct_of_ballpark=15.5, capped=False
            ),
        ),
        budget_reality_check=BudgetRealityCheck(stated_vs_ballpark="plausible", note="ok"),
        budget_reality_resolved=True,
        user_final_verdict=False,  # not yet confirmed
    )
    for k, v in over.items():
        setattr(s, k, v)
    return s


def _dossier(scope, stage="scope"):
    return Dossier(
        envelope=DossierEnvelope(dossier_id="scope-test", current_stage=stage),
        project=ProjectBody(scope=scope),
    )


# --------------------------------------------------------------------------- #
# Supported project scope
# --------------------------------------------------------------------------- #


def test_config_supports_only_bathroom_by_default():
    assert settings.supported_project_types == ["bathroom"]
    assert is_project_type_supported("bathroom remodel") is True
    assert is_project_type_supported("master bath") is True  # shorthand
    assert is_project_type_supported("") is True  # not yet a violation
    assert is_project_type_supported("kitchen remodel") is False
    assert is_project_type_supported("basement finish") is False


def test_prompt_directive_names_supported_types_and_forbids_switching():
    from agents.base import _supported_scope_directive

    text = _supported_scope_directive()
    assert "bathroom remodels" in text
    assert "kitchen" in text  # explicitly listed as an example to decline
    assert "switch" in text.lower()


# --------------------------------------------------------------------------- #
# Decision-boundary chips
# --------------------------------------------------------------------------- #


def test_no_proceed_chip_during_scope_qna():
    # An incomplete scope (still gathering) offers NO chips and NO hint — the user just
    # answers questions. This is the first-interaction case.
    incomplete = _scope(budget_target=-1.0, stated_goal="TBD")
    d = _dossier(incomplete)
    assert main._quick_replies_for(d) == []
    assert main._input_hint_for(d) is None


def test_proceed_chip_only_at_decision_boundary():
    # A fully-captured scope awaiting only confirmation IS the decision boundary: a
    # single "Yes, proceed" chip plus the type-to-change hint, and no "Not yet" chip.
    d = _dossier(_scope())  # complete, user_final_verdict=False
    chips = main._quick_replies_for(d)
    assert chips == ["Yes, proceed"]
    assert not any("not yet" in c.lower() for c in chips)
    assert main._input_hint_for(d) == main._CONFIRM_INPUT_HINT


def test_unsupported_project_never_reaches_the_boundary():
    # A kitchen scope, however complete, is blocked by the product-scope gate, so the
    # proceed chip never appears.
    d = _dossier(_scope(project_type="kitchen remodel"))
    assert main._quick_replies_for(d) == []
    assert main._input_hint_for(d) is None


# --------------------------------------------------------------------------- #
# Block-warning specificity (the "scope keeps looping" fix)
# --------------------------------------------------------------------------- #


def test_missing_reasons_names_the_real_blocker_not_generic_fields():
    from domain.dossier import SpecialConsiderations

    # Everything given EXCEPT allergies (never resolved) — the classic loop: the user
    # re-sends budget/zip while the true blocker (allergies) goes unnamed.
    scope = _scope(special_considerations=SpecialConsiderations(allergies=None))
    d = _dossier(scope)
    reasons = main._gate_missing_reasons(d, "scope")
    assert len(reasons) == 1
    assert "allerg" in reasons[0].lower()
    # Budget/zip/goal are NOT falsely reported as missing.
    assert not any("budget" in r.lower() or "zip" in r.lower() for r in reasons)


def test_missing_reasons_empty_when_scope_complete():
    # A fully-captured scope has no outstanding requirements (only the verdict remains,
    # which this helper intentionally ignores).
    assert main._gate_missing_reasons(_dossier(_scope()), "scope") == []


# --------------------------------------------------------------------------- #
# No premature confirm chip on a freshly-entered, empty stage (gate-strength fix)
# --------------------------------------------------------------------------- #


def test_no_proceed_chip_on_freshly_entered_materials_stage():
    # The reported bug: entering Materials showed "Yes, proceed" before a single material
    # was chosen. An empty, just-entered Materials stage must offer NO chip and NO hint.
    from domain.dossier import MaterialsStage

    empty_materials = MaterialsStage(status=SectionStatus(state="in_progress"), line_items=[])
    d = Dossier(
        envelope=DossierEnvelope(dossier_id="mat-test", current_stage="materials"),
        project=ProjectBody(scope=_scope(), materials=empty_materials),
    )
    assert main._stage_ready_to_confirm(d, "materials") is False
    assert main._quick_replies_for(d) == []
    assert main._input_hint_for(d) is None
