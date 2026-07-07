"""Unit tests to verify Card metadata contracts for all 8 stage agents."""

from datetime import datetime

import pytest

from agents import (
    ContractorAgent,
    DesignAgent,
    DiyAgent,
    LogisticsAgent,
    MaterialsAgent,
    SafetyAgent,
    ScopeAgent,
    SynthesisAgent,
)
from domain.dossier import Dossier, DossierEnvelope, ProjectBody


@pytest.fixture
def mock_dossier() -> Dossier:
    """Returns basic mock dossier."""
    return Dossier(
        envelope=DossierEnvelope(
            dossier_id="reno_s_stages_test",
            schema_version="1.0.0",
            created_at=datetime.utcnow(),
            last_updated_at=datetime.utcnow(),
            origin="fresh",
            current_stage="scope",
        ),
        project=ProjectBody(),
    )


def test_agent_card_declarations(mock_dossier):
    """Verifies that all 8 stage agents declare correct identities and data limits."""
    # Scope
    scope = ScopeAgent(mock_dossier)
    assert scope.card.stage_key == "scope"
    assert "pricing-ballpark" in scope.card.associated_skills
    assert "RD-2" in scope.card.associated_references
    assert scope.card.search_grounding_enabled is False

    # Design — refined estimates come from frozen RD-2, so grounding stays OFF (Principle 9)
    design = DesignAgent(mock_dossier)
    assert design.card.stage_key == "design"
    assert "design-generation" in design.card.associated_skills
    assert "RD-2" in design.card.associated_references  # refined estimate basis
    assert "RD-4" in design.card.associated_references  # lighting targets
    assert design.card.search_grounding_enabled is False

    # Safety
    safety = SafetyAgent(mock_dossier)
    assert safety.card.stage_key == "safety_permit"
    assert "safety-tier-classification" in safety.card.associated_skills
    assert "RD-1" in safety.card.associated_references
    assert safety.card.search_grounding_enabled is False

    # Logistics — displacement costs come from frozen RD-2 bands, grounding OFF (Principle 9)
    logistics = LogisticsAgent(mock_dossier)
    assert logistics.card.stage_key == "logistics_feasibility"
    assert "displacement-alternatives" in logistics.card.associated_skills
    assert "RD-2" in logistics.card.associated_references
    assert logistics.card.search_grounding_enabled is False

    # Materials — bands (RD-3) + regional factor (RD-2) + finish (RD-4) + envelope bounds (RD-1)
    materials = MaterialsAgent(mock_dossier)
    assert materials.card.stage_key == "materials"
    assert "material-bands" in materials.card.associated_skills
    for ref in ("RD-3", "RD-2", "RD-4", "RD-1"):
        assert ref in materials.card.associated_references
    assert materials.card.search_grounding_enabled is True  # live product availability (M1)

    # Contractor — shared safety-tier spine + RD-2/RD-3 for the low-bid cross-check
    contractor = ContractorAgent(mock_dossier)
    assert contractor.card.stage_key == "contractor_validation"
    assert "quote-audit" in contractor.card.associated_skills
    assert "safety-tier-classification" in contractor.card.associated_skills
    for ref in ("RD-5", "RD-2", "RD-3"):
        assert ref in contractor.card.associated_references
    assert contractor.card.search_grounding_enabled is False

    # DIY — RD-1 hold-points + RD-3 material bands
    diy = DiyAgent(mock_dossier)
    assert diy.card.stage_key == "diy_planning"
    assert "diy-procedure" in diy.card.associated_skills
    assert "RD-1" in diy.card.associated_references
    assert "RD-3" in diy.card.associated_references
    assert diy.card.search_grounding_enabled is True

    # Synthesis
    synthesis = SynthesisAgent(mock_dossier)
    assert synthesis.card.stage_key == "synthesis"
    assert "consolidation-summary" in synthesis.card.associated_skills
    assert len(synthesis.card.associated_references) == 0
    assert synthesis.card.search_grounding_enabled is False
