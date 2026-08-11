# app/ai/agents/front_desk_agent.py
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.google_genai import GoogleGenAI


def build_front_desk_agent(
    llm: GoogleGenAI, specialist_names: list[str]
) -> FunctionAgent:
    return FunctionAgent(
        name="front_desk_agent",
        description="Greets the student and routes their question to the right specialist.",
        system_prompt=(
            "You are the front desk of a university admissions helpdesk, "
            "speaking with a logged-in, verified student.\n\n"
            f"Available specialists: {', '.join(specialist_names)}.\n\n"
            "Classify the student's question and hand off to exactly one "
            "specialist:\n"
            "- application_agent: application status, status history\n"
            "- document_agent: uploaded documents, validation issues, requirements\n"
            "- offer_agent: offers received, branch preferences, shortlisting/rounds\n"
            "- loan_agent: education loan status and scheme information\n\n"
            "Do not answer substantive questions yourself — you have no tools. "
            "If the question spans multiple topics, hand off to the primary one; "
            "specialists can hand off to each other directly as the conversation "
            "continues, so you generally only need to route once per new topic."
        ),
        llm=llm,
        tools=[],
        can_handoff_to=specialist_names,
    )
