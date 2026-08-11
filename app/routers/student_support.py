# app/routers/student_support.py
"""
Two entry points:
  - /support/public/chat/stream   — no auth, counsellor_agent only, no orchestrator
  - /support/chat/stream          — JWT-authenticated, full 4-agent + front desk workflow
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from llama_index.core.llms import ChatMessage as LlamaChatMessage, MessageRole
from llama_index.core.agent.workflow import AgentInput, AgentStream, ToolCall, ToolCallResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_student
from app.ai.config import initialize_ai_environment
from app.ai.agents.counsellor_agent import build_counsellor_agent
from app.ai.agents.orchestrator import build_authenticated_support_workflow
from app.ai.schemas.chat_support_schemas import StudentSupportChatRequest  




router = APIRouter(prefix="/support", tags=["support"])

_ROLE_MAP = {"user": MessageRole.USER, "assistant": MessageRole.ASSISTANT}

NO_APPLICATION_MESSAGE = (
    "You don't have an application yet. Please create your application first "
    "before using the support chat — once it's submitted, I can help with "
    "eligibility, documents, offers, and loan questions."
)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _static_message_stream(message: str):
    yield _sse("token", {"content": message})
    yield _sse("done", {"handled_by": None})


def _to_chat_history(history) -> list[LlamaChatMessage]:
    return [
        LlamaChatMessage(role=_ROLE_MAP[m.role], content=m.content)
        for m in history
        if m.role in _ROLE_MAP
    ]


# ============================= PUBLIC (no auth, no orchestrator) =============================

@router.post("/public/chat/stream")
async def public_chat_stream(payload: StudentSupportChatRequest) -> StreamingResponse:
    llm = initialize_ai_environment()
    counsellor_agent = build_counsellor_agent(llm)
    chat_history = _to_chat_history(payload.history)

    return StreamingResponse(
        _agent_event_generator(counsellor_agent, payload.message, chat_history),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _agent_event_generator(agent, user_msg: str, chat_history: list):
    """Streams a single FunctionAgent directly — no AgentWorkflow, so no
    agent_switch events (there's only ever one agent on the public side)."""
    handler = agent.run(user_msg=user_msg, chat_history=chat_history)

    try:
        async for event in handler.stream_events():
            if isinstance(event, AgentStream):
                if event.delta:
                    yield _sse("token", {"content": event.delta})
            elif isinstance(event, ToolCall):
                yield _sse("tool_call", {"agent": agent.name, "tool": event.tool_name})
            elif isinstance(event, ToolCallResult):
                yield _sse("tool_result", {"agent": agent.name, "tool": event.tool_name})

        await handler
        yield _sse("done", {"handled_by": agent.name})

    except Exception:
        yield _sse("error", {"message": "Support assistant is temporarily unavailable."})


# ============================= AUTHENTICATED (JWT, full orchestrator) =============================

@router.post("/chat/stream")
async def authenticated_chat_stream(
    payload: StudentSupportChatRequest,
    current_student=Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    if current_student.application_id is None:
        return StreamingResponse(
            _static_message_stream(NO_APPLICATION_MESSAGE),
            media_type="text/event-stream",
        )

    workflow = build_authenticated_support_workflow(db, current_student.application_id)
    chat_history = _to_chat_history(payload.history)

    return StreamingResponse(
        _workflow_event_generator(workflow, payload.message, chat_history),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _workflow_event_generator(workflow, user_msg: str, chat_history: list):
    handler = workflow.run(user_msg=user_msg, chat_history=chat_history)
    current_agent = None

    try:
        async for event in handler.stream_events():
            if isinstance(event, AgentInput) and event.current_agent_name != current_agent:
                current_agent = event.current_agent_name
                yield _sse("agent_switch", {"agent": current_agent})

            elif isinstance(event, AgentStream):
                if event.delta:
                    yield _sse("token", {"content": event.delta})

            elif isinstance(event, ToolCall):
                yield _sse("tool_call", {"agent": current_agent, "tool": event.tool_name})

            elif isinstance(event, ToolCallResult):
                yield _sse("tool_result", {"agent": current_agent, "tool": event.tool_name})

        await handler
        yield _sse("done", {"handled_by": current_agent})

    except Exception:
        yield _sse("error", {"message": "Support assistant is temporarily unavailable."})


        