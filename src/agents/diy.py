"""DIY Planning Agent.

Generates step-level DIY procedures for cosmetic and non-Tier-1 work,
integrating professional dependencies as hold-points.
"""

from agents.base import AgentCard, BaseAgent


class DiyAgent(BaseAgent):
    """DIY stage agent compiling safe project execution tutorials and tool specs."""

    card = AgentCard(
        name="DIY Execution Planner Agent",
        stage_key="diy_planning",
        description="Compiles detailed DIY procedures and tool guidelines, integrating safety hold-points for professional inspections.",
        reads=[
            "project.scope",
            "project.design",
            "project.safety_permit",
            "project.materials",
            "project.diy_planning",
        ],
        writes=["project.diy_planning"],
        associated_skills=["diy-procedure", "tools-equipment"],
        associated_references=["RD-1", "RD-3"],  # RD-1 safety hold-points + RD-3 material bands
        search_grounding_enabled=True,  # Grounded to query tool hire guides or local rental rates
    )
