"""Phase 1 tests: verify DB creates all tables, seed runs successfully (per §17).

Tests cover:
- All 10 tables exist in metadata
- Model CRUD operations work
- CHECK constraints enforce hard constraints (§18)
- Seed universe data is well-formed
- Sample portfolio fixture loads correctly
"""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import inspect, select, text

from app.database import Base
from app.models.portfolio import CashBalance, Holding, RiskProfile, Transaction
from app.models.reports import AgentDecision, AnalysisReport
from app.models.market_data import FundamentalSnapshot, PriceHistory
from app.models.filings import EarningsTranscript, SECFiling


# ---------------------------------------------------------------------------
# Table existence
# ---------------------------------------------------------------------------

EXPECTED_TABLES = sorted([
    "holdings",
    "transactions",
    "cash_balances",
    "risk_profiles",
    "analysis_reports",
    "agent_decisions",
    "price_history",
    "fundamental_snapshots",
    "sec_filings",
    "earnings_transcripts",
])


class TestTableCreation:
    """Verify all 10 tables are registered and created."""

    def test_all_tables_in_metadata(self):
        """All 10 tables must be in Base.metadata."""
        actual = sorted(Base.metadata.tables.keys())
        assert actual == EXPECTED_TABLES

    @pytest.mark.asyncio
    async def test_tables_exist_in_db(self, test_engine):
        """All tables should be created in the test database."""
        async with test_engine.connect() as conn:
            table_names = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        for t in EXPECTED_TABLES:
            assert t in table_names, f"Table '{t}' not found in database"


# ---------------------------------------------------------------------------
# Model CRUD
# ---------------------------------------------------------------------------

class TestPortfolioModels:
    """Test portfolio model CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_holding(self, db_session):
        now = datetime.now(timezone.utc)
        h = Holding(
            symbol="AAPL",
            asset_type="equity",
            shares=Decimal("10.5"),
            avg_cost_basis=Decimal("150.0000"),
            current_price=Decimal("185.5000"),
            sector="technology",
            acquired_at=now,
        )
        db_session.add(h)
        await db_session.flush()

        result = await db_session.execute(select(Holding).where(Holding.symbol == "AAPL"))
        fetched = result.scalar_one()
        assert fetched.shares == Decimal("10.5")
        assert fetched.asset_type == "equity"
        assert fetched.sector == "technology"

    @pytest.mark.asyncio
    async def test_create_cash_balance(self, db_session):
        cash = CashBalance(balance=Decimal("100000.0000"))
        db_session.add(cash)
        await db_session.flush()

        result = await db_session.execute(select(CashBalance))
        fetched = result.scalar_one()
        assert fetched.balance == Decimal("100000.0000")

    @pytest.mark.asyncio
    async def test_create_risk_profile(self, db_session):
        rp = RiskProfile(
            aggressiveness=5,
            max_single_position_pct=Decimal("5.00"),
            max_sector_pct=Decimal("25.00"),
            min_cash_pct=Decimal("5.00"),
            target_equity_pct=Decimal("60.00"),
            target_fixed_income_pct=Decimal("30.00"),
            target_cash_pct=Decimal("10.00"),
            updated_by="system",
        )
        db_session.add(rp)
        await db_session.flush()

        result = await db_session.execute(select(RiskProfile))
        fetched = result.scalar_one()
        assert fetched.aggressiveness == 5
        # Verify allocations sum to 100
        total = fetched.target_equity_pct + fetched.target_fixed_income_pct + fetched.target_cash_pct
        assert total == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_create_transaction(self, db_session):
        now = datetime.now(timezone.utc)
        t = Transaction(
            symbol="MSFT",
            action="BUY",
            shares=Decimal("5.0"),
            price_per_share=Decimal("410.0000"),
            total_amount=Decimal("2050.0000"),
            executed_at=now,
        )
        db_session.add(t)
        await db_session.flush()

        result = await db_session.execute(select(Transaction).where(Transaction.symbol == "MSFT"))
        fetched = result.scalar_one()
        assert fetched.action == "BUY"
        assert fetched.total_amount == Decimal("2050.0000")


class TestReportModels:
    """Test report model CRUD and self-referential relationship."""

    @pytest.mark.asyncio
    async def test_create_analysis_report(self, db_session):
        report = AnalysisReport(
            agent_name="technology_filing_analyst",
            agent_role="analyst",
            report_type="filing_analysis",
            symbol="AAPL",
            sector="technology",
            title="AAPL 10-K FY2025 Analysis",
            content="Apple reported strong revenue growth...",
            recommendation="BUY",
            confidence=8,
            key_metrics={"revenue_growth": 0.12, "gross_margin": 0.46},
        )
        db_session.add(report)
        await db_session.flush()

        result = await db_session.execute(
            select(AnalysisReport).where(AnalysisReport.symbol == "AAPL")
        )
        fetched = result.scalar_one()
        assert fetched.agent_role == "analyst"
        assert fetched.confidence == 8
        assert fetched.key_metrics["revenue_growth"] == 0.12

    @pytest.mark.asyncio
    async def test_report_parent_child_relationship(self, db_session):
        """Reports should support self-referential tree structure (per §4.2)."""
        parent = AnalysisReport(
            agent_name="cio_agent",
            agent_role="cio",
            report_type="sector_overview",
            sector="technology",
            title="Technology Sector Overview",
            content="Technology sector is strong...",
        )
        db_session.add(parent)
        await db_session.flush()

        child = AnalysisReport(
            agent_name="technology_filing_analyst",
            agent_role="analyst",
            report_type="filing_analysis",
            symbol="AAPL",
            sector="technology",
            title="AAPL Filing Analysis",
            content="AAPL filings look good...",
            parent_report_id=parent.id,
        )
        db_session.add(child)
        await db_session.flush()

        # Reload parent and check children
        result = await db_session.execute(
            select(AnalysisReport).where(AnalysisReport.id == parent.id)
        )
        fetched_parent = result.scalar_one()
        await db_session.refresh(fetched_parent, ["children"])
        assert len(fetched_parent.children) == 1
        assert fetched_parent.children[0].symbol == "AAPL"

    @pytest.mark.asyncio
    async def test_create_agent_decision(self, db_session):
        decision = AgentDecision(
            decision_type="trade",
            symbol="NVDA",
            action="BUY",
            recommended_shares=Decimal("50.0"),
            recommended_amount=Decimal("7100.0000"),
            reasoning="Strong convergence across analyst levels.",
            confidence=8,
            risk_score=Decimal("3.20"),
            supporting_report_ids=[1, 2, 3],
            status="proposed",
        )
        db_session.add(decision)
        await db_session.flush()

        result = await db_session.execute(
            select(AgentDecision).where(AgentDecision.symbol == "NVDA")
        )
        fetched = result.scalar_one()
        assert fetched.action == "BUY"
        assert fetched.supporting_report_ids == [1, 2, 3]


class TestMarketDataModels:
    """Test market data model CRUD."""

    @pytest.mark.asyncio
    async def test_create_price_history(self, db_session):
        ph = PriceHistory(
            symbol="AAPL",
            date=date(2025, 12, 1),
            open=Decimal("185.0000"),
            high=Decimal("187.5000"),
            low=Decimal("184.0000"),
            close=Decimal("186.5000"),
            volume=45_000_000,
        )
        db_session.add(ph)
        await db_session.flush()

        result = await db_session.execute(
            select(PriceHistory).where(PriceHistory.symbol == "AAPL")
        )
        fetched = result.scalar_one()
        assert fetched.close == Decimal("186.5000")
        assert fetched.volume == 45_000_000

    @pytest.mark.asyncio
    async def test_price_history_unique_constraint(self, db_session):
        """Duplicate (symbol, date) should raise an error."""
        d = date(2025, 11, 15)
        ph1 = PriceHistory(symbol="MSFT", date=d, close=Decimal("400.0000"))
        ph2 = PriceHistory(symbol="MSFT", date=d, close=Decimal("401.0000"))
        db_session.add(ph1)
        await db_session.flush()
        db_session.add(ph2)
        with pytest.raises(Exception):  # IntegrityError
            await db_session.flush()

    @pytest.mark.asyncio
    async def test_create_fundamental_snapshot(self, db_session):
        fs = FundamentalSnapshot(
            symbol="GOOGL",
            snapshot_date=date(2025, 12, 1),
            pe_ratio=Decimal("25.30"),
            roe=Decimal("0.2850"),
            market_cap=Decimal("2100000000000.00"),
            raw_data={"source": "yfinance"},
        )
        db_session.add(fs)
        await db_session.flush()

        result = await db_session.execute(
            select(FundamentalSnapshot).where(FundamentalSnapshot.symbol == "GOOGL")
        )
        fetched = result.scalar_one()
        assert fetched.pe_ratio == Decimal("25.30")


class TestFilingModels:
    """Test filing model CRUD."""

    @pytest.mark.asyncio
    async def test_create_sec_filing(self, db_session):
        filing = SECFiling(
            symbol="AAPL",
            cik="0000320193",
            filing_type="10-K",
            filing_date=date(2025, 10, 30),
            accession_number="0000320193-25-000100",
            filing_url="https://www.sec.gov/Archives/edgar/data/320193/...",
        )
        db_session.add(filing)
        await db_session.flush()

        result = await db_session.execute(
            select(SECFiling).where(SECFiling.symbol == "AAPL")
        )
        fetched = result.scalar_one()
        assert fetched.filing_type == "10-K"
        assert fetched.is_processed is False

    @pytest.mark.asyncio
    async def test_create_earnings_transcript(self, db_session):
        et = EarningsTranscript(
            symbol="MSFT",
            fiscal_year=2025,
            fiscal_quarter=4,
            event_date=date(2025, 10, 22),
            full_text="Good afternoon, everyone...",
            ceo_remarks="We had an outstanding quarter...",
            sentiment_score=Decimal("0.7500"),
        )
        db_session.add(et)
        await db_session.flush()

        result = await db_session.execute(
            select(EarningsTranscript).where(EarningsTranscript.symbol == "MSFT")
        )
        fetched = result.scalar_one()
        assert fetched.fiscal_quarter == 4
        assert fetched.sentiment_score == Decimal("0.7500")

    @pytest.mark.asyncio
    async def test_transcript_unique_constraint(self, db_session):
        """Duplicate (symbol, fiscal_year, fiscal_quarter) should raise an error."""
        base = dict(
            symbol="NVDA", fiscal_year=2025, fiscal_quarter=3,
            event_date=date(2025, 8, 20), full_text="..."
        )
        db_session.add(EarningsTranscript(**base))
        await db_session.flush()
        db_session.add(EarningsTranscript(**base))
        with pytest.raises(Exception):
            await db_session.flush()


# ---------------------------------------------------------------------------
# Seed universe verification
# ---------------------------------------------------------------------------

class TestSeedUniverse:
    """Verify the stock universe data is well-formed."""

    def test_all_sectors_present(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
        from scripts.seed_universe import STOCK_UNIVERSE, BOND_ETFS, SECTOR_ETFS

        expected_sectors = {
            "technology", "healthcare", "financials", "energy",
            "consumer", "industrials", "real_estate", "utilities",
        }
        assert set(STOCK_UNIVERSE.keys()) == expected_sectors

    def test_each_sector_has_symbols(self):
        from scripts.seed_universe import STOCK_UNIVERSE
        for sector, symbols in STOCK_UNIVERSE.items():
            assert len(symbols) >= 5, f"{sector} has too few symbols"
            assert all(isinstance(s, str) and s == s.upper() for s in symbols)

    def test_no_duplicate_symbols(self):
        from scripts.seed_universe import STOCK_UNIVERSE
        all_symbols = [s for syms in STOCK_UNIVERSE.values() for s in syms]
        assert len(all_symbols) == len(set(all_symbols)), "Duplicate symbols found"

    def test_bond_etfs_exist(self):
        from scripts.seed_universe import BOND_ETFS
        assert len(BOND_ETFS) >= 5
        assert "AGG" in BOND_ETFS
        assert "TLT" in BOND_ETFS

    def test_sector_etf_mapping(self):
        from scripts.seed_universe import STOCK_UNIVERSE, SECTOR_ETFS
        assert set(SECTOR_ETFS.keys()) == set(STOCK_UNIVERSE.keys())


# ---------------------------------------------------------------------------
# Sample portfolio fixture
# ---------------------------------------------------------------------------

class TestSamplePortfolio:
    """Verify the sample_portfolio fixture loads correctly (per §16.2)."""

    @pytest.mark.asyncio
    async def test_sample_holdings_count(self, sample_holdings):
        assert len(sample_holdings) == 10

    @pytest.mark.asyncio
    async def test_sample_holdings_sectors(self, sample_holdings):
        sectors = {h.sector for h in sample_holdings}
        assert sectors == {"technology", "healthcare", "financials"}

    @pytest.mark.asyncio
    async def test_sample_cash(self, sample_cash):
        assert sample_cash.balance == Decimal("100000.0000")

    @pytest.mark.asyncio
    async def test_sample_risk_profile(self, sample_risk_profile):
        assert sample_risk_profile.aggressiveness == 5
        total = (
            sample_risk_profile.target_equity_pct
            + sample_risk_profile.target_fixed_income_pct
            + sample_risk_profile.target_cash_pct
        )
        assert total == Decimal("100.00")


# ---------------------------------------------------------------------------
# Hard constraint enforcement (§18)
# ---------------------------------------------------------------------------

class TestHardConstraints:
    """Verify DB-level constraint enforcement per §18."""

    @pytest.mark.asyncio
    async def test_transaction_fk_to_agent_decision(self, db_session):
        """Transaction.agent_decision_id should FK to agent_decisions (per §4.1)."""
        decision = AgentDecision(
            decision_type="trade",
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
            confidence=7,
            supporting_report_ids=[],
        )
        db_session.add(decision)
        await db_session.flush()

        now = datetime.now(timezone.utc)
        txn = Transaction(
            symbol="AAPL",
            action="BUY",
            shares=Decimal("10"),
            price_per_share=Decimal("185.00"),
            total_amount=Decimal("1850.00"),
            agent_decision_id=decision.id,
            executed_at=now,
        )
        db_session.add(txn)
        await db_session.flush()

        result = await db_session.execute(
            select(Transaction).where(Transaction.agent_decision_id == decision.id)
        )
        fetched = result.scalar_one()
        assert fetched.symbol == "AAPL"
