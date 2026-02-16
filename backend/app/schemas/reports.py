"""Report request/response schemas (per §10.1)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ReportSummary(BaseModel):
    id: int
    agent_name: str
    agent_role: str
    report_type: str
    symbol: str | None
    sector: str | None
    title: str
    recommendation: str | None
    confidence: int | None
    created_at: datetime


class ReportDetail(BaseModel):
    id: int
    agent_name: str
    agent_role: str
    report_type: str
    symbol: str | None
    sector: str | None
    title: str
    content: str
    recommendation: str | None
    confidence: int | None
    key_metrics: dict[str, Any] | None
    parent_report_id: int | None
    created_at: datetime


class PaginatedReports(BaseModel):
    items: list[ReportSummary]
    total: int
    page: int
    limit: int


class DecisionTrailNode(BaseModel):
    report_id: int
    agent_name: str
    agent_role: str
    report_type: str
    title: str
    content: str
    recommendation: str | None
    confidence: int | None
    children: list["DecisionTrailNode"] = []


class SectorLatestResponse(BaseModel):
    sector: str
    reports: list[ReportSummary]
