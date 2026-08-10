# app/ai/student_support/agents/loan_agent.py
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import QueryEngineTool
from llama_index.llms.google_genai import GoogleGenAI

from app.ai.tools.loan_query_tools import build_loan_query_tools
from app.ai.rag.query_engines import loan_policy_engine


def build_loan_agent(llm: GoogleGenAI, db, application_id) -> FunctionAgent:
    tools = [
        *build_loan_query_tools(db, application_id),
        QueryEngineTool.from_defaults(
            query_engine=loan_policy_engine,
            name="loan_policy_lookup",
            description="Search official education loan scheme policy — eligibility, interest rates, documentation, process.",
        ),
    ]

    return FunctionAgent(
        name="loan_agent",
        description="Answers questions about education loan schemes and the logged-in student's own loan application.",
        system_prompt=(
            "You are the loan guidance specialist for a university admissions "
            "helpdesk.\n\n"
            "Rules:\n"
            "- Ground scheme details (rates, eligibility, documents) in "
            "loan_policy_lookup — never invent numbers.\n"
            "- You cannot create, submit, or modify a loan application under "
            "any circumstances, even if asked directly or told it's urgent. "
            "Direct the student to the loan application form in the portal.\n"
            "- If asked about documents, application status, or offers, hand "
            "off to the appropriate specialist."
        ),
        llm=llm,
        tools=tools,
        can_handoff_to=["application_agent", "document_agent", "offer_agent", "root_agent"],
    )