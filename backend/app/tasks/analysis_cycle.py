"""Analysis cycle Celery tasks (per §9.2).

run_full_analysis: Execute the full agent graph.
run_targeted_analysis: Run only one sector team + CIO + CEO for a symbol.
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.celery_app import celery

logger = logging.getLogger(__name__)


async def _run_full_analysis_async() -> dict:
    """Async implementation of full analysis cycle."""
    from app.agents.orchestrator import build_fund_graph

    logger.info("Starting full analysis cycle")
    start_time = datetime.now(timezone.utc)

    try:
        graph = build_fund_graph()
        result = await graph.ainvoke(
            {"messages": [{"role": "user", "content": "Run full analysis cycle for all sectors."}]},
        )

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(f"Full analysis cycle completed in {elapsed:.1f}s")

        return {
            "status": "completed",
            "elapsed_seconds": elapsed,
            "timestamp": start_time.isoformat(),
        }

    except Exception as e:
        logger.error(f"Full analysis cycle failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": start_time.isoformat(),
        }


async def _run_targeted_analysis_async(symbol: str) -> dict:
    """Async implementation of targeted analysis."""
    from scripts.seed_universe import STOCK_UNIVERSE
    from app.agents.orchestrator import build_targeted_graph

    # Find which sector this symbol belongs to
    sector = None
    for sec_name, symbols in STOCK_UNIVERSE.items():
        if symbol.upper() in symbols:
            sector = sec_name
            break

    if not sector:
        return {"status": "error", "error": f"Symbol {symbol} not found in stock universe"}

    logger.info(f"Starting targeted analysis for {symbol} (sector: {sector})")
    start_time = datetime.now(timezone.utc)

    try:
        graph = build_targeted_graph(sector)
        result = await graph.ainvoke(
            {"messages": [{"role": "user", "content": f"Run targeted analysis for {symbol} in the {sector} sector."}]},
        )

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(f"Targeted analysis for {symbol} completed in {elapsed:.1f}s")

        return {
            "status": "completed",
            "symbol": symbol,
            "sector": sector,
            "elapsed_seconds": elapsed,
            "timestamp": start_time.isoformat(),
        }

    except Exception as e:
        logger.error(f"Targeted analysis for {symbol} failed: {e}")
        return {
            "status": "error",
            "symbol": symbol,
            "error": str(e),
            "timestamp": start_time.isoformat(),
        }


@celery.task(name="app.tasks.analysis_cycle.run_full_analysis")
def run_full_analysis() -> dict:
    """Execute the full agent graph end-to-end (per §9.2)."""
    return asyncio.run(_run_full_analysis_async())


@celery.task(name="app.tasks.analysis_cycle.run_targeted_analysis")
def run_targeted_analysis(symbol: str) -> dict:
    """Run analysis for a single symbol through its sector team + CIO + CEO (per §9.2)."""
    return asyncio.run(_run_targeted_analysis_async(symbol))
