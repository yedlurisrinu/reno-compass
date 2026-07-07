"""Design Generation Agent.

Handles layout creation, preferred vs economy options, lighting targeting,
and refined design estimates. Enforces Title 24 design-level boundaries.
"""

from agents.base import AgentCard, BaseAgent


class DesignAgent(BaseAgent):
    """Design stage agent generating layout and spatial geometry alternatives."""

    card = AgentCard(
        name="Design Layout Agent",
        stage_key="design",
        description="Generates scope-faithful preferred and economy layout choices, and assigns lighting requirements.",
        reads=["project.scope", "project.design"],
        writes=["project.design"],
        associated_skills=["design-generation", "lighting-targets"],
        associated_references=["RD-2", "RD-4"],  # RD-2 refined estimates + RD-4 lighting
        # Refined estimates must come from the frozen RD-2 bands, not live web pricing
        # (Principle 9); grounding is off so numbers stay curated.
        search_grounding_enabled=False,
    )
