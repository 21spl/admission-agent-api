# app/ai/student_support/agents/counsellor_agent.py
"""
Public-facing agent — no authentication, no DB access, static policy
documents only. This is the entire public interface: one agent, no
handoff graph needed since there's nothing to route to.
"""

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import QueryEngineTool
from llama_index.llms.google_genai import GoogleGenAI

from app.ai.rag.query_engines import (
    branch_eligibility_engine,
    document_validation_policy_engine,
    loan_policy_engine,
    offer_policy_engine,
)


def build_counsellor_agent(llm: GoogleGenAI) -> FunctionAgent:
    tools = [
        QueryEngineTool.from_defaults(
            query_engine=loan_policy_engine,
            name="loan_policy_lookup",
            description="Search official education loan scheme policy — eligibility, interest rates, documentation, process.",
        ),
        QueryEngineTool.from_defaults(
            query_engine=offer_policy_engine,
            name="offer_shortlisting_policy_lookup",
            description="Search official policy on offer generation, shortlisting rounds, tie-breaking, and response handling.",
        ),
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
        name="counsellor_agent",
        description="Public admissions counsellor answering general policy questions for prospective and current applicants.",
        system_prompt=(
            "You are the public admissions counsellor for a university helpdesk. "
            "Visitors may be prospective applicants who haven't applied yet, or "
            "current applicants asking general policy questions.\n\n"
            "Rules:\n"
            "- Ground every answer in the policy lookup tools — never state a "
            "rule, fee, deadline, or number from general knowledge.\n"
            "- If a tool doesn't cover the question, say so plainly and direct "
            "the visitor to contact the admissions office. Do not guess.\n"
            "- You have NO access to any individual's personal application, "
            "documents, offers, or loan status. If asked about 'my application' "
            "or anything requiring a login, explain that personal account "
            "questions require logging in to the student portal.\n"
            "- Never predict or speculate about someone's chances of admission "
            "to a specific branch — that is out of scope for this assistant."
        ),
        llm=llm,
        tools=tools,
    )
