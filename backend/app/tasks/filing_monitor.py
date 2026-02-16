"""Filing monitor Celery tasks (per §9.2).

check_new_filings: Query SEC EDGAR for new filings for all tracked CIKs.
ingest_filing: Download, parse, store, and trigger analysis for a filing.
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.celery_app import celery
from app.database import async_session
from app.models.filings import SECFiling
from app.services.data_ingestion import fetch_sec_filings_list, fetch_filing_document

logger = logging.getLogger(__name__)


async def _check_new_filings_async() -> dict:
    """Async implementation of filing check."""
    from scripts.seed_universe import STOCK_UNIVERSE

    all_symbols = []
    for symbols in STOCK_UNIVERSE.values():
        all_symbols.extend(symbols)

    new_filings = 0
    errors = []

    for symbol in all_symbols:
        try:
            filings = fetch_sec_filings_list(symbol, filing_type="10-K,10-Q", limit=5)

            for filing_data in filings:
                accession = filing_data.get("accession_number", "")
                if not accession:
                    continue

                # Check if we already have this filing
                async with async_session() as session:
                    from sqlalchemy import select
                    existing = await session.execute(
                        select(SECFiling).where(SECFiling.accession_number == accession)
                    )
                    if existing.scalar_one_or_none():
                        continue

                    # New filing — create record
                    sec_filing = SECFiling(
                        symbol=symbol,
                        cik=filing_data.get("cik", ""),
                        filing_type=filing_data.get("filing_type", ""),
                        filing_date=filing_data.get("filing_date", datetime.now(timezone.utc)),
                        accession_number=accession,
                        filing_url=filing_data.get("filing_url", ""),
                        is_processed=False,
                    )
                    session.add(sec_filing)
                    await session.commit()
                    await session.refresh(sec_filing)

                    # Trigger ingestion
                    ingest_filing.delay(sec_filing.id)
                    new_filings += 1

        except Exception as e:
            errors.append({"symbol": symbol, "error": str(e)})
            logger.warning(f"Failed to check filings for {symbol}: {e}")

    logger.info(f"Filing check complete: {new_filings} new filings found")
    return {"new_filings": new_filings, "errors": errors}


async def _ingest_filing_async(filing_id: int) -> dict:
    """Async implementation of filing ingestion."""
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(SECFiling).where(SECFiling.id == filing_id)
        )
        filing = result.scalar_one_or_none()

        if not filing:
            return {"error": f"Filing {filing_id} not found"}

        try:
            # Download and parse the filing
            doc = fetch_filing_document(filing.filing_url)

            # Mark as processed
            filing.is_processed = True
            filing.processed_at = datetime.now(timezone.utc)
            await session.commit()

            # Trigger targeted analysis for the affected symbol
            from app.tasks.analysis_cycle import run_targeted_analysis
            run_targeted_analysis.delay(filing.symbol)

            logger.info(f"Ingested filing {filing_id} for {filing.symbol}")
            return {"filing_id": filing_id, "symbol": filing.symbol, "status": "processed"}

        except Exception as e:
            logger.error(f"Failed to ingest filing {filing_id}: {e}")
            return {"filing_id": filing_id, "error": str(e)}


@celery.task(name="app.tasks.filing_monitor.check_new_filings")
def check_new_filings() -> dict:
    """Query SEC EDGAR for new filings for all tracked symbols (per §9.2)."""
    return asyncio.run(_check_new_filings_async())


@celery.task(name="app.tasks.filing_monitor.ingest_filing")
def ingest_filing(filing_id: int) -> dict:
    """Download, parse, store, and trigger analysis for a filing (per §9.2)."""
    return asyncio.run(_ingest_filing_async(filing_id))
