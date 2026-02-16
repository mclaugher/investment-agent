"""Reports API router (per §10.1).

Endpoints for listing reports, report details, decision trails, and sector summaries.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import verify_token
from app.database import get_db
from app.models.reports import AgentDecision, AnalysisReport
from app.schemas.reports import (
    DecisionTrailNode,
    PaginatedReports,
    ReportDetail,
    ReportSummary,
    SectorLatestResponse,
)

router = APIRouter(prefix="/api/reports", tags=["reports"], dependencies=[Depends(verify_token)])


def _report_to_summary(r: AnalysisReport) -> ReportSummary:
    return ReportSummary(
        id=r.id,
        agent_name=r.agent_name,
        agent_role=r.agent_role,
        report_type=r.report_type,
        symbol=r.symbol,
        sector=r.sector,
        title=r.title,
        recommendation=r.recommendation,
        confidence=r.confidence,
        created_at=r.created_at,
    )


@router.get("", response_model=PaginatedReports)
async def list_reports(
    agent: str | None = None,
    sector: str | None = None,
    symbol: str | None = None,
    type: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List reports with filters (per §10.1)."""
    query = select(AnalysisReport)
    count_query = select(func.count(AnalysisReport.id))

    if agent:
        query = query.where(AnalysisReport.agent_name == agent)
        count_query = count_query.where(AnalysisReport.agent_name == agent)
    if sector:
        query = query.where(AnalysisReport.sector == sector)
        count_query = count_query.where(AnalysisReport.sector == sector)
    if symbol:
        query = query.where(AnalysisReport.symbol == symbol)
        count_query = count_query.where(AnalysisReport.symbol == symbol)
    if type:
        query = query.where(AnalysisReport.report_type == type)
        count_query = count_query.where(AnalysisReport.report_type == type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * limit
    result = await db.execute(
        query.order_by(AnalysisReport.created_at.desc()).offset(offset).limit(limit)
    )
    reports = result.scalars().all()

    return PaginatedReports(
        items=[_report_to_summary(r) for r in reports],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/latest-by-sector", response_model=list[SectorLatestResponse])
async def get_latest_by_sector(db: AsyncSession = Depends(get_db)):
    """Latest sector summaries grouped by sector (per §10.1)."""
    # Get all distinct sectors from existing reports
    sector_result = await db.execute(
        select(AnalysisReport.sector)
        .where(AnalysisReport.sector.is_not(None))
        .distinct()
    )
    sectors = [row[0] for row in sector_result.fetchall()]

    responses = []
    for sector_name in sectors:
        result = await db.execute(
            select(AnalysisReport)
            .where(AnalysisReport.sector == sector_name)
            .order_by(AnalysisReport.created_at.desc())
            .limit(5)
        )
        reports = result.scalars().all()
        responses.append(SectorLatestResponse(
            sector=sector_name,
            reports=[_report_to_summary(r) for r in reports],
        ))

    return responses


@router.get("/decision-trail/{decision_id}", response_model=list[DecisionTrailNode])
async def get_decision_trail(decision_id: int, db: AsyncSession = Depends(get_db)):
    """Decision reasoning chain from CEO down to analysts (per §10.1)."""
    # Get the decision
    decision_result = await db.execute(
        select(AgentDecision).where(AgentDecision.id == decision_id)
    )
    decision = decision_result.scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    # Get supporting reports
    supporting_ids = decision.supporting_report_ids or []
    if not supporting_ids:
        return []

    result = await db.execute(
        select(AnalysisReport).where(AnalysisReport.id.in_(supporting_ids))
    )
    reports = result.scalars().all()
    reports_by_id = {r.id: r for r in reports}

    # Build trail nodes
    async def build_node(report: AnalysisReport) -> DecisionTrailNode:
        # Find children reports
        child_result = await db.execute(
            select(AnalysisReport).where(AnalysisReport.parent_report_id == report.id)
        )
        children = child_result.scalars().all()

        child_nodes = []
        for child in children:
            child_nodes.append(await build_node(child))

        return DecisionTrailNode(
            report_id=report.id,
            agent_name=report.agent_name,
            agent_role=report.agent_role,
            report_type=report.report_type,
            title=report.title,
            content=report.content,
            recommendation=report.recommendation,
            confidence=report.confidence,
            children=child_nodes,
        )

    trail = []
    for report in reports:
        trail.append(await build_node(report))

    return trail


@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    """Full report detail (per §10.1)."""
    result = await db.execute(
        select(AnalysisReport).where(AnalysisReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportDetail(
        id=report.id,
        agent_name=report.agent_name,
        agent_role=report.agent_role,
        report_type=report.report_type,
        symbol=report.symbol,
        sector=report.sector,
        title=report.title,
        content=report.content,
        recommendation=report.recommendation,
        confidence=report.confidence,
        key_metrics=report.key_metrics,
        parent_report_id=report.parent_report_id,
        created_at=report.created_at,
    )
