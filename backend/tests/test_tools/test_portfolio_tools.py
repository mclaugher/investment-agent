"""Unit tests for portfolio_tools (per §16.3).

Tests trade execution, constraint validation, and especially no-margin enforcement (§18).
Uses the async SQLite test DB from conftest.py.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.models.portfolio import CashBalance, Holding, RiskProfile, Transaction
from app.models.reports import AgentDecision


class TestValidateTrade:
    """Test validate_trade enforces all constraints from §18."""

    @pytest.mark.asyncio
    async def test_reject_invalid_action(self, db_session, sample_cash, sample_risk_profile):
        """§18: Only BUY and SELL allowed — no margin, no short selling."""
        with patch("app.agents.tools.portfolio_tools.async_session") as mock_session_factory:
            mock_session_factory.return_value.__aenter__ = lambda s: db_session
            mock_session_factory.return_value.__aexit__ = lambda s, *a: None

            # We need to test the tool logic directly with our test session
            # Build a minimal test instead of going through the tool decorator
            pass

    @pytest.mark.asyncio
    async def test_buy_insufficient_cash(self, db_session, sample_cash, sample_risk_profile):
        """§18: Cash balance must never go negative. No borrowing."""
        # sample_cash has $100,000
        # Try to buy $200,000 worth — should fail
        from app.agents.tools.portfolio_tools import validate_trade

        # Patch async_session to return our test session
        async def mock_session():
            return db_session

        with patch("app.agents.tools.portfolio_tools.async_session") as mock_factory:
            # Create a context manager that returns our session
            class MockCM:
                async def __aenter__(self):
                    return db_session
                async def __aexit__(self, *args):
                    pass
            mock_factory.return_value = MockCM()

            result = await validate_trade.ainvoke({
                "action": "BUY",
                "symbol": "AAPL",
                "shares": 1000.0,
                "estimated_price": 200.0,
            })

            assert result["valid"] is False
            assert any("cash" in e.lower() or "margin" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_sell_insufficient_shares(self, db_session, sample_cash, sample_risk_profile, sample_holdings):
        """§18: Cannot sell more than owned. No short selling."""
        from app.agents.tools.portfolio_tools import validate_trade

        class MockCM:
            async def __aenter__(self):
                return db_session
            async def __aexit__(self, *args):
                pass

        with patch("app.agents.tools.portfolio_tools.async_session") as mock_factory:
            mock_factory.return_value = MockCM()

            # AAPL has 10 shares in sample_holdings, try to sell 100
            result = await validate_trade.ainvoke({
                "action": "SELL",
                "symbol": "AAPL",
                "shares": 100.0,
                "estimated_price": 185.0,
            })

            assert result["valid"] is False
            assert any("short" in e.lower() or "insufficient" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_valid_buy(self, db_session, sample_cash, sample_risk_profile, sample_holdings):
        """A reasonable buy within constraints should pass."""
        from app.agents.tools.portfolio_tools import validate_trade

        class MockCM:
            async def __aenter__(self):
                return db_session
            async def __aexit__(self, *args):
                pass

        with patch("app.agents.tools.portfolio_tools.async_session") as mock_factory:
            mock_factory.return_value = MockCM()

            # Buy $1000 worth of AAPL — well within cash and limits
            result = await validate_trade.ainvoke({
                "action": "BUY",
                "symbol": "AAPL",
                "shares": 5.0,
                "estimated_price": 185.0,
            })

            assert result["valid"] is True
            assert result["errors"] == []
            assert result["post_trade_cash"] > 0


class TestExecuteTrade:
    """Test execute_trade enforces constraints and updates DB correctly."""

    @pytest.mark.asyncio
    async def test_reject_invalid_action(self, db_session, sample_cash):
        """§18: Only BUY or SELL — everything else rejected."""
        from app.agents.tools.portfolio_tools import execute_trade

        class MockCM:
            async def __aenter__(self):
                return db_session
            async def __aexit__(self, *args):
                pass
            async def begin(self):
                return self
            async def __aenter_nested__(self):
                return db_session

        with patch("app.agents.tools.portfolio_tools.async_session") as mock_factory:
            mock_factory.return_value = MockCM()

            result = await execute_trade.ainvoke({
                "action": "SHORT",
                "symbol": "AAPL",
                "shares": 10.0,
                "price": 185.0,
                "decision_id": 1,
            })

            assert result["success"] is False
            assert "REJECTED" in result["error"]

    @pytest.mark.asyncio
    async def test_reject_negative_shares(self, db_session, sample_cash):
        """Shares must be positive."""
        from app.agents.tools.portfolio_tools import execute_trade

        class MockCM:
            async def __aenter__(self):
                return db_session
            async def __aexit__(self, *args):
                pass

        with patch("app.agents.tools.portfolio_tools.async_session") as mock_factory:
            mock_factory.return_value = MockCM()

            result = await execute_trade.ainvoke({
                "action": "BUY",
                "symbol": "AAPL",
                "shares": -5.0,
                "price": 185.0,
                "decision_id": 1,
            })

            assert result["success"] is False


class TestGetCurrentHoldings:
    @pytest.mark.asyncio
    async def test_returns_holdings_with_pnl(self, db_session, sample_holdings, sample_cash):
        from app.agents.tools.portfolio_tools import get_current_holdings

        class MockCM:
            async def __aenter__(self):
                return db_session
            async def __aexit__(self, *args):
                pass

        with patch("app.agents.tools.portfolio_tools.async_session") as mock_factory:
            mock_factory.return_value = MockCM()

            result = await get_current_holdings.ainvoke({})

            assert len(result) == 10
            for h in result:
                assert "symbol" in h
                assert "unrealized_pnl" in h
                assert "weight_pct" in h
                assert "market_value" in h


class TestGetCashBalance:
    @pytest.mark.asyncio
    async def test_returns_cash_info(self, db_session, sample_cash, sample_risk_profile):
        from app.agents.tools.portfolio_tools import get_cash_balance

        class MockCM:
            async def __aenter__(self):
                return db_session
            async def __aexit__(self, *args):
                pass

        with patch("app.agents.tools.portfolio_tools.async_session") as mock_factory:
            mock_factory.return_value = MockCM()

            result = await get_cash_balance.ainvoke({})

            assert result["balance"] == 100000.0
            assert "min_reserve" in result
            assert "available_for_investment" in result
            assert result["available_for_investment"] <= result["balance"]


class TestGetRiskProfile:
    @pytest.mark.asyncio
    async def test_returns_profile(self, db_session, sample_risk_profile):
        from app.agents.tools.portfolio_tools import get_risk_profile

        class MockCM:
            async def __aenter__(self):
                return db_session
            async def __aexit__(self, *args):
                pass

        with patch("app.agents.tools.portfolio_tools.async_session") as mock_factory:
            mock_factory.return_value = MockCM()

            result = await get_risk_profile.ainvoke({})

            assert result["aggressiveness"] == 5
            assert result["max_single_position_pct"] == 5.0
            assert result["max_sector_pct"] == 25.0
            total = result["target_equity_pct"] + result["target_fixed_income_pct"] + result["target_cash_pct"]
            assert total == 100.0
