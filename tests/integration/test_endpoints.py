"""Integration tests for FastAPI endpoints, middleware, and rate-limiting."""

import os

import pytest
from fastapi.testclient import TestClient

# Set mock env variables before importing app
os.environ["STORAGE_LOCAL_FALLBACK"] = "true"
os.environ["MOCK_VERTEX_AI"] = "true"

from main import app


@pytest.fixture
def client() -> TestClient:
    """Returns FastAPI test client."""
    return TestClient(app)


def test_create_new_session_flow(client):
    """Verifies that a new session is correctly initiated with cookie set."""
    response = client.post("/api/session/new")
    assert response.status_code == 200
    data = response.json()

    # Assert session token formatting
    token = data["session_token"]
    assert token.startswith("reno_s_")

    # Assert HttpOnly cookie matches token
    cookie = response.cookies.get("reno_session_token")
    assert cookie == token


def test_chat_and_rate_limiting_middleware(client, monkeypatch):
    """Verifies chat completions and rate-limiting blocks rapid requests."""
    from config.config import settings

    # Clear the global limiters cache and temporarily restrict rate limits
    from middleware import LIMITERS

    LIMITERS.clear()
    monkeypatch.setattr(settings, "rate_limit_per_minute", 1)
    monkeypatch.setattr(settings, "rate_limit_burst", 1)

    # 1. Start a new session
    session_res = client.post("/api/session/new")
    token = session_res.json()["session_token"]

    # Configure client to pass cookie
    client.cookies.set("reno_session_token", token)

    # 2. First chat message passes rate limit
    chat_res1 = client.post(
        "/api/chat", json={"message": "We want to remodel our primary master bathroom."}
    )
    assert chat_res1.status_code == 200
    assert "response" in chat_res1.json()

    # 3. Consecutive message within same minute is rate limited
    chat_res2 = client.post("/api/chat", json={"message": "We have $15000 budget."})
    # Returns 429 Too Many Requests
    assert chat_res2.status_code == 429
    assert "rate limit" in chat_res2.json()["detail"].lower()


def test_finalize_deletes_completed_session(client):
    """A completed session's checkpoint is deleted from storage on finalize."""
    from data.storage import read_session, write_session

    token = client.post("/api/session/new").json()["session_token"]
    dossier = read_session(token)
    assert dossier is not None
    dossier.envelope.current_stage = "complete"
    write_session(token, dossier)

    res = client.post("/api/session/finalize", json={"session_token": token})
    assert res.status_code == 200
    assert res.json()["deleted"] is True
    # The checkpoint is gone.
    assert read_session(token) is None
    # A second finalize is a harmless no-op (session already removed).
    res2 = client.post("/api/session/finalize", json={"session_token": token})
    assert res2.status_code == 200
    assert res2.json()["deleted"] is False


def test_finalize_skips_incomplete_session(client):
    """Finalize must never delete a session that has not reached 'complete'."""
    from data.storage import read_session

    token = client.post("/api/session/new").json()["session_token"]  # stage == scope
    res = client.post("/api/session/finalize", json={"session_token": token})
    assert res.status_code == 200
    assert res.json() == {"deleted": False, "reason": "not_complete"}
    # The in-progress session is untouched.
    assert read_session(token) is not None


def test_finalize_requires_token(client):
    """Finalize rejects a missing session token."""
    res = client.post("/api/session/finalize", json={})
    assert res.status_code == 400
    assert res.json()["error_code"] == "MISSING_SESSION_TOKEN"


def test_proceed_on_blocked_stage_names_the_blocker_not_silent_loop(client):
    """Proceed-intent on a stage whose gate can't pass must NAME the missing item.

    Regression for the safety loop: a Tier-1 item with depth_consent=None keeps the gate
    closed. When the user asks to move on, the pipeline can't advance — and the backend
    must SAY what's still needed instead of silently repeating the agent's text (the
    warning was previously trapped inside the advance-attempt block and never fired).
    """
    from unittest.mock import patch

    from data.storage import read_session, write_session
    from domain.dossier import SafetyPermitStage, SectionStatus, TierClassification

    token = client.post("/api/session/new").json()["session_token"]
    dossier = read_session(token)
    dossier.envelope.current_stage = "safety_permit"
    dossier.project.safety_permit = SafetyPermitStage(
        status=SectionStatus(state="in_progress"),
        classifications=[
            TierClassification(
                item="Removing a Load-Bearing Wall",
                tier="tier_1_professional",
                source="IRC R502",
                rationale="structural change requires a licensed pro",
                depth_consent=None,  # never acknowledged -> gate stays closed
            )
        ],
        user_final_verdict=False,
    )
    write_session(token, dossier)

    client.cookies.set("reno_session_token", token)
    # Isolate the advancement logic: the agent replies canned text and extraction is a
    # no-op, so the seeded blocked state is exactly what the gate evaluates.
    with (
        patch("agents.safety.SafetyAgent.run_chat", return_value="Noted."),
        patch("agents.safety.SafetyAgent.extract_and_update_stage_dossier", return_value=None),
    ):
        res = client.post("/api/chat", json={"message": "let's move on to the next stage"})

    assert res.status_code == 200
    data = res.json()
    # Did NOT advance...
    assert data["current_stage"] == "safety_permit"
    # ...and NAMED the real blocker instead of looping silently.
    assert "Tier-1" in data["response"] or "professional-only" in data["response"]


def test_proceed_on_satisfiable_stage_advances_without_a_spurious_warning(client):
    """The mirror of the loop fix: when the gate CAN pass, a proceed advances cleanly and
    the "I still need…" warning must NOT be appended (the new top-level warning branch
    must never fire on a successful advance).
    """
    from unittest.mock import patch

    from data.storage import read_session, write_session
    from domain.dossier import SafetyPermitStage, SectionStatus, TierClassification

    token = client.post("/api/session/new").json()["session_token"]
    dossier = read_session(token)
    dossier.envelope.current_stage = "safety_permit"
    # A fully-satisfiable safety stage: Tier-1 item acknowledged, no permit outstanding.
    dossier.project.safety_permit = SafetyPermitStage(
        status=SectionStatus(state="in_progress"),
        classifications=[
            TierClassification(
                item="Removing a Load-Bearing Wall",
                tier="tier_1_professional",
                source="IRC R502",
                rationale="structural change requires a licensed pro",
                depth_consent=True,  # acknowledged -> gate can open
            )
        ],
        permit_required=False,
        user_final_verdict=False,
    )
    write_session(token, dossier)

    client.cookies.set("reno_session_token", token)
    with (
        patch("agents.safety.SafetyAgent.run_chat", return_value="Noted."),
        patch("agents.safety.SafetyAgent.extract_and_update_stage_dossier", return_value=None),
    ):
        res = client.post("/api/chat", json={"message": "let's move on to the next stage"})

    assert res.status_code == 200
    data = res.json()
    # It advanced past safety...
    assert data["current_stage"] != "safety_permit"
    # ...and did NOT append the missing-requirement warning.
    assert "I still need" not in data["response"]
