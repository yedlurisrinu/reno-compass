"""Materials Selection Agent.

Compiles itemized material lists, runs allergy screens, and performs
material-to-safety envelope check validations.
"""

from agents.base import AgentCard, BaseAgent


class MaterialsAgent(BaseAgent):
    """Materials stage agent compiling product lists and running allergen screens."""

    card = AgentCard(
        name="Materials Selection Agent",
        stage_key="materials",
        description="Compiles material specifications, runs allergy filters, and validates selection weight and power against Safety limits.",
        reads=[
            "project.scope",
            "project.design",
            "project.safety_permit",
            "project.logistics_feasibility",
            "project.materials",
        ],
        writes=["project.materials"],
        associated_skills=["material-bands"],
        # RD-3 bands + RD-2 regional factor + RD-4 finish/lighting + RD-1 envelope bounds (SI-31)
        associated_references=["RD-3", "RD-2", "RD-4", "RD-1"],
        search_grounding_enabled=True,  # Grounded to perform live web queries for missing materials and pricing bands
    )
