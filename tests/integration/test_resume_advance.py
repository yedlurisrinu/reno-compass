"""Regression: on resume, a stage whose gate is already satisfied must advance.

The auto-advance tag ([APPROVE_STAGE_TRANSITION]) is only emitted in the turn where
the agent first signals readiness. After a reload, a stage confirmed in a prior
session never re-emits it, so advancement must fall back to the deterministic stage
gate. Conversely, an unsatisfied gate with no tag must stay put and NOT warn.
"""

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ["MOCK_VERTEX_AI"] = "true"
os.environ["STORAGE_LOCAL_FALLBACK"] = "true"

from data.storage import write_session  # noqa: E402
from domain.dossier import (  # noqa: E402
    Dossier,
    DossierEnvelope,
    LogisticsFeasibilityStage,
    ProjectBody,
    SectionStatus,
)
from main import app  # noqa: E402


def _logistics_dossier(token, *, can_live_through_it, verdict):
    logi = LogisticsFeasibilityStage(
        status=SectionStatus(state="in_progress"),
        disruption={
            "offline_utilities": [],
            "offline_duration_estimate": "",
            "can_live_through_it": can_live_through_it,
        },
        verdict="proceed",
        user_final_verdict=verdict,
    )
    return Dossier(
        envelope=DossierEnvelope(dossier_id=token, current_stage="logistics_feasibility"),
        project=ProjectBody(logistics_feasibility=logi),
    )


def test_resume_advances_when_gate_satisfied_without_tag():
    """Gate fully satisfied + NO tag in the reply -> still advances to materials."""
    token = "reno_s_resume_ok"
    write_session(token, _logistics_dossier(token, can_live_through_it=True, verdict=True))

    client = TestClient(app)
    with (
        patch(
            "agents.logistics.LogisticsAgent.run_chat",
            return_value="Sure, we can proceed.",  # deliberately NO transition tag
        ),
        patch(
            "agents.materials.MaterialsAgent.run_chat",
            return_value="Welcome to materials selection.",
        ),
    ):
        res = client.post("/api/chat", json={"session_token": token, "message": "Please continue."})

    assert res.status_code == 200, res.text
    assert res.json()["current_stage"] == "materials"


def test_no_tag_and_unsatisfied_gate_stays_and_does_not_warn():
    """Gate NOT satisfied (can_live_through_it null) + no tag -> stays, no warning noise."""
    token = "reno_s_resume_block"
    write_session(token, _logistics_dossier(token, can_live_through_it=None, verdict=False))

    client = TestClient(app)
    with patch(
        "agents.logistics.LogisticsAgent.run_chat",
        return_value="Tell me about your living arrangements.",
    ):
        res = client.post(
            "/api/chat", json={"session_token": token, "message": "What are my options?"}
        )

    assert res.status_code == 200, res.text
    assert res.json()["current_stage"] == "logistics_feasibility"
    # A plain turn (no transition tag) must not surface the readiness warning.
    assert "fully captured on my end" not in res.json()["response"]


def test_user_proceed_intent_advances_without_tag():
    """Explicit user proceed-intent sets the verdict and advances (no agent tag)."""
    token = "reno_s_proceed_intent"
    # Substantive gate met (can_live_through_it) but verdict not yet given.
    write_session(token, _logistics_dossier(token, can_live_through_it=True, verdict=False))

    client = TestClient(app)
    with (
        patch("agents.logistics.LogisticsAgent.run_chat", return_value="Understood."),
        patch("agents.materials.MaterialsAgent.run_chat", return_value="On to materials."),
    ):
        res = client.post(
            "/api/chat",
            json={"session_token": token, "message": "Great, let's move on to the next stage."},
        )

    assert res.status_code == 200, res.text
    assert res.json()["current_stage"] == "materials"


def test_mere_mention_without_proceed_intent_does_not_advance():
    """Discussing something ('sounds good') without an explicit proceed request stays put."""
    token = "reno_s_no_intent"
    write_session(token, _logistics_dossier(token, can_live_through_it=True, verdict=False))

    client = TestClient(app)
    with patch(
        "agents.logistics.LogisticsAgent.run_chat",
        return_value="Glad that helps.",
    ):
        res = client.post(
            "/api/chat",
            json={"session_token": token, "message": "That displacement idea sounds good."},
        )

    assert res.status_code == 200, res.text
    assert res.json()["current_stage"] == "logistics_feasibility"


def test_transition_tag_never_leaks_to_customer():
    """The [APPROVE_STAGE_TRANSITION] tag is detected but stripped from the reply."""
    token = "reno_s_tag_strip"
    write_session(token, _logistics_dossier(token, can_live_through_it=True, verdict=False))

    client = TestClient(app)
    with (
        patch(
            "agents.logistics.LogisticsAgent.run_chat",
            return_value="All set here. [APPROVE_STAGE_TRANSITION]",
        ),
        patch("agents.materials.MaterialsAgent.run_chat", return_value="Materials time."),
    ):
        res = client.post("/api/chat", json={"session_token": token, "message": "ok"})

    assert res.status_code == 200, res.text
    assert res.json()["current_stage"] == "materials"
    assert "APPROVE_STAGE_TRANSITION" not in res.json()["response"]
