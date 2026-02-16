"""Data refresh Celery tasks (per §9.2).

refresh_market_data: Update prices for all holdings + watchlist symbols.
refresh_fundamentals: Pull latest fundamental data for all tracked symbols.
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.celery_app import celery
from app.database import async_session
from app.models.market_data import PriceHistory, FundamentalSnapshot
from app.models.portfolio import Holding
from app.services.data_ingestion import fetch_yfinance_info, fetch_yfinance_history, fetch_yfinance_financials

logger = logging.getLogger(__name__)


async def _refresh_market_data_async() -> dict:
    """Async implementation of market data refresh."""
    async with async_session() as session:
        # Get all held symbols
        from sqlalchemy import select
        result = await session.execute(select(Holding.symbol).distinct())
        held_symbols = [row[0] for row in result.fetchall()]

    if not held_symbols:
        logger.info("No holdings found, skipping market data refresh")
        return {"symbols_updated": 0}

    updated = 0
    errors = []

    for symbol in held_symbols:
        try:
            info = fetch_yfinance_info(symbol)
            price = info.get("regularMarketPrice") or info.get("currentPrice")

            if price:
                async with async_session() as session:
                    # Update holding current price
                    from sqlalchemy import update
                    await session.execute(
                        update(Holding)
                        .where(Holding.symbol == symbol)
                        .values(current_price=price, updated_at=datetime.now(timezone.utc))
                    )
                    await session.commit()
                updated += 1

        except Exception as e:
            errors.append({"symbol": symbol, "error": str(e)})
            logger.warning(f"Failed to refresh {symbol}: {e}")

    result = {"symbols_updated": updated, "errors": errors}
    logger.info(f"Market data refresh complete: {updated}/{len(held_symbols)} updated")
    return result


async def _refresh_fundamentals_async() -> dict:
    """Async implementation of fundamental data refresh."""
    from scripts.seed_universe import STOCK_UNIVERSE

    all_symbols = []
    for symbols in STOCK_UNIVERSE.values():
        all_symbols.extend(symbols)

    updated = 0
    errors = []

    for symbol in all_symbols:
        try:
            info = fetch_yfinance_info(symbol)

            async with async_session() as session:
                snapshot = FundamentalSnapshot(
                    symbol=symbol,
                    snapshot_date=datetime.now(timezone.utc).date(),
                    pe_ratio=info.get("trailingPE"),
                    pb_ratio=info.get("priceToBook"),
                    ps_ratio=info.get("priceToSalesTrailing12Months"),
                    ev_ebitda=info.get("enterpriseToEbitda"),
                    roe=info.get("returnOnEquity"),
                    roa=info.get("returnOnAssets"),
                    debt_to_equity=info.get("debtToEquity"),
                    current_ratio=info.get("currentRatio"),
                    revenue_ttm=info.get("totalRevenue"),
                    net_income_ttm=info.get("netIncomeToCommon"),
                    free_cash_flow_ttm=info.get("freeCashflow"),
                    market_cap=info.get("marketCap"),
                    dividend_yield=info.get("dividendYield"),
                    beta=info.get("beta"),
                    raw_data=info,
                )
                session.add(snapshot)
                await session.commit()
            updated += 1

        except Exception as e:
            errors.append({"symbol": symbol, "error": str(e)})
            logger.warning(f"Failed to refresh fundamentals for {symbol}: {e}")

    logger.info(f"Fundamental refresh complete: {updated}/{len(all_symbols)} updated")
    return {"symbols_updated": updated, "errors": errors}


@celery.task(name="app.tasks.data_refresh.refresh_market_data")
def refresh_market_data() -> dict:
    """Update prices for all holdings + watchlist symbols (per §9.2)."""
    return asyncio.run(_refresh_market_data_async())


@celery.task(name="app.tasks.data_refresh.refresh_fundamentals")
def refresh_fundamentals() -> dict:
    """Pull latest fundamental data for all tracked symbols (per §9.2)."""
    return asyncio.run(_refresh_fundamentals_async())
