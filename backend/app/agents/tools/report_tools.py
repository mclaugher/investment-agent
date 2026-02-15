"""Report tools for agent use (per §6.7).

CRUD operations for AnalysisReport and AgentDecision.
All tools are @tool decorated, stateless, and return typed dicts.
"""

from datetime import datetime, timezone

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session
from app.models.reports import AgentDecision, AnalysisReport


@tool
async def save_analysis_report(
    agent_name: str,
    agent_role: str,
    report_type: str,
    title: str,
    content: str,
    symbol: str | None = None,
    sector: str | None = None,
    recommendation: str | None = None,
    confidence: int | None = None,
    key_metrics: dict | None = None,
    parent_report_id: int | None = None,
) -> dict:
    """Save an analysis report to the database. Returns: {report_id: int}"""
    async with async_session() as session:
        async with session.begin():
            report = AnalysisReport(
                agent_name=agent_name,
                agent_role=agent_role,
                report_type=report_type,
                title=title,
                content=content,
                symbol=symbol,
                sector=sector,
                recommendation=recommendation,
                confidence=confidence,
                key_metrics=key_metrics or {},
                parent_report_id=parent_report_id,
            )
            session.add(report)
            await session.flush()
            return {"report_id": report.id}


@tool
async def get_reports_for_symbol(symbol: str, limit: int = 10) -> list[dict]:
    """Get most recent analysis reports for a symbol, ordered by created_at desc."""
    async with async_session() as session:
        result = await session.execute(
            select(AnalysisReport)
            .where(AnalysisReport.symbol == symbol)
            .order_by(AnalysisReport.created_at.desc())
            .limit(limit)
        )
        reports = result.scalars().all()
        return [
            {
                "id": r.id,
                "agent_name": r.agent_name,
                "agent_role": r.agent_role,
                "report_type": r.report_type,
                "title": r.title,
                "content": r.content[:2000],  # Truncate for context window
                "recommendation": r.recommendation,
                "confidence": r.confidence,
                "key_metrics": r.key_metrics,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ]


@tool
async def get_reports_by_agent(agent_name: str, limit: int = 10) -> list[dict]:
    """Get most recent reports from a specific agent."""
    async with async_session() as session:
        result = await session.execute(
            select(AnalysisReport)
            .where(AnalysisReport.agent_name == agent_name)
            .order_by(AnalysisReport.created_at.desc())
            .limit(limit)
        )
        reports = result.scalars().all()
        return [
            {
                "id": r.id,
                "report_type": r.report_type,
                "symbol": r.symbol,
                "sector": r.sector,
                "title": r.title,
                "recommendation": r.recommendation,
                "confidence": r.confidence,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ]


@tool
async def get_decision_trail(decision_id: int) -> dict:
    """Get the full chain of reports that supported a decision.
    Follows parent_report_id relationships from CEO report down to analyst reports.
    Returns: {decision, report_chain}"""
    async with async_session() as session:
        # Get decision
        dec_result = await session.execute(
            select(AgentDecision).where(AgentDecision.id == decision_id)
        )
        decision = dec_result.scalar_one_or_none()
        if not decision:
            return {"error": f"Decision {decision_id} not found"}

        decision_dict = {
            "id": decision.id,
            "decision_type": decision.decision_type,
            "symbol": decision.symbol,
            "action": decision.action,
            "recommended_shares": float(decision.recommended_shares) if decision.recommended_shares else None,
            "recommended_amount": float(decision.recommended_amount) if decision.recommended_amount else None,
            "reasoning": decision.reasoning,
            "confidence": decision.confidence,
            "status": decision.status,
            "supporting_report_ids": decision.supporting_report_ids,
        }

        # Build report chain from supporting report IDs
        report_chain = []
        report_ids = decision.supporting_report_ids or []

        for report_id in report_ids:
            report_result = await session.execute(
                select(AnalysisReport)
                .where(AnalysisReport.id == report_id)
                .options(selectinload(AnalysisReport.children))
            )
            report = report_result.scalar_one_or_none()
            if report:
                entry = {
                    "level": report.agent_role,
                    "report": {
                        "id": report.id,
                        "agent_name": report.agent_name,
                        "report_type": report.report_type,
                        "title": report.title,
                        "content": report.content[:1000],
                        "recommendation": report.recommendation,
                        "confidence": report.confidence,
                        "symbol": report.symbol,
                        "sector": report.sector,
                    },
                }
                # Include child reports recursively (one level deep)
                if report.children:
                    entry["supporting_reports"] = [
                        {
                            "id": c.id,
                            "agent_name": c.agent_name,
                            "agent_role": c.agent_role,
                            "title": c.title,
                            "recommendation": c.recommendation,
                            "confidence": c.confidence,
                        }
                        for c in report.children
                    ]
                report_chain.append(entry)

        return {"decision": decision_dict, "report_chain": report_chain}


@tool
async def get_latest_sector_reports(sector: str) -> dict:
    """Get the latest analysis reports for all stocks in a sector.
    Returns: {sector, reports}"""
    async with async_session() as session:
        result = await session.execute(
            select(AnalysisReport)
            .where(AnalysisReport.sector == sector)
            .order_by(AnalysisReport.created_at.desc())
            .limit(50)
        )
        reports = result.scalars().all()

        # Group by symbol, keep latest per symbol
        seen_symbols: set[str] = set()
        output = []
        for r in reports:
            key = r.symbol or r.agent_name
            if key not in seen_symbols:
                seen_symbols.add(key)
                output.append({
                    "symbol": r.symbol,
                    "report_type": r.report_type,
                    "recommendation": r.recommendation,
                    "confidence": r.confidence,
                    "summary": r.content[:500],
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                })

        return {"sector": sector, "reports": output}
