"""Safety & Permit Agent.

Classifies all scope and design modifications into explicit safety tiers
(Professional, Permitted, Proceed) using Building Code references (IRC/NEC).
"""

from agents.base import AgentCard, BaseAgent


class SafetyAgent(BaseAgent):
    """Safety stage agent performing code inspections and structural/electrical safety categorizations."""

    card = AgentCard(
        name="Safety & Permit Invariant Agent",
        stage_key="safety_permit",
        description="Evaluates joist modifications, spans, floor loading, and dedicated circuit needs against IRC/NEC.",
        reads=["project.scope", "project.design", "project.safety_permit"],
        writes=["project.safety_permit"],
        associated_skills=["safety-tier-classification", "irc-safety"],
        associated_references=["RD-1"],
        search_grounding_enabled=False,  # Safety limits must stay strictly bound to curated code tables
    )
