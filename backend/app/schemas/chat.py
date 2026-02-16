"""Chat request/response schemas (per §10.1, §11)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    intent: str
    data: dict[str, Any] | None = None
    actions_taken: list[str] = []


class ChatHistoryEntry(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    intent: str | None = None
