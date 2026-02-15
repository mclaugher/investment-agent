"""Unit tests for market_tools (per §16.3).

All yfinance calls mocked with realistic data.
Verify return schema matches expected dict structure.
"""

from unittest.mock import patch

import pytest


# Realistic mock yfinance info
MOCK_AAPL_INFO = {
    "regularMarketPrice": 185.50,
    "regularMarketPreviousClose": 183.25,
    "regularMarketVolume": 45_000_000,
    "fiftyTwoWeekHigh": 199.62,
    "fiftyTwoWeekLow": 143.90,
    "marketCap": 2_900_000_000_000,
    "currentPrice": 185.50,
    "previousClose": 183.25,
}

MOCK_HISTORY = [
    {"date": "2025-01-02", "open": 180.0, "high": 182.0, "low": 179.0, "close": 181.5, "volume": 40_000_000},
    {"date": "2025-01-03", "open": 181.5, "high": 184.0, "low": 181.0, "close": 183.0, "volume": 42_000_000},
    {"date": "2025-01-06", "open": 183.0, "high": 186.0, "low": 182.5, "close": 185.5, "volume": 45_000_000},
]


class TestGetStockPrice:
    @patch("app.agents.tools.market_tools.fetch_yfinance_info", return_value=MOCK_AAPL_INFO)
    def test_returns_expected_schema(self, mock_info):
        from app.agents.tools.market_tools import get_stock_price
        result = get_stock_price.invoke({"symbol": "AAPL"})

        assert result["symbol"] == "AAPL"
        assert result["price"] == 185.50
        assert result["change"] == pytest.approx(2.25, abs=0.01)
        assert result["change_pct"] == pytest.approx(1.23, abs=0.1)
        assert result["volume"] == 45_000_000
        assert result["high_52w"] == 199.62
        assert result["low_52w"] == 143.90
        assert result["market_cap"] == 2_900_000_000_000

    @patch("app.agents.tools.market_tools.fetch_yfinance_info", return_value=MOCK_AAPL_INFO)
    def test_all_keys_present(self, mock_info):
        from app.agents.tools.market_tools import get_stock_price
        result = get_stock_price.invoke({"symbol": "AAPL"})
        expected_keys = {"symbol", "price", "change", "change_pct", "volume", "high_52w", "low_52w", "market_cap"}
        assert set(result.keys()) == expected_keys


class TestGetPriceHistory:
    @patch("app.agents.tools.market_tools.fetch_yfinance_history", return_value=MOCK_HISTORY)
    def test_returns_expected_schema(self, mock_hist):
        from app.agents.tools.market_tools import get_price_history
        result = get_price_history.invoke({"symbol": "AAPL", "period": "1y", "interval": "1d"})

        assert result["symbol"] == "AAPL"
        assert result["period"] == "1y"
        assert len(result["data"]) == 3
        assert "close" in result["data"][0]
        assert "volume" in result["data"][0]

    @patch("app.agents.tools.market_tools.fetch_yfinance_history", return_value=MOCK_HISTORY)
    def test_invalid_period_defaults_to_1y(self, mock_hist):
        from app.agents.tools.market_tools import get_price_history
        result = get_price_history.invoke({"symbol": "AAPL", "period": "invalid"})
        assert result["period"] == "1y"


class TestGetMarketOverview:
    @patch("app.agents.tools.market_tools.fetch_yfinance_info", return_value=MOCK_AAPL_INFO)
    def test_returns_indices_and_sectors(self, mock_info):
        from app.agents.tools.market_tools import get_market_overview
        result = get_market_overview.invoke({})

        assert "indices" in result
        assert "vix" in result
        assert "sectors" in result
        assert len(result["indices"]) == 4  # SPY, QQQ, DIA, IWM


class TestGetSectorEtfPerformance:
    @patch("app.agents.tools.market_tools.fetch_yfinance_history", return_value=MOCK_HISTORY)
    @patch("app.agents.tools.market_tools.fetch_yfinance_info", return_value=MOCK_AAPL_INFO)
    def test_known_sector(self, mock_info, mock_hist):
        from app.agents.tools.market_tools import get_sector_etf_performance
        result = get_sector_etf_performance.invoke({"sector": "technology"})

        assert result["sector"] == "technology"
        assert result["etf_symbol"] == "XLK"
        assert "price" in result
        assert "daily_change_pct" in result

    def test_unknown_sector(self):
        from app.agents.tools.market_tools import get_sector_etf_performance
        result = get_sector_etf_performance.invoke({"sector": "crypto"})
        assert "error" in result
