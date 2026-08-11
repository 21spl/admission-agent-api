# app/ai/schemas.py
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class StudentSupportChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(
        default_factory=list,
        description=(
            "Prior turns in this conversation, oldest first. The client "
            "resends the full history on every call — no server-side "
            "session/context is kept between requests, matching the "
            "stateless JWT pattern used elsewhere in the API."
        ),
    )
