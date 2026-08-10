# app/ai/student_support/agents/offer_agent.py
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import QueryEngineTool
from llama_index.llms.google_genai import GoogleGenAI

from app.ai.tools.offer_query_tools import build_offer_query_tools
from app.ai.rag.query_engines import offer_policy_engine, branch_eligibility_engine


def build_offer_agent(llm: GoogleGenAI, db, application_id) -> FunctionAgent:
    tools = [
        *build_offer_query_tools(db, application_id),
        QueryEngineTool.from_defaults(
            query_engine=offer_policy_engine,
            name="offer_shortlisting_policy_lookup",
            description="Search official policy on offer generation, shortlisting rounds, tie-breaking, and response handling.",
        ),
        QueryEngineTool.from_defaults(
            query_engine=branch_eligibility_engine,
            name="branch_eligibility_policy_lookup",
            description="Search official branch/program eligibility criteria and cutoff rules.",
        ),
    ]

    return FunctionAgent(
        name="offer_agent",
        description="Answers questions about the logged-in student's offers, branch preferences, and shortlisting mechanics.",
        system_prompt=(
            "You are the offer and shortlisting specialist for a university "
            "admissions helpdesk. You help the logged-in student understand "
            "their own offers, branch preferences, and how shortlisting/rounds "
            "work — using only the tools provided.\n\n"
            "Rules:\n"
            "- Ground shortlisting mechanics and eligibility rules in the "
            "lookup tools — never invent tie-breaking or cutoff rules.\n"
            "- Never predict or speculate about future offers or admission "
            "chances — only report actual recorded offers and documented policy.\n"
            "- If asked about documents or loans, hand off to the appropriate specialist."
        ),
        llm=llm,
        tools=tools,
        can_handoff_to=["application_agent", "document_agent", "loan_agent", "root_agent"],
    )