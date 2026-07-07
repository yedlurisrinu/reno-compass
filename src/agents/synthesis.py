"""Synthesis Agent.

Assembles the final renovation plan, compiles phase checklists, bridges budget gaps,
and triggers PDF/XLSX generation.
"""

from agents.base import AgentCard, BaseAgent


class SynthesisAgent(BaseAgent):
    """Synthesis stage agent wrapping up calculations and consolidating planning documents."""

    card = AgentCard(
        name="Plan Consolidation Synthesis Agent",
        stage_key="synthesis",
        description="Assembles the final blueprint, maps out execution phases, and initiates document base64 rendering.",
        reads=[
            "project.scope",
            "project.design",
            "project.safety_permit",
            "project.logistics_feasibility",
            "project.materials",
            "project.contractor_validation",
            "project.diy_planning",
            "project.synthesis",
        ],
        writes=["project.synthesis"],
        associated_skills=["consolidation-summary", "phase-checklist"],
        associated_references=[],
        search_grounding_enabled=False,
    )
