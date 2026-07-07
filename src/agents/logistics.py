"""Logistics & Feasibility Agent.

Assesses utility outages (water, power, sewer), evaluates whether family can
live through the build, and provides displacement cost ranges.
"""

from agents.base import AgentCard, BaseAgent


class LogisticsAgent(BaseAgent):
    """Logistics stage agent managing project schedules, outages, and housing fallbacks."""

    card = AgentCard(
        name="Logistics & Feasibility Agent",
        stage_key="logistics_feasibility",
        description="Coordinates utility outage calculations and calculates alternative housing displacement outlays.",
        reads=[
            "project.scope",
            "project.design",
            "project.safety_permit",
            "project.logistics_feasibility",
        ],
        writes=["project.logistics_feasibility"],
        associated_skills=["disruption-assessment", "displacement-alternatives"],
        associated_references=["RD-2"],
        # Displacement costs come from the frozen RD-2 regional bands, not live
        # rental pricing (Principle 9); grounding off keeps estimates curated.
        search_grounding_enabled=False,
    )
