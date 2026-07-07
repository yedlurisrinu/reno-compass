"""Scope Elicitation Agent.

Handles project scope decomposition, home age hidden condition surfacing,
ballpark estimation, and stated-vs-ballpark budget recalibration.
"""

from agents.base import AgentCard, BaseAgent


class ScopeAgent(BaseAgent):
    """Scope stage agent managing initial requirements gathering and budget checks."""

    card = AgentCard(
        name="Scope Elicitation Agent",
        stage_key="scope",
        description="Elicits renovation goals, weights hidden conditions, and performs budget checks.",
        reads=["project.scope"],
        writes=["project.scope"],
        associated_skills=["scope-decomposition", "hidden-condition-surfacing", "pricing-ballpark"],
        associated_references=["RD-2"],
        search_grounding_enabled=False,
    )
