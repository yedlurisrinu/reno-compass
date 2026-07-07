import datetime

from agents.scope import ScopeAgent
from domain.dossier import ConversationTurn, Dossier, DossierEnvelope, ProjectBody


def test_scope_stated_parameter_role_filtering(monkeypatch):
    """Verifies that stated parameters are extracted ONLY from user turns."""
    monkeypatch.setenv("MOCK_VERTEX_AI", "true")
    # 1. Create a dossier with a mixed conversation
    dossier = Dossier(
        envelope=DossierEnvelope(
            dossier_id="test_filter",
            schema_version="1.0.0",
            created_at=datetime.datetime.utcnow(),
            last_updated_at=datetime.datetime.utcnow(),
            origin="fresh",
            current_stage="scope",
        ),
        project=ProjectBody(),
    )

    agent = ScopeAgent(dossier)
    stage_obj = agent._create_default_stage_object("scope")
    dossier.project.scope = stage_obj

    # 2. Append turns where Agent mentions standard numbers but user states different numbers
    stage_obj.conversation = [
        ConversationTurn(
            role="agent",
            text="A standard ballpark bathroom remodel budget is $20000 and zipcode is 94043.",
            at=datetime.datetime.utcnow(),
        ),
        ConversationTurn(
            role="user",
            text="Actually, my zipcode is 95120 and my budget target is $15000.",
            at=datetime.datetime.utcnow(),
        ),
    ]

    # 3. Trigger extraction pass
    agent.extract_and_update_stage_dossier()

    # Assert that the extracted parameters match the USER turns, NOT the AGENT suggestions
    assert stage_obj.budget_target == 15000.0
    assert stage_obj.property_context.zipcode == "95120"
