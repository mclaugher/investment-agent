"""Agent request/response schemas (per §10.1)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AgentSummary(BaseModel):
    name: str
    role: str
    description: str
    status: str  # "idle", "running", "error"
    last_run: datetime | None
    next_scheduled: datetime | None
    reports_count: int


class AgentDetail(BaseModel):
    name: str
    role: str
    description: str
    status: str
    last_run: datetime | None
    next_scheduled: datetime | None
    tools: list[str]
    recent_reports: list[dict[str, Any]]


class AgentQueryRequest(BaseModel):
    question: str


class AgentQueryResponse(BaseModel):
    agent_name: str
    response: str
    report_ids: list[int] = []
