from fastapi.testclient import TestClient

from main import app


def test_payload_exposure_endpoints(monkeypatch):
    """Verifies that no endpoints leak raw dossier data schemas and return flat keys."""
    monkeypatch.setenv("MOCK_VERTEX_AI", "true")
    client = TestClient(app)

    # 1. New Session
    res_new = client.post("/api/session/new")
    assert res_new.status_code == 200
    data_new = res_new.json()
    assert "dossier" not in data_new
    assert "current_stage" in data_new
    assert "conversation" in data_new

    # 2. Chat
    token = data_new["session_token"]
    res_chat = client.post(
        "/api/chat", json={"session_token": token, "message": "Hi, I want to start my remodel"}
    )
    assert res_chat.status_code == 200
    data_chat = res_chat.json()
    assert "dossier" not in data_chat
    assert "response" in data_chat
    assert "current_stage" in data_chat
    assert "conversation" in data_chat
