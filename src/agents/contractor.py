"""Contractor Validation Agent.

Audits contractor quotes against the required-coverage rubric and flags
potential contractor corner-cutting patterns.
"""

from agents.base import AgentCard, BaseAgent


class ContractorAgent(BaseAgent):
    """Contractor stage agent reviewing bids and validating itemized task coverage."""

    card = AgentCard(
        name="Contractor Bid Auditor Agent",
        stage_key="contractor_validation",
        description="Audits contractor bids for scope omissions, hidden costs, and potential corner-cutting behaviors.",
        reads=[
            "project.scope",
            "project.design",
            "project.safety_permit",
            "project.materials",
            "project.contractor_validation",
        ],
        writes=["project.contractor_validation"],
        # safety-tier-classification is the shared spine, re-invoked to confirm the
        # quote covers the licensed trades the work needs (CL-20).
        associated_skills=[
            "quote-audit",
            "coverage-audit",
            "corner-cutting",
            "safety-tier-classification",
        ],
        # RD-5 audit rubric + RD-2/RD-3 bands for the suspiciously-low-bid cross-check
        associated_references=["RD-5", "RD-2", "RD-3"],
        search_grounding_enabled=False,
    )
