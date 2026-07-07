"""Regression: advancing INTO synthesis via /api/chat must not crash.

SynthesisStage has no ``conversation`` field; the auto-advance seed-greeting logic
in main.py must skip conversation seeding for it (found in the live walk).
"""

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ["MOCK_VERTEX_AI"] = "true"
os.environ["STORAGE_LOCAL_FALLBACK"] = "true"

from data.storage import write_session  # noqa: E402
from domain.dossier import (  # noqa: E402
    ChosenDesign,
    ContractorValidationStage,
    DesignOption,
    DesignStage,
    Dossier,
    DossierEnvelope,
    ProjectBody,
    RefinedEstimate,
    SafetyPermitStage,
    SectionStatus,
    TierClassification,
)
from main import app  # noqa: E402


def _dossier_at_contractor(token):
    est = RefinedEstimate(
        low=19000.0,
        high=22000.0,
        includes_professional=True,
        includes_permit=True,
        over_ceiling=False,
    )
    design = DesignStage(
        status=SectionStatus(state="completed"),
        options=[
            DesignOption(
                label="P",
                option_role="preferred",
                description="p",
                value_proposition="v",
                layout={},
                refined_estimate=est,
            )
        ],
        chosen_design=ChosenDesign(
            chosen_label="P", option_role="preferred", layout={}, refined_estimate=est
        ),
        user_final_verdict=True,
    )
    # All Tier-1 -> DIY is skipped, so contractor advances straight to synthesis.
    safety = SafetyPermitStage(
        status=SectionStatus(state="completed"),
        classifications=[
            TierClassification(
                item="panel circuit",
                tier="tier_1_professional",
                source="NEC 210.11",
                rationale="dedicated circuit",
                depth_consent=True,
            )
        ],
        user_final_verdict=True,
    )
    contractor = ContractorValidationStage(
        status=SectionStatus(state="in_progress"),
        advisory_checklist=["Get 3-5 bids on identical scope."],
        quote_provided=False,
    )
    return Dossier(
        envelope=DossierEnvelope(dossier_id=token, current_stage="contractor_validation"),
        project=ProjectBody(design=design, safety_permit=safety, contractor_validation=contractor),
    )


def test_advance_into_synthesis_does_not_crash():
    token = "reno_s_synthtest"
    write_session(token, _dossier_at_contractor(token))

    client = TestClient(app)
    with (
        patch(
            "agents.contractor.ContractorAgent.run_chat",
            return_value="All set. [APPROVE_STAGE_TRANSITION]",
        ),
        patch(
            "agents.synthesis.SynthesisAgent.run_chat",
            return_value="Here is your finalized plan summary.",
        ),
    ):
        res = client.post("/api/chat", json={"session_token": token, "message": "Please finalize."})

    assert res.status_code == 200, res.text  # previously 500: no 'conversation' on SynthesisStage
    assert res.json()["current_stage"] == "synthesis"
