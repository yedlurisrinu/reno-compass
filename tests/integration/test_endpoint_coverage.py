"""Integration tests covering the session-lifecycle endpoints and error handlers.

Exercises ``/api/session/load``, ``/api/session/advance``,
``/api/session/restore-pdf``, ``/api/session/download-artifacts`` and
``/api/session/finalize`` across their success and failure branches, plus the
custom HTTPException handler, using an in-process ``TestClient`` in mock mode.
"""

import os

os.environ["STORAGE_LOCAL_FALLBACK"] = "true"
os.environ["MOCK_VERTEX_AI"] = "true"

import pytest
from fastapi.testclient import TestClient

from data.storage import read_session, write_session
from main import app
from tools.pdf_xlsx_generator import generate_dossier_pdf


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _new_token(client) -> str:
    return client.post("/api/session/new").json()["session_token"]


# --------------------------------------------------------------------------- #
# /api/session/load
# --------------------------------------------------------------------------- #


def test_load_missing_token(client):
    res = client.post("/api/session/load", json={})
    assert res.status_code == 400
    assert res.json()["error_code"] == "MISSING_SESSION_TOKEN"


def test_load_not_found(client):
    res = client.post("/api/session/load", json={"session_token": "reno_s_missing"})
    assert res.status_code == 404
    assert res.json()["error_code"] == "SESSION_NOT_FOUND"


def test_load_existing_session(client):
    token = _new_token(client)
    res = client.post("/api/session/load", json={"session_token": token})
    assert res.status_code == 200
    body = res.json()
    assert body["session_token"] == token
    assert body["current_stage"] == "scope"
    assert "quick_replies" in body
    assert "input_hint" in body


# --------------------------------------------------------------------------- #
# /api/session/advance
# --------------------------------------------------------------------------- #


def test_advance_missing_token(client):
    res = client.post("/api/session/advance", json={})
    assert res.status_code == 400
    assert res.json()["error_code"] == "MISSING_SESSION_TOKEN"


def test_advance_not_found(client):
    res = client.post("/api/session/advance", json={"session_token": "reno_s_missing"})
    assert res.status_code == 404


def test_advance_blocked_when_gate_unsatisfied(client):
    # A brand-new session sits at scope with no budget/zip -> gate must block.
    token = _new_token(client)
    res = client.post("/api/session/advance", json={"session_token": token})
    assert res.status_code == 400
    assert res.json()["error_code"] == "STAGE_GATE_NOT_SATISFIED"


# --------------------------------------------------------------------------- #
# /api/session/download-artifacts
# --------------------------------------------------------------------------- #


def test_download_missing_token(client):
    res = client.post("/api/session/download-artifacts", json={})
    assert res.status_code == 400


def test_download_not_found(client):
    res = client.post("/api/session/download-artifacts", json={"session_token": "reno_s_missing"})
    assert res.status_code == 404


def test_download_artifacts_success(client):
    token = _new_token(client)
    res = client.post("/api/session/download-artifacts", json={"session_token": token})
    assert res.status_code == 200
    body = res.json()
    assert body["pdf_base64"]
    assert body["xlsx_base64"]
    assert body["pdf_filename"].endswith(".pdf")
    assert body["xlsx_filename"].endswith(".xlsx")


# --------------------------------------------------------------------------- #
# /api/session/restore-pdf
# --------------------------------------------------------------------------- #


def test_restore_pdf_roundtrip(client):
    token = _new_token(client)
    dossier = read_session(token)
    pdf_b64 = generate_dossier_pdf(dossier)
    import base64

    pdf_bytes = base64.b64decode(pdf_b64)

    res = client.post(
        "/api/session/restore-pdf",
        files={"file": ("blueprint.pdf", pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 200
    body = res.json()
    # Untrusted import is reset to scope for re-walk verification.
    assert body["current_stage"] == "scope"
    assert body["session_token"].startswith("reno_s_")
    assert "warning" in body


def test_restore_pdf_invalid_file(client):
    res = client.post(
        "/api/session/restore-pdf",
        files={"file": ("junk.pdf", b"not a real pdf", "application/pdf")},
    )
    assert res.status_code == 400
    assert res.json()["error_code"] == "PDF_PARSE_FAILED"


# --------------------------------------------------------------------------- #
# /api/session/finalize
# --------------------------------------------------------------------------- #


def test_finalize_missing_token(client):
    res = client.post("/api/session/finalize", json={})
    assert res.status_code == 400


def test_finalize_not_found_is_success(client):
    res = client.post("/api/session/finalize", json={"session_token": "reno_s_missing"})
    assert res.status_code == 200
    assert res.json() == {"deleted": False, "reason": "not_found"}


def test_finalize_not_complete(client):
    token = _new_token(client)
    res = client.post("/api/session/finalize", json={"session_token": token})
    assert res.status_code == 200
    assert res.json() == {"deleted": False, "reason": "not_complete"}


def test_finalize_complete_deletes(client):
    token = _new_token(client)
    dossier = read_session(token)
    dossier.envelope.current_stage = "complete"
    write_session(token, dossier)

    res = client.post("/api/session/finalize", json={"session_token": token})
    assert res.status_code == 200
    assert res.json()["deleted"] is True
    # Session is gone now.
    assert read_session(token) is None


# --------------------------------------------------------------------------- #
# Chat endpoint guard branches
# --------------------------------------------------------------------------- #


def test_chat_missing_token(client):
    res = client.post("/api/chat", json={"message": "hi"})
    assert res.status_code == 400
    assert res.json()["error_code"] == "MISSING_SESSION_TOKEN"


def test_chat_missing_message(client):
    token = _new_token(client)
    res = client.post("/api/chat", json={"session_token": token})
    assert res.status_code == 400
    assert res.json()["error_code"] == "MISSING_CHAT_MESSAGE"


def test_chat_rejected_when_complete(client):
    token = _new_token(client)
    dossier = read_session(token)
    dossier.envelope.current_stage = "complete"
    write_session(token, dossier)
    res = client.post("/api/chat", json={"session_token": token, "message": "hi"})
    assert res.status_code == 400
    assert res.json()["error_code"] == "DOSSIER_COMPLETE"
