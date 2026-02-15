"""Unit tests for sec_tools (per §16.3).

SEC EDGAR API calls mocked. Verify return schema.
"""

from unittest.mock import AsyncMock, patch

import pytest

MOCK_FILINGS_LIST = [
    {
        "accession_number": "0000320193-25-000100",
        "filing_type": "10-K",
        "filing_date": "2025-10-30",
        "company_name": "Apple Inc.",
        "filing_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019325000100",
    }
]

MOCK_FILING_HTML = """
<html><body>
<h2>Item 1. Business</h2>
<p>Apple designs, manufactures, and markets smartphones.</p>
<h2>Item 1A. Risk Factors</h2>
<p>The company is subject to various risks including competition.</p>
<h2>Item 7. Management's Discussion and Analysis</h2>
<p>Revenue increased 12% year over year.</p>
<h2>Item 8. Financial Statements</h2>
<p>See consolidated financial statements.</p>
</body></html>
"""


class TestFetch10kFiling:
    @pytest.mark.asyncio
    @patch("app.agents.tools.sec_tools.fetch_filing_document", new_callable=AsyncMock, return_value=MOCK_FILING_HTML)
    @patch("app.agents.tools.sec_tools.fetch_sec_filings_list", new_callable=AsyncMock, return_value=MOCK_FILINGS_LIST)
    async def test_returns_parsed_sections(self, mock_list, mock_doc):
        from app.agents.tools.sec_tools import fetch_10k_filing
        result = await fetch_10k_filing.ainvoke({"symbol": "AAPL", "year": 2025})

        assert result["symbol"] == "AAPL"
        assert result["year"] == 2025
        assert result["filing_type"] == "10-K"
        assert "sections" in result
        assert "business" in result["sections"]
        assert "risk_factors" in result["sections"]
        assert "mda" in result["sections"]

    @pytest.mark.asyncio
    @patch("app.agents.tools.sec_tools.fetch_sec_filings_list", new_callable=AsyncMock, return_value=[])
    async def test_no_filing_found(self, mock_list):
        from app.agents.tools.sec_tools import fetch_10k_filing
        result = await fetch_10k_filing.ainvoke({"symbol": "UNKNOWN", "year": 2025})

        assert "error" in result
        assert result["sections"] == {}


class TestGetRecentFilings:
    @pytest.mark.asyncio
    @patch("app.agents.tools.sec_tools.fetch_sec_filings_list", new_callable=AsyncMock, return_value=MOCK_FILINGS_LIST)
    async def test_returns_filing_list(self, mock_list):
        from app.agents.tools.sec_tools import get_recent_filings
        result = await get_recent_filings.ainvoke({"symbol": "AAPL"})

        assert len(result) == 1
        assert result[0]["filing_type"] == "10-K"
        assert result[0]["accession_number"] == "0000320193-25-000100"
