"""Chat API router (per §10.1, §11).

Natural language interface with intent classification and routing.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from app.api.auth import verify_token
from app.schemas.chat import ChatHistoryEntry, ChatRequest, ChatResponse
from app.services.chat_router import classify_intent, route_query

router = APIRouter(prefix="/api/chat", tags=["chat"], dependencies=[Depends(verify_token)])

# In-memory chat history (would use Redis or DB in production)
_chat_history: list[dict] = []


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Natural language interface (per §10.1, §11)."""
    # Classify intent
    intent = await classify_intent(request.message)

    # Route to handler
    result = await route_query(request.message, intent)

    # Store in history
    now = datetime.now(timezone.utc)
    _chat_history.append({
        "role": "user",
        "content": request.message,
        "timestamp": now,
        "intent": intent,
    })
    _chat_history.append({
        "role": "assistant",
        "content": result.get("response", ""),
        "timestamp": now,
        "intent": intent,
    })

    return ChatResponse(
        response=result.get("response", ""),
        intent=intent,
        data=result.get("data"),
        actions_taken=result.get("actions_taken", []),
    )


@router.get("/history", response_model=list[ChatHistoryEntry])
async def get_chat_history(limit: int = Query(50, ge=1, le=200)):
    """Recent chat history (per §10.1)."""
    entries = _chat_history[-limit:]
    return [
        ChatHistoryEntry(
            role=e["role"],
            content=e["content"],
            timestamp=e["timestamp"],
            intent=e.get("intent"),
        )
        for e in entries
    ]
