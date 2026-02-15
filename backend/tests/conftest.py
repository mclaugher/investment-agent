"""Shared test fixtures (per §16.2).

Phase 1 fixtures:
- test_db: Async SQLite database for speed (per §16.2 option)
- db_session: Async session scoped to each test
- sample_portfolio: Pre-populated portfolio data
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base

# Import all models so Base.metadata is populated
import app.models  # noqa: F401
from app.models.portfolio import CashBalance, Holding, RiskProfile, Transaction
from app.models.reports import AgentDecision, AnalysisReport
from app.models.market_data import FundamentalSnapshot, PriceHistory
from app.models.filings import EarningsTranscript, SECFiling


# ---------------------------------------------------------------------------
# Engine & session fixtures
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a session-scoped async SQLite engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # SQLite needs PRAGMA foreign_keys = ON per-connection
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a per-test async session that rolls back after each test."""
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        async with session.begin():
            yield session
            # Rollback to keep tests isolated
            await session.rollback()


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def sample_cash(db_session: AsyncSession) -> CashBalance:
    """Seed a CashBalance row."""
    cash = CashBalance(balance=Decimal("100000.0000"))
    db_session.add(cash)
    await db_session.flush()
    return cash


@pytest_asyncio.fixture
async def sample_risk_profile(db_session: AsyncSession) -> RiskProfile:
    """Seed a default RiskProfile."""
    rp = RiskProfile(
        aggressiveness=5,
        max_single_position_pct=Decimal("5.00"),
        max_sector_pct=Decimal("25.00"),
        min_cash_pct=Decimal("5.00"),
        target_equity_pct=Decimal("60.00"),
        target_fixed_income_pct=Decimal("30.00"),
        target_cash_pct=Decimal("10.00"),
        updated_by="system",
        notes="Test default.",
    )
    db_session.add(rp)
    await db_session.flush()
    return rp


@pytest_asyncio.fixture
async def sample_holdings(db_session: AsyncSession) -> list[Holding]:
    """Pre-populate 10 holdings across 3 sectors (per §16.2 sample_portfolio)."""
    now = datetime.now(timezone.utc)
    holdings_data = [
        # Technology (4)
        ("AAPL", "equity", "10.0", "150.0000", "185.5000", "technology"),
        ("MSFT", "equity", "8.0", "280.0000", "410.0000", "technology"),
        ("NVDA", "equity", "15.0", "45.0000", "142.0000", "technology"),
        ("GOOGL", "equity", "5.0", "120.0000", "175.0000", "technology"),
        # Healthcare (3)
        ("UNH", "equity", "3.0", "450.0000", "520.0000", "healthcare"),
        ("JNJ", "equity", "12.0", "160.0000", "155.0000", "healthcare"),
        ("LLY", "equity", "4.0", "350.0000", "780.0000", "healthcare"),
        # Financials (3)
        ("JPM", "equity", "6.0", "140.0000", "195.0000", "financials"),
        ("BAC", "equity", "25.0", "30.0000", "38.0000", "financials"),
        ("GS", "equity", "2.0", "330.0000", "470.0000", "financials"),
    ]
    holdings = []
    for symbol, asset_type, shares, cost, price, sector in holdings_data:
        h = Holding(
            symbol=symbol,
            asset_type=asset_type,
            shares=Decimal(shares),
            avg_cost_basis=Decimal(cost),
            current_price=Decimal(price),
            sector=sector,
            acquired_at=now,
        )
        db_session.add(h)
        holdings.append(h)
    await db_session.flush()
    return holdings
