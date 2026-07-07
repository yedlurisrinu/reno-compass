from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


def test_transition_tag_is_advisory_and_does_not_advance_on_its_own(monkeypatch):
    """The agent's inline tag is stripped but NEVER advances the stage by itself.

    Advancement is the family's decision, not the model's: the
    ``[APPROVE_STAGE_TRANSITION]`` tag signals the agent THINKS it is ready, but the
    pipeline only moves on a real user proceed-intent (or a satisfied resume gate). A
    tag emitted while the user is still answering questions must leave the stage put.
    """
    monkeypatch.setenv("MOCK_VERTEX_AI", "true")
    client = TestClient(app)

    res_new = client.post("/api/session/new")
    token = res_new.json()["session_token"]

    # The agent emits the readiness tag, but the user's message is NOT a proceed-intent
    # (they are merely restating a choice), so the pipeline must stay in scope.
    with patch(
        "agents.scope.ScopeAgent.run_chat",
        return_value="We are ready to proceed! [APPROVE_STAGE_TRANSITION]",
    ):
        client.post(
            "/api/chat",
            json={"session_token": token, "message": "My budget is 20000 and zipcode is 95120"},
        )
        res_chat = client.post(
            "/api/chat", json={"session_token": token, "message": "Confirming my choices."}
        )

    assert res_chat.status_code == 200
    data = res_chat.json()
    # The tag alone did NOT advance the stage...
    assert data["current_stage"] == "scope"
    # ...and it is never shown to the customer.
    assert "[APPROVE_STAGE_TRANSITION]" not in data["response"]
