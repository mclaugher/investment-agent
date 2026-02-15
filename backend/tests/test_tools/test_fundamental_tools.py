"""Unit tests for fundamental_tools (per §16.3).

yfinance calls mocked with realistic data.
"""

from unittest.mock import patch

import pytest

MOCK_INFO = {
    "regularMarketPrice": 185.50,
    "currentPrice": 185.50,
    "trailingPE": 28.5,
    "forwardPE": 25.2,
    "priceToBook": 45.3,
    "priceToSalesTrailing12Months": 7.8,
    "enterpriseToEbitda": 22.1,
    "returnOnEquity": 0.175,
    "returnOnAssets": 0.21,
    "debtToEquity": 176.3,
    "currentRatio": 1.07,
    "quickRatio": 0.94,
    "grossMargins": 0.462,
    "operatingMargins": 0.311,
    "profitMargins": 0.264,
    "revenueGrowth": 0.05,
    "earningsGrowth": 0.12,
    "dividendYield": 0.0055,
    "payoutRatio": 0.156,
    "beta": 1.25,
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "sharesOutstanding": 15_600_000_000,
    "marketCap": 2_900_000_000_000,
}

MOCK_FINANCIALS = {
    "info": MOCK_INFO,
    "financials": {},
    "balance_sheet": {},
    "cashflow": {
        "Free Cash Flow": {
            "2024-09-30": 100_000_000_000,
            "2023-09-30": 92_000_000_000,
            "2022-09-30": 85_000_000_000,
        }
    },
}


class TestGetFinancialRatios:
    @patch("app.agents.tools.fundamental_tools.fetch_yfinance_info", return_value=MOCK_INFO)
    def test_returns_all_ratios(self, mock_info):
        from app.agents.tools.fundamental_tools import get_financial_ratios
        result = get_financial_ratios.invoke({"symbol": "AAPL"})

        assert result["symbol"] == "AAPL"
        assert result["pe"] == 28.5
        assert result["forward_pe"] == 25.2
        assert result["roe"] == 0.175
        assert result["beta"] == 1.25
        assert result["dividend_yield"] == 0.0055

    @patch("app.agents.tools.fundamental_tools.fetch_yfinance_info", return_value=MOCK_INFO)
    def test_schema_keys(self, mock_info):
        from app.agents.tools.fundamental_tools import get_financial_ratios
        result = get_financial_ratios.invoke({"symbol": "AAPL"})
        expected = {
            "symbol", "pe", "forward_pe", "pb", "ps", "ev_ebitda",
            "roe", "roa", "debt_equity", "current_ratio", "quick_ratio",
            "gross_margin", "operating_margin", "net_margin",
            "revenue_growth_yoy", "earnings_growth_yoy",
            "dividend_yield", "payout_ratio", "beta",
        }
        assert set(result.keys()) == expected


class TestRunDcfAnalysis:
    @patch("app.agents.tools.fundamental_tools.fetch_yfinance_financials", return_value=MOCK_FINANCIALS)
    def test_returns_dcf_result(self, mock_fin):
        from app.agents.tools.fundamental_tools import run_dcf_analysis
        result = run_dcf_analysis.invoke({"symbol": "AAPL"})

        assert result["symbol"] == "AAPL"
        assert "fair_value_per_share" in result
        assert "current_price" in result
        assert "upside_pct" in result
        assert "sensitivity_table" in result
        assert "bull" in result["sensitivity_table"]
        assert "base" in result["sensitivity_table"]
        assert "bear" in result["sensitivity_table"]

    @patch("app.agents.tools.fundamental_tools.fetch_yfinance_financials", return_value=MOCK_FINANCIALS)
    def test_dcf_with_custom_params(self, mock_fin):
        from app.agents.tools.fundamental_tools import run_dcf_analysis
        result = run_dcf_analysis.invoke({
            "symbol": "AAPL",
            "growth_rate": 0.08,
            "discount_rate": 0.12,
            "projection_years": 10,
        })

        assert result["assumptions"]["base_growth_rate"] == 0.08
        assert result["assumptions"]["discount_rate"] == 0.12
        assert result["assumptions"]["projection_years"] == 10
        assert len(result["projected_fcf"]) == 10

    @patch("app.agents.tools.fundamental_tools.fetch_yfinance_financials")
    def test_dcf_no_data(self, mock_fin):
        mock_fin.return_value = {"info": {"currentPrice": 100}, "cashflow": {}, "financials": {}, "balance_sheet": {}}
        from app.agents.tools.fundamental_tools import run_dcf_analysis
        result = run_dcf_analysis.invoke({"symbol": "UNKNOWN"})
        assert "error" in result


class TestGetComparableAnalysis:
    @patch("app.agents.tools.fundamental_tools.fetch_yfinance_info", return_value=MOCK_INFO)
    def test_returns_target_and_peers(self, mock_info):
        from app.agents.tools.fundamental_tools import get_comparable_analysis
        result = get_comparable_analysis.invoke({"symbol": "AAPL"})

        assert "target" in result
        assert result["target"]["symbol"] == "AAPL"
        assert "peers" in result
        assert "target_vs_median" in result
