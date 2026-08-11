# app/ai/student_support/agents/document_agent.py
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import QueryEngineTool
from llama_index.llms.google_genai import GoogleGenAI

from app.ai.rag.query_engines import document_validation_policy_engine
from app.ai.tools.document_query_tools import build_document_query_tools


def build_document_agent(llm: GoogleGenAI, db, application_id) -> FunctionAgent:
    tools = [
        *build_document_query_tools(db, application_id),
        QueryEngineTool.from_defaults(
            query_engine=document_validation_policy_engine,
            name="document_policy_lookup",
            description="Search official policy on required documents and verification procedures.",
        ),
    ]

    return FunctionAgent(
        name="document_agent",
        description="Answers questions about the logged-in student's uploaded documents and validation status.",
        system_prompt=(
            "You are the document specialist for a university admissions helpdesk. "
            "You help the logged-in student understand what documents they need, "
            "their upload/validation status, and any validation issues — using "
            "only the tools provided.\n\n"
            "Rules:\n"
            "- Ground requirements and procedures in document_policy_lookup — "
            "never guess what's required.\n"
            "- If asked about application status generally, offers, or loans, "
            "hand off to the appropriate specialist."
        ),
        llm=llm,
        tools=tools,
        can_handoff_to=["application_agent", "offer_agent", "loan_agent", "root_agent"],
    )
