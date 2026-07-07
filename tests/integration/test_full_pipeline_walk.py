"""End-to-end regression: a mock-mode pipeline walk from Scope to complete.

Exercises every tightened gate, the DIY skip, and the Synthesis population/finalize
path in one pass. If any gate over-blocks the happy path, this fails.
"""

from agents.contractor import ContractorAgent
from agents.design import DesignAgent
from agents.diy import DiyAgent
from agents.logistics import LogisticsAgent
from agents.materials import MaterialsAgent
from agents.safety import SafetyAgent
from agents.scope import ScopeAgent
from agents.synthesis import SynthesisAgent
from domain.dossier import (
    ConversationTurn,
    Dossier,
    DossierEnvelope,
    ProjectBody,
)
from orchestrator import advance_pipeline

_AGENTS = {
    "scope": ScopeAgent,
    "design": DesignAgent,
    "safety_permit": SafetyAgent,
    "logistics_feasibility": LogisticsAgent,
    "materials": MaterialsAgent,
    "contractor_validation": ContractorAgent,
    "diy_planning": DiyAgent,
    "synthesis": SynthesisAgent,
}


def test_full_pipeline_walk_to_complete(monkeypatch):
    monkeypatch.setenv("MOCK_VERTEX_AI", "true")
    dossier = Dossier(envelope=DossierEnvelope(dossier_id="walk"), project=ProjectBody())

    visited = []
    for _ in range(20):  # generous bound; the DAG is 8 stages with one skip
        stage = dossier.envelope.current_stage
        if stage == "complete":
            break
        visited.append(stage)

        agent = _AGENTS[stage](dossier)
        obj = getattr(dossier.project, stage, None)
        if not obj:
            obj = agent._create_default_stage_object(stage)
            setattr(dossier.project, stage, obj)

        if hasattr(obj, "conversation"):
            obj.conversation.append(
                ConversationTurn(
                    role="user",
                    text="My budget is 40000 and zipcode is 95120. Ready to proceed.",
                )
            )
        agent.extract_and_update_stage_dossier()
        if hasattr(obj, "user_final_verdict"):
            obj.user_final_verdict = True

        # Mirror the chip-driven decisions the chat endpoint records deterministically:
        # the all-or-none DIY intent at Contractor, and the per-item can-do decision in
        # the DIY loop. Without these the new gates correctly hold the pipeline.
        if stage == "contractor_validation":
            obj.wants_diy = True
        if stage == "diy_planning":
            for proc in obj.procedures:
                if proc.user_feasible is None:
                    proc.user_feasible = True

        assert advance_pipeline(dossier), f"pipeline failed to advance from {stage}"

    assert dossier.envelope.current_stage == "complete"
    # The mock Safety set has a Tier-2 (permitted) item, now DIY-eligible on its own,
    # so with wants_diy=True the DIY loop runs (it is no longer skipped).
    assert "diy_planning" in visited
    assert visited[0] == "scope"

    # Synthesis writes were populated and the artifact reference recorded (H8/H9).
    synthesis = dossier.project.synthesis
    assert synthesis.design_accepted is True
    assert synthesis.pdf_ref == "reno_compass_blueprint.pdf"
    assert synthesis.generated_at is not None
    assert synthesis.phase_checklists is not None
    # The self-performed item lands in the DIY scope; nothing handed back to a pro.
    assert synthesis.diy_scope
    assert synthesis.contractor_scope_additions == []
