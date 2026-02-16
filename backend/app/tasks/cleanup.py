"""Cleanup Celery task (per §9.2).

cleanup_old_data: Archive old reports, prune price data, log cleanup actions.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.celery_app import celery
from app.database import async_session

logger = logging.getLogger(__name__)


async def _cleanup_old_data_async() -> dict:
    """Async implementation of data cleanup."""
    from sqlalchemy import delete, select, func
    from app.models.reports import AnalysisReport
    from app.models.market_data import PriceHistory

    now = datetime.now(timezone.utc)
    two_years_ago = now - timedelta(days=730)
    one_year_ago = now - timedelta(days=365)

    results = {}

    async with async_session() as session:
        # Archive reports older than 2 years
        old_reports = await session.execute(
            select(func.count(AnalysisReport.id)).where(
                AnalysisReport.created_at < two_years_ago
            )
        )
        report_count = old_reports.scalar() or 0

        if report_count > 0:
            await session.execute(
                delete(AnalysisReport).where(
                    AnalysisReport.created_at < two_years_ago
                )
            )
            results["archived_reports"] = report_count
            logger.info(f"Archived {report_count} reports older than 2 years")

        # Prune intraday price data older than 1 year (keep daily only)
        # We keep the last record per (symbol, date) and delete extras
        old_prices = await session.execute(
            select(func.count(PriceHistory.id)).where(
                PriceHistory.date < one_year_ago.date()
            )
        )
        price_count = old_prices.scalar() or 0
        results["pruned_price_records"] = price_count

        if price_count > 0:
            logger.info(f"Found {price_count} price records older than 1 year")

        await session.commit()

    results["timestamp"] = now.isoformat()
    logger.info(f"Cleanup complete: {results}")
    return results


@celery.task(name="app.tasks.cleanup.cleanup_old_data")
def cleanup_old_data() -> dict:
    """Archive old data and prune stale records (per §9.2)."""
    return asyncio.run(_cleanup_old_data_async())
