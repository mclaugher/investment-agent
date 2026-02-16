"""Agents API router (per §10.1).

Endpoints for agent listing, detail, triggering, and querying.
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import verify_token
from app.database import get_db
from app.models.reports import AnalysisReport
from app.schemas.agents import AgentDetail, AgentQueryRequest, AgentQueryResponse, AgentSummary

router = APIRouter(prefix="/api/agents", tags=["agents"], dependencies=[Depends(verify_token)])

# Agent registry — static metadata loaded from org_config.json
_AGENT_REGISTRY: list[dict] | None = None


def _load_agent_registry() -> list[dict]:
    """Load agent metadata from org_config.json."""
    global _AGENT_REGISTRY
    if _AGENT_REGISTRY is None:
        import os
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "org_config.json")
        config_path = os.path.normpath(config_path)
        try:
            with open(config_path) as f:
                config = json.load(f)
            _AGENT_REGISTRY = config.get("agents", [])
        except FileNotFoundError:
            _AGENT_REGISTRY = []
    return _AGENT_REGISTRY


@router.get("", response_model=list[AgentSummary])
async def list_agents(db: AsyncSession = Depends(get_db)):
    """All agents with status and last run (per §10.1)."""
    registry = _load_agent_registry()

    agents = []
    for agent_meta in registry:
        name = agent_meta["name"]

        # Get last report time as proxy for last run
        result = await db.execute(
            select(AnalysisReport.created_at)
            .where(AnalysisReport.agent_name == name)
            .order_by(AnalysisReport.created_at.desc())
            .limit(1)
        )
        last_run_row = result.first()
        last_run = last_run_row[0] if last_run_row else None

        # Count reports
        count_result = await db.execute(
            select(func.count(AnalysisReport.id)).where(AnalysisReport.agent_name == name)
        )
        reports_count = count_result.scalar() or 0

        agents.append(AgentSummary(
            name=name,
            role=agent_meta.get("role", ""),
            description=agent_meta.get("description", ""),
            status="idle",
            last_run=last_run,
            next_scheduled=None,
            reports_count=reports_count,
        ))

    return agents


@router.get("/{name}", response_model=AgentDetail)
async def get_agent(name: str, db: AsyncSession = Depends(get_db)):
    """Single agent detail with recent reports (per §10.1)."""
    registry = _load_agent_registry()
    agent_meta = next((a for a in registry if a["name"] == name), None)

    if not agent_meta:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    # Get last run
    last_result = await db.execute(
        select(AnalysisReport.created_at)
        .where(AnalysisReport.agent_name == name)
        .order_by(AnalysisReport.created_at.desc())
        .limit(1)
    )
    last_run_row = last_result.first()
    last_run = last_run_row[0] if last_run_row else None

    # Get recent reports
    reports_result = await db.execute(
        select(AnalysisReport)
        .where(AnalysisReport.agent_name == name)
        .order_by(AnalysisReport.created_at.desc())
        .limit(10)
    )
    reports = reports_result.scalars().all()

    recent_reports = [
        {
            "id": r.id,
            "title": r.title,
            "report_type": r.report_type,
            "symbol": r.symbol,
            "recommendation": r.recommendation,
            "confidence": r.confidence,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reports
    ]

    return AgentDetail(
        name=name,
        role=agent_meta.get("role", ""),
        description=agent_meta.get("description", ""),
        status="idle",
        last_run=last_run,
        next_scheduled=None,
        tools=agent_meta.get("tools", []),
        recent_reports=recent_reports,
    )


@router.post("/trigger/{name}")
async def trigger_agent(name: str):
    """Manually trigger an agent or team run (per §10.1)."""
    from app.tasks.analysis_cycle import run_full_analysis, run_targeted_analysis

    # Map agent names to task triggers
    if name in ("orchestrator", "ceo_agent"):
        task = run_full_analysis.delay()
        return {"status": "triggered", "task_id": task.id, "agent": name}

    # For sector teams, run targeted analysis
    from scripts.seed_universe import STOCK_UNIVERSE
    for sector, symbols in STOCK_UNIVERSE.items():
        if name == f"{sector}_supervisor" or name == f"{sector}_team":
            task = run_targeted_analysis.delay(symbols[0])
            return {"status": "triggered", "task_id": task.id, "agent": name, "sector": sector}

    raise HTTPException(status_code=404, detail=f"Cannot trigger agent '{name}'")


@router.post("/query", response_model=AgentQueryResponse)
async def query_agent(request: AgentQueryRequest):
    """Route a question to the appropriate agent (per §10.1)."""
    from app.services.chat_router import classify_intent, route_query

    intent = await classify_intent(request.question)
    response = await route_query(request.question, intent)

    return AgentQueryResponse(
        agent_name=response.get("agent", "system"),
        response=response.get("response", ""),
        report_ids=response.get("report_ids", []),
    )
