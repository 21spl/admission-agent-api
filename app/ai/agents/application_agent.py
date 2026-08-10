# app/ai/student_support/agents/application_agent.py
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import QueryEngineTool
from llama_index.llms.google_genai import GoogleGenAI

from app.ai.tools.application_query_tools import build_application_query_tools
from app.ai.rag.query_engines import document_validation_policy_engine, branch_eligibility_engine


def build_application_agent(llm: GoogleGenAI, db, application_id) -> FunctionAgent:
    tools = [
        *build_application_query_tools(db, application_id),
        QueryEngineTool.from_defaults(
            query_engine=document_validation_policy_engine,
            name="document_policy_lookup",
            description="Search official policy on required documents and verification procedures.",
        ),
        QueryEngineTool.from_defaults(
            query_engine=branch_eligibility_engine,
            name="branch_eligibility_policy_lookup",
            description="Search official branch/program eligibility criteria and cutoff rules.",
        ),
    ]

    return FunctionAgent(
        name="application_agent",
        description="Answers questions about the logged-in student's application status and history.",
        system_prompt=(
            "You are the application status specialist for a university admissions "
            "helpdesk. You answer questions about the logged-in student's own "
            "application status and status history, using only the tools provided.\n\n"
            "Rules:\n"
            "- Ground policy claims in the lookup tools — never invent a rule or number.\n"
            "- Never predict admission chances or outcomes.\n"
            "- If the question is about documents specifically or loans/offers, "
            "hand off to the appropriate specialist rather than guessing."
        ),
        llm=llm,
        tools=tools,
        can_handoff_to=["document_agent", "offer_agent", "loan_agent", "root_agent"],
    )