"""Tests for FastAPI API endpoints (per §16.3).

Uses httpx AsyncClient with connection-sharing pattern:
a single DB connection with nested savepoints so that endpoint
commit() calls work correctly while still rolling back after each test.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.auth import create_access_token
from app.database import get_db
from app.main import app
from app.models.portfolio import CashBalance, Holding, RiskProfile
from app.models.reports import AnalysisReport


@pytest_asyncio.fixture
async def api_session(test_engine):
    """Create a connection-sharing session for API tests.

    Uses a single connection with a top-level transaction that rolls back
    after the test. Endpoints that call commit() create savepoints instead.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()

    # Session bound to this connection — commit becomes savepoint
    session = AsyncSession(bind=connection, expire_on_commit=False)

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def client(api_session: AsyncSession):
    """Create an async test client with DB session override."""
    token = create_access_token("admin")

    async def override_get_db():
        yield api_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers["Authorization"] = f"Bearer {token}"
        yield ac

    app.dependency_overrides.clear()


# --- Helper to seed data through the api_session ---

async def seed_cash(session: AsyncSession) -> CashBalance:
    cash = CashBalance(balance=Decimal("100000.0000"))
    session.add(cash)
    await session.flush()
    return cash


async def seed_risk_profile(session: AsyncSession) -> RiskProfile:
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
    session.add(rp)
    await session.flush()
    return rp


async def seed_holdings(session: AsyncSession) -> list[Holding]:
    now = datetime.now(timezone.utc)
    holdings_data = [
        ("AAPL", "equity", "10.0", "150.0000", "185.5000", "technology"),
        ("MSFT", "equity", "8.0", "280.0000", "410.0000", "technology"),
        ("NVDA", "equity", "15.0", "45.0000", "142.0000", "technology"),
        ("GOOGL", "equity", "5.0", "120.0000", "175.0000", "technology"),
        ("UNH", "equity", "3.0", "450.0000", "520.0000", "healthcare"),
        ("JNJ", "equity", "12.0", "160.0000", "155.0000", "healthcare"),
        ("LLY", "equity", "4.0", "350.0000", "780.0000", "healthcare"),
        ("JPM", "equity", "6.0", "140.0000", "195.0000", "financials"),
        ("BAC", "equity", "25.0", "30.0000", "38.0000", "financials"),
        ("GS", "equity", "2.0", "330.0000", "470.0000", "financials"),
    ]
    holdings = []
    for symbol, asset_type, shares, cost, price, sector in holdings_data:
        h = Holding(
            symbol=symbol, asset_type=asset_type, shares=Decimal(shares),
            avg_cost_basis=Decimal(cost), current_price=Decimal(price),
            sector=sector, acquired_at=now,
        )
        session.add(h)
        holdings.append(h)
    await session.flush()
    return holdings


async def seed_reports(session: AsyncSession) -> list[AnalysisReport]:
    reports = []
    for i in range(3):
        r = AnalysisReport(
            agent_name=f"test_agent_{i}", agent_role="analyst",
            report_type="filing_analysis", symbol="AAPL", sector="technology",
            title=f"Test Report {i}", content=f"Test content {i}",
            recommendation="BUY", confidence=7 + i,
        )
        session.add(r)
        reports.append(r)
    await session.flush()
    return reports


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client: AsyncClient):
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        response = await client.post("/api/auth/login", json={
            "username": "admin", "password": "change_me",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        response = await client.post("/api/auth/login", json={
            "username": "admin", "password": "wrong",
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_no_token(self, client: AsyncClient):
        client.headers.pop("Authorization", None)
        response = await client.get("/api/portfolio")
        assert response.status_code in (401, 403)


class TestPortfolioEndpoints:
    @pytest.mark.asyncio
    async def test_get_portfolio_summary(self, api_session, client: AsyncClient):
        await seed_holdings(api_session)
        await seed_cash(api_session)
        response = await client.get("/api/portfolio")
        assert response.status_code == 200
        data = response.json()
        assert "total_value" in data
        assert "cash_balance" in data
        assert data["cash_balance"] == 100000.0
        assert data["total_value"] > 100000.0

    @pytest.mark.asyncio
    async def test_get_holdings(self, api_session, client: AsyncClient):
        await seed_holdings(api_session)
        await seed_cash(api_session)
        response = await client.get("/api/portfolio/holdings")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        for h in data:
            assert "symbol" in h
            assert "market_value" in h
            assert "unrealized_pnl" in h
            assert "weight_pct" in h

    @pytest.mark.asyncio
    async def test_get_holdings_empty(self, api_session, client: AsyncClient):
        await seed_cash(api_session)
        response = await client.get("/api/portfolio/holdings")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_transactions_empty(self, client: AsyncClient):
        response = await client.get("/api/portfolio/transactions")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_performance(self, client: AsyncClient):
        response = await client.get("/api/portfolio/performance?period=1Y")
        assert response.status_code == 200


class TestReportEndpoints:
    @pytest.mark.asyncio
    async def test_list_reports(self, api_session, client: AsyncClient):
        await seed_reports(api_session)
        response = await client.get("/api/reports")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    @pytest.mark.asyncio
    async def test_list_reports_with_filters(self, api_session, client: AsyncClient):
        await seed_reports(api_session)
        response = await client.get("/api/reports?symbol=AAPL&sector=technology")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_get_report_detail(self, api_session, client: AsyncClient):
        reports = await seed_reports(api_session)
        report_id = reports[0].id
        response = await client.get(f"/api/reports/{report_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert "content" in data

    @pytest.mark.asyncio
    async def test_get_report_not_found(self, client: AsyncClient):
        response = await client.get("/api/reports/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_latest_by_sector(self, api_session, client: AsyncClient):
        await seed_reports(api_session)
        response = await client.get("/api/reports/latest-by-sector")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        sectors = [entry["sector"] for entry in data]
        assert "technology" in sectors


class TestSettingsEndpoints:
    @pytest.mark.asyncio
    async def test_get_risk_profile(self, api_session, client: AsyncClient):
        await seed_risk_profile(api_session)
        response = await client.get("/api/settings/risk-profile")
        assert response.status_code == 200
        data = response.json()
        assert data["aggressiveness"] == 5
        assert data["max_single_position_pct"] == 5.0

    @pytest.mark.asyncio
    async def test_update_risk_profile_partial(self, api_session, client: AsyncClient):
        await seed_risk_profile(api_session)
        response = await client.put("/api/settings/risk-profile", json={
            "aggressiveness": 7,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["aggressiveness"] == 7
        assert data["updated_by"] == "human"

    @pytest.mark.asyncio
    async def test_update_risk_profile_invalid_allocation(self, api_session, client: AsyncClient):
        await seed_risk_profile(api_session)
        response = await client.put("/api/settings/risk-profile", json={
            "target_equity_pct": 90.0,
        })
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_watchlist_crud(self, client: AsyncClient):
        response = await client.get("/api/settings/watchlist")
        assert response.status_code == 200

        response = await client.post("/api/settings/watchlist", json={"symbol": "TSLA"})
        assert response.status_code == 200
        assert "TSLA" in response.json()["symbols"]

        response = await client.delete("/api/settings/watchlist/TSLA")
        assert response.status_code == 200
        assert "TSLA" not in response.json()["symbols"]

    @pytest.mark.asyncio
    async def test_get_schedule(self, client: AsyncClient):
        response = await client.get("/api/settings/schedule")
        assert response.status_code == 200
        data = response.json()
        assert len(data["schedules"]) == 6


class TestChatEndpoints:
    @pytest.mark.asyncio
    async def test_chat_endpoint(self, client: AsyncClient):
        with patch("app.api.chat.classify_intent", new_callable=AsyncMock, return_value="GENERAL"):
            with patch("app.api.chat.route_query", new_callable=AsyncMock, return_value={
                "agent": "system",
                "response": "Hello! How can I help with your portfolio?",
            }):
                response = await client.post("/api/chat", json={"message": "Hello"})
                assert response.status_code == 200
                data = response.json()
                assert "response" in data
                assert data["intent"] == "GENERAL"

    @pytest.mark.asyncio
    async def test_chat_history(self, client: AsyncClient):
        response = await client.get("/api/chat/history")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAgentEndpoints:
    @pytest.mark.asyncio
    async def test_list_agents(self, client: AsyncClient):
        response = await client.get("/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "name" in data[0]
            assert "role" in data[0]
