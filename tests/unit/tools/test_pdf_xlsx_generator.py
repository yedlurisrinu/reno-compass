"""Unit tests for document generation (PDF/XLSX) and restore parsing."""

import base64
import json
from datetime import UTC, datetime

from domain.dossier import Dossier, DossierEnvelope, ProjectBody
from tools.pdf_xlsx_generator import (
    extract_dossier_json_from_pdf,
    generate_dossier_pdf,
    generate_materials_xlsx,
)


def _create_mock_dossier() -> Dossier:
    """Creates a complete mock dossier for document tests."""
    return Dossier(
        envelope=DossierEnvelope(
            dossier_id="reno_s_doc_test",
            schema_version="1.0.0",
            created_at=datetime.now(UTC),
            last_updated_at=datetime.now(UTC),
            origin="fresh",
            current_stage="scope",
        ),
        project=ProjectBody(),
    )


def test_pdf_generation_and_attachment_restore():
    """Verifies PDF generation and PDF-to-JSON parsing restore loop."""
    dossier = _create_mock_dossier()

    # 1. Generate base64 PDF
    pdf_b64 = generate_dossier_pdf(dossier)
    assert isinstance(pdf_b64, str)
    assert len(pdf_b64) > 0

    # Decode back to raw PDF bytes
    pdf_bytes = base64.b64decode(pdf_b64)

    # 2. Extract embedded dossier JSON from PDF bytes
    extracted_json = extract_dossier_json_from_pdf(pdf_bytes)
    assert isinstance(extracted_json, str)

    # Verify the contents match the original dossier
    extracted_data = json.loads(extracted_json)
    assert extracted_data["envelope"]["dossier_id"] == "reno_s_doc_test"
    assert extracted_data["envelope"]["schema_version"] == "1.0.0"


def test_pdf_is_safety_forward_and_handles_design_options():
    """H10: PDF puts Safety before Budget, carries disclaimers, and renders design options."""
    import io

    from pypdf import PdfReader

    from domain.dossier import (
        BallparkContingency,
        BallparkEstimate,
        BudgetRealityCheck,
        ChosenDesign,
        DesignOption,
        DesignStage,
        Dimensions,
        PhaseChecklists,
        PropertyContext,
        RefinedEstimate,
        Room,
        SafetyPermitStage,
        ScopeStage,
        SpecialConsiderations,
        SynthesisStage,
        TierClassification,
    )

    est = RefinedEstimate(
        low=19000.0,
        high=22000.0,
        includes_professional=True,
        includes_permit=True,
        over_ceiling=False,
    )
    scope = ScopeStage(
        project_title="Bath",
        project_type="bathroom",
        property_context=PropertyContext(
            zipcode="95120",
            dwelling_type="independent_house",
            occupancy="owner_occupied",
            renovation_area=80.0,
        ),
        special_considerations=SpecialConsiderations(allergies=[]),
        stated_goal="Refresh the bath",
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
    design = DesignStage(
        rooms=[
            Room(
                label="Bath",
                dimensions=Dimensions(length=10.0, width=8.0, height=8.0, unit="ft"),
                derived_area=80.0,
                derived_volume=640.0,
            )
        ],
        # design options present — the path that crashed before the H10 rewrite
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
    )
    safety = SafetyPermitStage(
        classifications=[
            TierClassification(
                item="panel circuit",
                tier="tier_1_professional",
                source="NEC 210.11",
                rationale="dedicated circuit",
                depth_consent=True,
            )
        ],
        permit_required=True,
    )
    synthesis = SynthesisStage(
        design_accepted=True,
        phase_checklists=PhaseChecklists(
            before_demolition=["Order materials"],
            after_demolition=["Inspect"],
            while_reno_in_progress=["Waterproof"],
            wrap_up=["Sign off"],
        ),
        pdf_ref="reno_compass_blueprint.pdf",
    )
    dossier = Dossier(
        envelope=DossierEnvelope(dossier_id="t", current_stage="synthesis"),
        project=ProjectBody(scope=scope, design=design, safety_permit=safety, synthesis=synthesis),
    )

    pdf_b64 = generate_dossier_pdf(dossier)  # must not raise with options present
    text = "".join(p.extract_text() for p in PdfReader(io.BytesIO(base64.b64decode(pdf_b64))).pages)

    assert "Safety" in text and "Budget" in text
    # Safety-forward: the Safety section precedes the Budget section.
    assert text.index("Safety") < text.index("Budget")
    # Disclaimers carry through.
    assert "Not intended for contractor distribution" in text
    assert "verify locally" in text


def test_materials_xlsx_generation():
    """Verifies Excel shopping list generation outputs base64 data."""
    dossier = _create_mock_dossier()

    xlsx_b64 = generate_materials_xlsx(dossier)
    assert isinstance(xlsx_b64, str)
    assert len(xlsx_b64) > 0

    # Decode to verify it's valid zip/xlsx bytes
    xlsx_bytes = base64.b64decode(xlsx_b64)
    # Excel files start with PK signature (standard zip)
    assert xlsx_bytes.startswith(b"PK")
