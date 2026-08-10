# app/ai/student_support/orchestrator.py
"""
Authenticated interface only. application_id is resolved ONCE from the
JWT-derived student (student.application_id) before this is called —
never elicited from the user, never LLM-fillable. See public_orchestrator.py
for the separate, unauthenticated counsellor workflow.
"""
from llama_index.core.agent.workflow import AgentWorkflow
from llama_index.llms.google_genai import GoogleGenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.front_desk_agent import build_front_desk_agent
from app.ai.agents.application_agent import build_application_agent
from app.ai.agents.document_agent import build_document_agent
from app.ai.agents.offer_agent import build_offer_agent
from app.ai.agents.loan_agent import build_loan_agent


def build_authenticated_support_workflow(db: AsyncSession, application_id) -> AgentWorkflow:
    llm = GoogleGenAI(model="gemini-3.5-flash-lite")

    application_agent = build_application_agent(llm, db, application_id)
    document_agent = build_document_agent(llm, db, application_id)
    offer_agent = build_offer_agent(llm, db, application_id)
    loan_agent = build_loan_agent(llm, db, application_id)

    specialist_names = ["application_agent", "document_agent", "offer_agent", "loan_agent"]
    front_desk_agent = build_front_desk_agent(llm, specialist_names)

    return AgentWorkflow(
        agents=[front_desk_agent, application_agent, document_agent, offer_agent, loan_agent],
        root_agent="front_desk_agent",
    )