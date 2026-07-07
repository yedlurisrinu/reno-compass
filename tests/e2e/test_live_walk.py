"""Live end-to-end walk against a running Reno Compass server (real Vertex AI).

This drives the exact click-through we validated by hand: create a session, walk
every stage to `complete`, and verify the safety-forward PDF + XLSX artifacts.

It makes REAL Gemini calls, so it is slow (~10 min) and needs Google credentials.
It is SKIPPED by default; opt in explicitly:

    # start the server first:
    PYTHONPATH=src uvicorn main:app --port 8000 &
    # then:
    RUN_LIVE_E2E=1 pytest tests/e2e/test_live_walk.py -v -s

Override the target with BASE_URL (default http://localhost:8000).
"""

import base64
import io
import os

import pytest

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
REQUEST_TIMEOUT = float(os.getenv("LIVE_E2E_TIMEOUT", "300"))  # per LLM turn

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_E2E") != "1",
    reason="Live E2E walk (real Vertex AI) — set RUN_LIVE_E2E=1 and start the server to run.",
)

# One representative message per stage. The driver resends a stage's message until
# the stage advances (LLM turn count varies), so each must fully satisfy that gate.
STAGE_MESSAGES = {
    "scope": (
        "I want a fresh modern main bathroom remodel. Home is 25 years old, bathroom is "
        "10 ft by 8 ft, zip 95120. Budget target 40000, ceiling 45000. I have no known "
        "allergies and no accessibility needs. Must-haves: walk-in shower and double vanity. "
        "Nice-to-have: heated floors. Timeline flexible over 6 months. This all looks correct, "
        "please proceed."
    ),
    "design": "I love the Preferred design concept - let's go with that one. Please proceed.",
    "safety_permit": (
        "I consent to hear the depth explanation for any professional-required items, and I "
        "will obtain all required permits. I understand and I'm ready to proceed."
    ),
    "logistics_feasibility": (
        "We have a second bathroom so we can live through the remodel without displacement. "
        "This is feasible within our budget - please proceed."
    ),
    "materials": (
        "Compile the materials list with mid-range finishes: porcelain tile at an 8 dollar per "
        "square foot allowance, and a quartz double vanity top. These look good - please proceed."
    ),
    "contractor_validation": (
        "I don't have a contractor quote yet. Just give me the advisory checklist of what to "
        "demand when I get bids. That's all I need - please proceed."
    ),
    "diy_planning": (
        "I'll do the painting and demo prep myself and hire out the rest. The DIY plan looks "
        "great - please finalize my complete plan."
    ),
    "synthesis": "This complete plan looks perfect. I have everything I need. Please finalize it.",
}


@pytest.fixture(scope="module")
def client():
    httpx = pytest.importorskip("httpx")
    with httpx.Client(base_url=BASE_URL, timeout=REQUEST_TIMEOUT) as c:
        try:
            if c.get("/").status_code != 200:
                pytest.skip(f"Server at {BASE_URL} did not return 200 on '/'.")
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"No server reachable at {BASE_URL}: {exc}")
        yield c


def _chat(client, token, message):
    r = client.post("/api/chat", json={"session_token": token, "message": message})
    assert r.status_code == 200, f"chat failed ({r.status_code}): {r.text[:300]}"
    return r.json()


def test_full_live_walk_to_complete_and_pdf(client):
    # 1. New session
    new = client.post("/api/session/new")
    assert new.status_code == 200
    token = new.json()["session_token"]
    assert new.json()["current_stage"] == "scope"

    # 2. Walk every stage to complete (resend a stage's message until it advances)
    stage = "scope"
    visited = []
    for _turn in range(25):  # generous bound for LLM turn variability
        if stage == "complete":
            break
        assert stage in STAGE_MESSAGES, f"unexpected stage: {stage}"
        if stage not in visited:
            visited.append(stage)
        data = _chat(client, token, STAGE_MESSAGES[stage])
        stage = data["current_stage"]

    assert stage == "complete", f"pipeline stuck at {stage}; visited={visited}"
    assert visited[0] == "scope"
    # Synthesis must have been reached (the DIY->synthesis seed path).
    assert "synthesis" in visited

    # 3. Artifacts: safety-forward PDF + XLSX
    art = client.post("/api/session/download-artifacts", json={"session_token": token})
    assert art.status_code == 200
    payload = art.json()
    pdf = base64.b64decode(payload["pdf_base64"])
    xlsx = base64.b64decode(payload["xlsx_base64"])
    assert xlsx[:2] == b"PK", "XLSX is not a valid zip/xlsx"

    pypdf = pytest.importorskip("pypdf")
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    text = "".join(p.extract_text() for p in reader.pages)
    assert "Safety" in text and "Budget" in text
    assert text.index("Safety") < text.index("Budget"), "PDF is not safety-forward"
    assert "Not intended for contractor distribution" in text
    assert "verify locally" in text
    assert "dossier.json" in reader.attachments, "PDF is missing the embedded dossier.json"
