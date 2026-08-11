# tests/test_track_b/test_agents.py
"""
These test agent CONSTRUCTION and tool scoping — not full LLM
conversations, which would be slow, nondeterministic, and cost real API
calls on every test run. The critical thing to verify here is the
identity-binding discipline: agents must never expose application_id
as an LLM-fillable parameter.
"""
import pytest
import inspect

from conftest import test_student


async def _get_student_token(client):
    response = await client.post(
        "/auth/student/login",
        json={
            "email": "test_{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]

def test_application_agent_tools_never_expose_application_id_parameter(db_session):
    """
    Regression test for the exact bug caught earlier in this project:
    every tool must have application_id closure-bound, never as a
    parameter the LLM can fill in.
    """
    from app.ai.agents.application_agent import build_application_agent
    from app.ai.config import initialize_ai_environment
    import uuid

    llm = initialize_ai_environment()
    agent = build_application_agent(llm, db_session, uuid.uuid4())

    for tool in agent.tools:
        schema_props = tool.metadata.get_parameters_dict().get("properties", {})
        assert "application_id" not in schema_props, (
            f"Tool '{tool.metadata.name}' exposes application_id as an "
            f"LLM-fillable parameter — this must be closure-bound instead."
        )


def test_all_four_authenticated_agents_have_no_application_id_leakage(db_session):
    from app.ai.config import initialize_ai_environment
    from app.ai.agents.application_agent import build_application_agent
    from app.ai.agents.document_agent import build_document_agent
    from app.ai.agents.offer_agent import build_offer_agent
    from app.ai.agents.loan_agent import build_loan_agent
    import uuid

    llm = initialize_ai_environment()
    application_id = uuid.uuid4()
    agents = [
        build_application_agent(llm, db_session, application_id),
        build_document_agent(llm, db_session, application_id),
        build_offer_agent(llm, db_session, application_id),
        build_loan_agent(llm, db_session, application_id),
    ]
    for agent in agents:
        for tool in agent.tools:
            schema_props = tool.metadata.get_parameters_dict().get("properties", {})
            assert "application_id" not in schema_props


def test_counsellor_agent_has_no_db_tools():
    """
    Regression test for the public/authenticated boundary: the counsellor
    agent must ONLY have QueryEngineTools (policy lookups), never a
    FunctionTool wrapping a DB service call.
    """
    from app.ai.agents.counsellor_agent import build_counsellor_agent
    from app.ai.config import initialize_ai_environment
    from llama_index.core.tools import QueryEngineTool

    llm = initialize_ai_environment()
    agent = build_counsellor_agent(llm)

    for tool in agent.tools:
        assert isinstance(tool, QueryEngineTool), (
            f"counsellor_agent has a non-QueryEngineTool tool: {tool.metadata.name} — "
            f"public interface must never have DB access."
        )



        


        