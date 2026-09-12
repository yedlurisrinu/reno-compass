"""Unit tests for BaseAgent prompt composition, credentials mock, and retry logic."""

import os
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from agents.base import (
    AgentCard,
    BaseAgent,
    _is_trivial_ack,
    _merge_extracted,
    _normalize_agent_text,
    _scrub_internal_refs,
    _tolerant_extract,
)
from domain.dossier import (
    BallparkContingency,
    BallparkEstimate,
    BudgetRealityCheck,
    Dossier,
    DossierEnvelope,
    ProjectBody,
    PropertyContext,
    ScopeStage,
    SpecialConsiderations,
)


class TestMockAgent(BaseAgent):
    """Temporary concrete agent subclass for testing BaseAgent methods."""

    card = AgentCard(
        name="Test Agent",
        stage_key="scope",
        description="Used for testing base behavior.",
        reads=["project.scope.project_title", "project.scope.budget_ceiling"],
        writes=["project.scope"],
        associated_skills=["scope-decomposition"],
        associated_references=["RD-2"],
        search_grounding_enabled=False,
    )


@pytest.fixture
def test_dossier() -> Dossier:
    """Helper mock dossier."""
    return Dossier(
        envelope=DossierEnvelope(
            dossier_id="reno_s_base_test",
            schema_version="1.0.0",
            created_at=datetime.now(UTC),
            last_updated_at=datetime.now(UTC),
            origin="fresh",
            current_stage="scope",
        ),
        project=ProjectBody(
            scope=ScopeStage(
                project_title="Luxurious Bath",
                project_type="bathroom",
                property_context=PropertyContext(
                    zipcode="95120",
                    dwelling_type="independent_house",
                    occupancy="owner_occupied",
                    renovation_area=80.0,
                ),
                special_considerations=SpecialConsiderations(allergies=[]),
                stated_goal="Redo tiles",
                budget_target=20000.0,
                budget_ceiling=30000.0,
                ballpark_estimate=BallparkEstimate(
                    low=18000.0,
                    high=24000.0,
                    basis_note="Ballpark basis",
                    contingency=BallparkContingency(
                        low=1800.0, high=2400.0, pct_of_ballpark=10.0, capped=False
                    ),
                ),
                budget_reality_check=BudgetRealityCheck(stated_vs_ballpark="plausible", note="OK"),
                budget_reality_resolved=True,
                user_final_verdict=True,
            )
        ),
    )


def test_dossier_context_filtering(test_dossier):
    """Verifies that reads contract strictly filters dossier details (Principle 8)."""
    agent = TestMockAgent(test_dossier)
    filtered = agent.get_dossier_context()

    # We authorized "project.scope.project_title" and "project.scope.budget_ceiling"
    assert "project" in filtered
    assert "scope" in filtered["project"]
    assert filtered["project"]["scope"]["project_title"] == "Luxurious Bath"
    assert filtered["project"]["scope"]["budget_ceiling"] == 30000.0

    # Assert unauthorized fields are omitted
    assert "budget_target" not in filtered["project"]["scope"]
    assert "envelope" not in filtered


@patch("agents.base.BaseAgent._read_file_safe")
def test_system_prompt_composition(mock_read, test_dossier):
    """Verifies dynamic prompt hydration combines rules, skills, and reference files."""
    agent = TestMockAgent(test_dossier)

    # Setup mocks for loaded files
    mock_read.side_effect = lambda path: f"Content of {os.path.basename(path)}"

    instructions = agent.compose_system_instructions()

    # Assert that rules and references are contained
    assert "Content of constitution.md" in instructions
    assert "Content of behavior.md" in instructions
    assert "Content of SKILL.md" in instructions  # skill loaded
    assert "### Reference Table: RD-2" in instructions  # RD-2 loaded

    # The agent's OWN stage workflow playbook is loaded (stage_key='scope' -> stage-1).
    assert "Content of stage-1-scope.md" in instructions
    # ...and NO other stage's workflow leaks in (keeps the agent in its lane).
    assert "stage-5-materials.md" not in instructions
    assert "stage-3-safety.md" not in instructions

    # Check persona injection
    assert "Name: Test Agent" in instructions
    assert "Stage Gate: SCOPE" in instructions


@patch("agents.base._build_genai_client")
def test_execute_vertex_call_retry_logic(mock_build_client, test_dossier, monkeypatch):
    """Verifies that the GenAI client retries 3 times on model error before failing."""
    monkeypatch.setenv("MOCK_VERTEX_AI", "false")
    monkeypatch.setattr("agents.base.time.sleep", lambda *a, **k: None)

    # Emulate the unified GenAI client failing with an exception on every call
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("Vertex Overloaded")
    mock_build_client.return_value = mock_client

    agent = TestMockAgent(test_dossier)

    with pytest.raises(Exception) as excinfo:
        agent.execute_vertex_call("System Instructions", "User message")

    assert "Vertex Overloaded" in str(excinfo.value)
    # generate_content should have been called 3 times due to retry loop
    assert mock_client.models.generate_content.call_count == 3


# --- Performance fixes A + B + C ---------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "hi",
        "Hello",
        " hey ",
        "thanks",
        "Thank you",
        "ty",
        "cheers",
        "",
        "   ",
    ],
)
def test_is_trivial_ack_true(text):
    """Only pure greetings/thanks skip extraction."""
    assert _is_trivial_ack(text) is True


@pytest.mark.parametrize(
    "text",
    [
        # Confirmations must NOT skip — they can coincide with a stage transition,
        # and extraction must run to capture the stage's deliverable.
        "ok",
        "yes",
        "proceed",
        "sounds good",
        "looks good",
        "perfect",
        # Parameter-bearing content.
        "ok, budget is 40000",
        "yes and my ceiling is 45000",
        "I have no allergies",
        "10 ft by 8 ft",
    ],
)
def test_is_trivial_ack_false(text):
    """Confirmations and any content beyond a bare greeting must NOT be skipped."""
    assert _is_trivial_ack(text) is False


@patch("agents.base.BaseAgent._run_live_extraction")
@patch("agents.base.BaseAgent._run_mock_extraction")
def test_extraction_skipped_on_greeting_turn(mock_mock_ex, mock_live_ex, test_dossier):
    """A trailing bare greeting short-circuits the extraction round-trip entirely."""
    from datetime import UTC, datetime

    from domain.dossier import ConversationTurn

    agent = TestMockAgent(test_dossier)
    scope = test_dossier.project.scope
    scope.conversation = [
        ConversationTurn(role="user", text="Budget is 40000, zip 95120.", at=datetime.now(UTC)),
        ConversationTurn(role="agent", text="Got it, here is the ballpark.", at=datetime.now(UTC)),
        ConversationTurn(role="user", text="thanks", at=datetime.now(UTC)),
    ]

    agent.extract_and_update_stage_dossier()

    mock_live_ex.assert_not_called()
    mock_mock_ex.assert_not_called()


@patch("agents.base.BaseAgent._run_mock_extraction")
def test_extraction_runs_on_confirmation_turn(mock_mock_ex, test_dossier, monkeypatch):
    """A confirmation like 'proceed' must still run extraction (capture deliverables)."""
    from datetime import UTC, datetime

    from domain.dossier import ConversationTurn

    monkeypatch.setenv("MOCK_VERTEX_AI", "true")
    agent = TestMockAgent(test_dossier)
    scope = test_dossier.project.scope
    scope.conversation = [
        ConversationTurn(role="user", text="Budget is 40000.", at=datetime.now(UTC)),
        ConversationTurn(role="agent", text="Ballpark ready.", at=datetime.now(UTC)),
        ConversationTurn(role="user", text="proceed", at=datetime.now(UTC)),
    ]

    agent.extract_and_update_stage_dossier()

    mock_mock_ex.assert_called_once()


@patch("agents.base.BaseAgent._run_mock_extraction")
def test_extraction_runs_on_substantive_turn(mock_mock_ex, test_dossier, monkeypatch):
    """C: a parameter-bearing latest turn still triggers extraction."""
    from datetime import UTC, datetime

    from domain.dossier import ConversationTurn

    monkeypatch.setenv("MOCK_VERTEX_AI", "true")
    agent = TestMockAgent(test_dossier)
    scope = test_dossier.project.scope
    scope.conversation = [
        ConversationTurn(role="user", text="Budget is 40000, zip 95120.", at=datetime.now(UTC)),
    ]

    agent.extract_and_update_stage_dossier()

    mock_mock_ex.assert_called_once()


@patch("agents.base._build_genai_client")
def test_execute_vertex_call_disables_thinking_and_forces_json(
    mock_build_client, test_dossier, monkeypatch
):
    """A + B: extraction-style call sets thinking_budget=0 and JSON mime type."""
    monkeypatch.setenv("MOCK_VERTEX_AI", "false")
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(text="{}")
    mock_build_client.return_value = mock_client

    agent = TestMockAgent(test_dossier)
    agent.execute_vertex_call(
        "sys", "user", use_grounding=False, disable_thinking=True, json_output=True
    )

    config = mock_client.models.generate_content.call_args.kwargs["config"]
    assert config.thinking_config is not None
    assert config.thinking_config.thinking_budget == 0
    assert config.response_mime_type == "application/json"


@patch("agents.base._build_genai_client")
def test_execute_vertex_call_defaults_keep_thinking(mock_build_client, test_dossier, monkeypatch):
    """Visible chat calls are untouched: no forced thinking budget, no JSON mime type."""
    monkeypatch.setenv("MOCK_VERTEX_AI", "false")
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(text="hello")
    mock_build_client.return_value = mock_client

    agent = TestMockAgent(test_dossier)
    agent.execute_vertex_call("sys", "user")

    config = mock_client.models.generate_content.call_args.kwargs["config"]
    assert config.thinking_config is None
    assert config.response_mime_type is None


# --- Agent text normalization (literal \n escape sequences) ------------------


def test_normalize_converts_literal_escape_sequences():
    """Literal backslash-n emitted by the model must become real line breaks."""
    # As actually observed: a real break followed by a LITERAL '\n\n'.
    raw = "What's your goal?\n\n\\n\\nWhat type of home?\\nAnd the zip code?"
    out = _normalize_agent_text(raw)
    assert "\\n" not in out  # no visible backslash-n remains
    assert "What type of home?" in out
    assert "And the zip code?" in out
    # runs of blank lines collapse to a single paragraph break
    assert "\n\n\n" not in out


def test_normalize_preserves_plain_text_and_real_newlines():
    out = _normalize_agent_text("Line one.\n\nLine two.")
    assert out == "Line one.\n\nLine two."


def test_normalize_handles_empty():
    assert _normalize_agent_text("") == ""


# --- Internal reference-code scrub (no leaking of RD5-*/SI-*/CL-* etc.) -------


@pytest.mark.parametrize(
    "raw",
    [
        "Project timeline with milestones (RD5-A9).",
        "The next items to confirm are RD5-A9, RD5-D for your project.",
        "verify the invisible inclusions (RD5-A4/A7) explicitly",
        "insist on an itemized bid covering [RD5-A list]; get bids",
        "This aligns with Principle 7 and SI-24 for safety.",
        "warranty terms present/absent (RD5-A11) — labor AND materials",
        "A quote missing waterproofing (CL-20) is a HIGH flag.",
        "Timeline context per RD5-D1 and RD-2 bands.",
    ],
)
def test_scrub_removes_all_internal_codes(raw):
    """No internal reference/governance code may survive into customer text."""
    out = _scrub_internal_refs(raw)
    for token in ["RD5-", "RD-2", "RD1-", "RD2-", "SI-", "CL-", "TS-", "Principle ", "APPROVE_"]:
        assert token not in out, f"leaked {token!r} in: {out!r}"


def test_scrub_preserves_ordinary_text():
    text = "Get 3-5 itemized bids and hold final payment until inspections pass."
    assert _scrub_internal_refs(text) == text


# --- Logistics disruption extraction (gate-critical dict merge) ---------------


def _logistics_dossier():
    from datetime import UTC, datetime

    from domain.dossier import (
        ConversationTurn,
        DossierEnvelope,
        LogisticsFeasibilityStage,
        ProjectBody,
        SectionStatus,
    )

    logi = LogisticsFeasibilityStage(
        status=SectionStatus(state="in_progress"),
        conversation=[
            ConversationTurn(
                role="user",
                text="We have a second bathroom so we can live through the remodel.",
                at=datetime.now(UTC),
            )
        ],
    )
    return Dossier(
        envelope=DossierEnvelope(dossier_id="reno_s_logi", current_stage="logistics_feasibility"),
        project=ProjectBody(logistics_feasibility=logi),
    )


def test_extraction_sets_can_live_through_it_from_scratch(monkeypatch):
    """The LLM mapping 'we can live through it' -> disruption.can_live_through_it=True lands."""
    from agents.logistics import LogisticsAgent

    monkeypatch.setenv("MOCK_VERTEX_AI", "false")
    dossier = _logistics_dossier()
    agent = LogisticsAgent(dossier)
    stage = dossier.project.logistics_feasibility

    with patch.object(
        agent,
        "execute_vertex_call",
        return_value='{"disruption": {"can_live_through_it": true}}',
    ):
        agent._run_live_extraction("logistics_feasibility", stage, "conv", "user")

    assert stage.disruption["can_live_through_it"] is True


def test_extraction_omitting_disruption_preserves_prior_value(monkeypatch):
    """A later extraction that omits `disruption` must NOT wipe a resolved key to null."""
    from agents.logistics import LogisticsAgent

    monkeypatch.setenv("MOCK_VERTEX_AI", "false")
    dossier = _logistics_dossier()
    agent = LogisticsAgent(dossier)
    stage = dossier.project.logistics_feasibility
    # Prior turn already resolved it.
    stage.disruption["can_live_through_it"] = True

    # LLM returns valid JSON that simply doesn't mention disruption at all.
    with patch.object(
        agent, "execute_vertex_call", return_value='{"feasible_within_target": true}'
    ):
        agent._run_live_extraction("logistics_feasibility", stage, "conv", "user")

    assert stage.disruption["can_live_through_it"] is True  # preserved, not reset to None
    assert stage.feasible_within_target is True  # a genuinely extracted field still lands
    assert stage.user_final_verdict is False  # verdict is never set by extraction


# --- Extraction robustness (conversation echo + no live mock fabrication) -----


def _safety_dossier():
    from datetime import UTC, datetime

    from domain.dossier import (
        ConversationTurn,
        DossierEnvelope,
        ProjectBody,
        SafetyPermitStage,
        SectionStatus,
    )

    saf = SafetyPermitStage(
        status=SectionStatus(state="in_progress"),
        classifications=[],
        conversation=[
            ConversationTurn(role="user", text="I'll paint myself.", at=datetime.now(UTC))
        ],
    )
    return Dossier(
        envelope=DossierEnvelope(dossier_id="reno_s_saf", current_stage="safety_permit"),
        project=ProjectBody(safety_permit=saf),
    )


def test_extraction_survives_echoed_conversation_with_null_timestamps(monkeypatch):
    """The LLM echoing `conversation` with null `at` must NOT sink extraction."""
    from agents.safety import SafetyAgent

    monkeypatch.setenv("MOCK_VERTEX_AI", "false")
    dossier = _safety_dossier()
    agent = SafetyAgent(dossier)
    stage = dossier.project.safety_permit

    # Model returns valid data BUT also echoes the conversation with null timestamps.
    payload = (
        '{"conversation": [{"role": "user", "text": "I\'ll paint myself.", "at": null}], '
        '"classifications": [{"item": "wall painting", "tier": "tier_3_proceed", '
        '"source": "General practice", "rationale": "cosmetic"}]}'
    )
    mock_ex = MagicMock()
    with (
        patch.object(agent, "execute_vertex_call", return_value=payload),
        patch.object(agent, "_run_mock_extraction", mock_ex),
    ):
        agent._run_live_extraction("safety_permit", stage, "conv", "user")

    mock_ex.assert_not_called()  # no fabrication
    assert len(stage.classifications) == 1
    assert stage.classifications[0].tier == "tier_3_proceed"


def test_extraction_never_sets_user_final_verdict(monkeypatch):
    """Extraction must NOT infer user_final_verdict — only the tag path may set it.

    Prevents premature stage advancement (e.g. opening DIY) when the user merely
    mentions or agrees to something without an explicit transition confirmation.
    """
    from agents.safety import SafetyAgent

    monkeypatch.setenv("MOCK_VERTEX_AI", "false")
    dossier = _safety_dossier()
    agent = SafetyAgent(dossier)
    stage = dossier.project.safety_permit
    assert stage.user_final_verdict is False

    # Model wrongly reports a verdict AND real classifications.
    payload = (
        '{"user_final_verdict": true, "classifications": [{"item": "paint", '
        '"tier": "tier_3_proceed", "source": "practice", "rationale": "cosmetic"}]}'
    )
    with patch.object(agent, "execute_vertex_call", return_value=payload):
        agent._run_live_extraction("safety_permit", stage, "conv", "user")

    assert stage.user_final_verdict is False  # NOT set by extraction
    assert len(stage.classifications) == 1  # other fields still extracted


def test_live_extraction_failure_does_not_fabricate_mock(monkeypatch):
    """A live extraction failure preserves state — it must NOT inject mock data."""
    from agents.safety import SafetyAgent

    monkeypatch.setenv("MOCK_VERTEX_AI", "false")
    dossier = _safety_dossier()
    agent = SafetyAgent(dossier)
    stage = dossier.project.safety_permit

    real_mock = agent._run_mock_extraction  # if wrongly called it would inject a mock item
    with (
        patch.object(agent, "execute_vertex_call", return_value="not valid json {{{"),
        patch.object(agent, "_run_mock_extraction", side_effect=real_mock) as spy,
    ):
        agent._run_live_extraction("safety_permit", stage, "conv", "user")

    spy.assert_not_called()
    assert stage.classifications == []  # preserved empty, no "Mock electrical wiring"


# --- List preservation + deterministic design choice binding -----------------


def _design_dossier():
    from datetime import UTC, datetime

    from domain.dossier import (
        ConversationTurn,
        DesignOption,
        DesignStage,
        Dimensions,
        DossierEnvelope,
        ProjectBody,
        RefinedEstimate,
        Room,
        SectionStatus,
    )

    rooms = [
        Room(
            label="Bathroom",
            dimensions=Dimensions(length=10, width=8, height=8, unit="ft"),
            derived_area=80,
            derived_volume=640,
        )
    ]
    est = RefinedEstimate(
        low=25000, high=30000, includes_professional=True, includes_permit=True, over_ceiling=False
    )
    eco = RefinedEstimate(
        low=18000, high=21000, includes_professional=True, includes_permit=True, over_ceiling=False
    )
    design = DesignStage(
        status=SectionStatus(state="in_progress"),
        rooms=rooms,
        options=[
            DesignOption(
                label="Preferred",
                option_role="preferred",
                description="Premium",
                value_proposition="High-end",
                layout={"bathroom": rooms},
                refined_estimate=est,
            ),
            DesignOption(
                label="Economy",
                option_role="economy",
                description="Cost",
                value_proposition="Value",
                layout={"bathroom": rooms},
                refined_estimate=eco,
            ),
        ],
        conversation=[
            ConversationTurn(role="user", text="Go with Preferred.", at=datetime.now(UTC))
        ],
    )
    return Dossier(
        envelope=DossierEnvelope(dossier_id="reno_s_dz", current_stage="design"),
        project=ProjectBody(design=design),
    )


def test_extraction_omitting_lists_preserves_them(monkeypatch):
    """A turn that omits options/rooms must NOT wipe the captured design."""
    from agents.design import DesignAgent

    monkeypatch.setenv("MOCK_VERTEX_AI", "false")
    dossier = _design_dossier()
    agent = DesignAgent(dossier)
    stage = dossier.project.design

    # Model echoes only the selection; options/rooms absent from the JSON.
    with patch.object(agent, "execute_vertex_call", return_value='{"user_final_verdict": true}'):
        agent._run_live_extraction("design", stage, "conv", "user")

    assert len(stage.options) == 2  # not wiped to []
    assert len(stage.rooms) == 1


def test_design_choice_binds_to_real_option(monkeypatch):
    """A chosen_design signal is reconciled to the authoritative option data."""
    from agents.design import DesignAgent

    monkeypatch.setenv("MOCK_VERTEX_AI", "false")
    dossier = _design_dossier()
    agent = DesignAgent(dossier)
    stage = dossier.project.design

    # Model signals the choice by role but mislabels it and omits nested data.
    payload = (
        '{"user_final_verdict": true, "chosen_design": {"chosen_label": '
        '"Preferred premium option", "option_role": "preferred", "layout": {}, '
        '"refined_estimate": {"low": 1, "high": 2, "includes_professional": true, '
        '"includes_permit": true, "over_ceiling": false}}}'
    )
    with patch.object(agent, "execute_vertex_call", return_value=payload):
        agent._run_live_extraction("design", stage, "conv", "user")

    # Rebound to the REAL option: correct label + authoritative estimate (25000).
    assert stage.chosen_design.chosen_label == "Preferred"
    assert stage.chosen_design.option_role == "preferred"
    assert stage.chosen_design.refined_estimate.low == 25000


# --- Deterministic materials allergy screen (Principle 9 / SI-6) --------------


def _materials_dossier(allergies, materials):
    from domain.dossier import (
        BallparkContingency,
        BallparkEstimate,
        BudgetRealityCheck,
        DossierEnvelope,
        MaterialLineItem,
        MaterialsStage,
        MaterialTotal,
        ProjectBody,
        PropertyContext,
        ScopeStage,
        SectionStatus,
        SpecialConsiderations,
    )

    scope = ScopeStage(
        status=SectionStatus(state="completed"),
        project_title="x",
        project_type="bathroom",
        property_context=PropertyContext(
            zipcode="95120",
            dwelling_type="independent_house",
            occupancy="owner_occupied",
            renovation_area=80,
        ),
        special_considerations=SpecialConsiderations(allergies=allergies),
        stated_goal="redo",
        budget_target=40000,
        budget_ceiling=45000,
        ballpark_estimate=BallparkEstimate(
            low=1,
            high=2,
            basis_note="b",
            contingency=BallparkContingency(low=1, high=2, pct_of_ballpark=10, capped=False),
        ),
        budget_reality_check=BudgetRealityCheck(stated_vs_ballpark="plausible", note="ok"),
    )
    items = [
        MaterialLineItem(
            material=m,
            category="finish",
            quantity=1,
            unit="ea",
            room_ref="bath",
            pricing_mode="allowance",
            waste_factor_pct=10,
            extended_cost={"low": 1, "high": 2},
        )
        for m in materials
    ]
    mats = MaterialsStage(
        status=SectionStatus(state="in_progress"),
        line_items=items,
        final_total=MaterialTotal(low=1, high=2, allowance_portion=0, diverges_from_refined=False),
    )
    return Dossier(
        envelope=DossierEnvelope(dossier_id="m", current_stage="materials"),
        project=ProjectBody(scope=scope, materials=mats),
    )


def test_materials_screen_clears_when_no_allergies():
    """Confirmed-empty allergy profile deterministically clears every line item."""
    from agents.materials import MaterialsAgent

    dossier = _materials_dossier([], ["Porcelain Tile", "Quartz Top"])
    mats = dossier.project.materials
    MaterialsAgent(dossier)._apply_materials_allergy_screen(mats)
    assert all(i.allergy_screened for i in mats.line_items)


def test_materials_screen_flags_named_allergen_conflict():
    """A named allergen appearing in a product's descriptors is NOT cleared."""
    from agents.materials import MaterialsAgent

    dossier = _materials_dossier(["latex"], ["Latex Paint", "Quartz Countertop"])
    mats = dossier.project.materials
    MaterialsAgent(dossier)._apply_materials_allergy_screen(mats)
    by_name = {i.material: i.allergy_screened for i in mats.line_items}
    assert by_name["Latex Paint"] is False
    assert by_name["Quartz Countertop"] is True


def test_materials_screen_untouched_when_allergies_unresolved():
    """Never resolved (None) -> stays unscreened so the SI-6 gate keeps blocking."""
    from agents.materials import MaterialsAgent

    dossier = _materials_dossier(None, ["Tile"])
    mats = dossier.project.materials
    MaterialsAgent(dossier)._apply_materials_allergy_screen(mats)
    assert mats.line_items[0].allergy_screened is False


# --- Tolerant per-field extraction (the "loses info on a loop" bug) ------------


# A realistic scope extraction where ONE nested sub-field is un-coercible: the LLM
# rendered "2 adults in 40s" as occupant_age_range.adults="40s" (an int field). It also
# omits the schema-required ballpark_estimate/budget_reality_check (computed downstream).
_POISON_SCOPE_PAYLOAD = {
    "project_title": "Bathroom Remodel",
    "project_type": "bathroom",
    "property_context": {
        "zipcode": "95120",
        "dwelling_type": "independent_house",
        "occupancy": "owner_occupied",
        "renovation_area": 50.0,
        "home_age": 55,
        "occupant_age_range": {"adults": "40s", "children": 2},
    },
    "special_considerations": {"allergies": []},
    "stated_goal": "Better access for the vanity",
    "budget_target": 35000.0,
    "budget_ceiling": 45000.0,
}


def test_whole_stage_validate_would_sink_on_the_poison_field():
    """Documents WHY tolerant extraction is needed: the old all-or-nothing path fails."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ScopeStage.model_validate(_POISON_SCOPE_PAYLOAD)


def test_tolerant_extract_keeps_good_fields_drops_only_the_bad_leaf():
    """_tolerant_extract keeps every parseable field and drops ONLY the offending leaf."""
    clean = _tolerant_extract(ScopeStage, _POISON_SCOPE_PAYLOAD)

    # Gate-critical scalars survive.
    assert clean["budget_target"] == 35000.0
    assert clean["budget_ceiling"] == 45000.0
    assert clean["stated_goal"] == "Better access for the vanity"
    # Nested property_context survives, pruned per key: zip/area kept, adults="40s" dropped
    # while the valid children:2 is retained.
    pc = clean["property_context"]
    assert pc["zipcode"] == "95120"
    assert pc["renovation_area"] == 50.0
    assert pc["occupant_age_range"] == {"children": 2}
    assert "adults" not in pc["occupant_age_range"]


def test_tolerant_extract_skips_null_and_absent_fields():
    """Null (not-yet-answered) and absent fields are omitted, never coerced to defaults."""
    clean = _tolerant_extract(
        ScopeStage,
        {"budget_target": 20000.0, "stated_goal": None, "property_context": {"zipcode": None}},
    )
    assert clean["budget_target"] == 20000.0
    assert "stated_goal" not in clean  # explicit null -> caller keeps existing
    # A nested dict whose only key is null yields no surviving sub-fields -> omitted.
    assert "property_context" not in clean


def test_live_extraction_survives_poison_field_and_populates_scope(monkeypatch):
    """End-to-end: a "40s" age no longer discards the whole turn — budget/zip/goal land."""
    import json

    from agents.scope import ScopeAgent

    monkeypatch.setenv("MOCK_VERTEX_AI", "false")

    # A fresh scope in its sentinel-default state, exactly as mid-conversation.
    from datetime import UTC, datetime

    from domain.dossier import ConversationTurn, SectionStatus

    scope = ScopeStage(
        status=SectionStatus(state="in_progress"),
        project_title="New Renovation",
        project_type="bathroom",
        property_context=PropertyContext(
            zipcode="-1",
            dwelling_type="independent_house",
            occupancy="owner_occupied",
            renovation_area=-1.0,
        ),
        special_considerations=SpecialConsiderations(allergies=[]),
        stated_goal="TBD",
        budget_target=-1.0,
        budget_ceiling=-1.0,
        ballpark_estimate=BallparkEstimate(
            low=-1.0,
            high=-1.0,
            basis_note="Initial Ballpark",
            contingency=BallparkContingency(
                low=-1.0, high=-1.0, pct_of_ballpark=-1.0, capped=False
            ),
        ),
        budget_reality_check=BudgetRealityCheck(stated_vs_ballpark="plausible", note="init"),
        conversation=[
            ConversationTurn(role="user", text="35K to 45K, 95120, 10x5", at=datetime.now(UTC))
        ],
    )
    dossier = Dossier(
        envelope=DossierEnvelope(dossier_id="reno_s_scope", current_stage="scope"),
        project=ProjectBody(scope=scope),
    )
    agent = ScopeAgent(dossier)

    with patch.object(agent, "execute_vertex_call", return_value=json.dumps(_POISON_SCOPE_PAYLOAD)):
        agent._run_live_extraction("scope", scope, "conv", "user")

    # The whole turn was NOT discarded — the captured data landed on the dossier.
    assert scope.budget_target == 35000.0
    assert scope.budget_ceiling == 45000.0
    assert scope.stated_goal == "Better access for the vanity"
    assert scope.property_context.zipcode == "95120"
    assert scope.property_context.renovation_area == 50.0
    # The deterministic reality pass could then run (needs a positive budget + area).
    assert scope.ballpark_estimate.low > 0
    assert scope.budget_reality_resolved is True


def test_merge_partial_nested_submodel_does_not_corrupt_dossier():
    """A partial nested sub-model (e.g. contingency missing low/high) must NOT overwrite a
    complete one with an unvalidated dict — that corrupts the checkpoint so it fails to
    reload (the observed 404). Deep-merge + re-validate preserves the required sub-fields.
    """
    from domain.dossier import SectionStatus

    scope = ScopeStage(
        status=SectionStatus(state="in_progress"),
        project_title="Bath",
        project_type="bathroom",
        property_context=PropertyContext(
            zipcode="95120",
            dwelling_type="independent_house",
            occupancy="owner_occupied",
            renovation_area=50.0,
        ),
        special_considerations=SpecialConsiderations(allergies=[]),
        stated_goal="Refresh",
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
    )
    dossier = Dossier(
        envelope=DossierEnvelope(dossier_id="reno_s_merge", current_stage="scope"),
        project=ProjectBody(scope=scope),
    )

    # The extraction LLM returned a PARTIAL ballpark contingency (no low/high) — exactly
    # the shape that corrupted the stored session.
    clean = {"ballpark_estimate": {"contingency": {"pct_of_ballpark": 0.2, "capped": False}}}
    _merge_extracted(scope, clean, frozenset())

    # Required sub-fields survived; the updated key applied.
    assert scope.ballpark_estimate.contingency.low == 3459.6
    assert scope.ballpark_estimate.contingency.high == 5381.6
    assert scope.ballpark_estimate.contingency.pct_of_ballpark == 0.2
    # And the whole dossier round-trips through serialize -> reload (what read_session does).
    reloaded = Dossier.model_validate(dossier.model_dump(mode="json"))
    assert reloaded.project.scope.ballpark_estimate.contingency.low == 3459.6


# --- Tier-1 depth-consent guard (the Safety stage loop) ----------------------


def _safety_with_tier1(consent_a=None, consent_b=None, reclassified_a=False, ack_turn=True):
    """A safety stage with two Tier-1 items + optional user acknowledgement turn."""
    from datetime import UTC, datetime

    from domain.dossier import (
        ConversationTurn,
        DossierEnvelope,
        ProjectBody,
        SafetyPermitStage,
        SectionStatus,
        TierClassification,
    )

    convo = []
    if ack_turn:
        convo.append(
            ConversationTurn(
                role="user",
                text="Yes I acknowledge the professional only Tier-1 item",
                at=datetime.now(UTC),
            )
        )
    saf = SafetyPermitStage(
        status=SectionStatus(state="in_progress"),
        classifications=[
            TierClassification(
                item="Load-bearing wall removal",
                tier="tier_1_professional",
                source="IRC R502",
                rationale="structural",
                depth_consent=consent_a,
                reclassified_from_materials=reclassified_a,
            ),
            TierClassification(
                item="New wall construction",
                tier="tier_1_professional",
                source="IRC R502",
                rationale="structural",
                depth_consent=consent_b,
            ),
            TierClassification(
                item="Vanity plumbing",
                tier="tier_2_permitted",
                source="IRC P2701",
                rationale="drain",
            ),
        ],
        conversation=convo,
    )
    dossier = Dossier(
        envelope=DossierEnvelope(dossier_id="reno_s_saf", current_stage="safety_permit"),
        project=ProjectBody(safety_permit=saf),
    )
    return dossier, saf


def test_depth_consent_guard_sets_false_on_acknowledgement():
    """A clear USER acknowledgement resolves every unanswered Tier-1 item to False (opens gate)."""
    from agents.base import BaseAgent

    dossier, saf = _safety_with_tier1(ack_turn=True)
    # Use any concrete agent instance to reach the method (it takes stage_obj explicitly).
    from agents.safety import SafetyAgent

    SafetyAgent(dossier)._apply_safety_depth_consent_guard(saf)
    tier1 = [c for c in saf.classifications if c.tier == "tier_1_professional"]
    assert all(c.depth_consent is False for c in tier1)
    # Tier-2 item untouched (guard only writes Tier-1).
    tier2 = [c for c in saf.classifications if c.tier == "tier_2_permitted"][0]
    assert tier2.depth_consent is None


def test_depth_consent_guard_stays_none_without_acknowledgement():
    """No acknowledgement -> Tier-1 depth_consent stays None so the gate keeps blocking."""
    from agents.safety import SafetyAgent

    dossier, saf = _safety_with_tier1(ack_turn=False)
    SafetyAgent(dossier)._apply_safety_depth_consent_guard(saf)
    assert all(
        c.depth_consent is None for c in saf.classifications if c.tier == "tier_1_professional"
    )


def test_depth_consent_guard_excludes_material_breach_reclassified_item():
    """SI-31: a materials-breach-reclassified Tier-1 item must NOT be auto-consented — it
    requires fresh explicit re-consent, so the guard skips it even on acknowledgement."""
    from agents.safety import SafetyAgent

    dossier, saf = _safety_with_tier1(reclassified_a=True, ack_turn=True)
    SafetyAgent(dossier)._apply_safety_depth_consent_guard(saf)
    by_item = {c.item: c for c in saf.classifications}
    # The reclassified item stays None (fresh re-consent still required)...
    assert by_item["Load-bearing wall removal"].depth_consent is None
    # ...while the ordinary Tier-1 item is resolved.
    assert by_item["New wall construction"].depth_consent is False


def test_depth_consent_guard_does_not_overwrite_existing_true():
    """An item the family explicitly wanted explained (True) is left as-is."""
    from agents.safety import SafetyAgent

    dossier, saf = _safety_with_tier1(consent_a=True, ack_turn=True)
    SafetyAgent(dossier)._apply_safety_depth_consent_guard(saf)
    by_item = {c.item: c for c in saf.classifications}
    assert by_item["Load-bearing wall removal"].depth_consent is True  # unchanged
    assert by_item["New wall construction"].depth_consent is False  # resolved from ack
