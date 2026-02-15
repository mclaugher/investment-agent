"""Shared data fetching logic for SEC EDGAR, yfinance, and FMP APIs (per §17 Phase 2).

All external API calls use tenacity retry with exponential backoff (per §6).
"""

import httpx
import structlog
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# HTTP client helpers
# ---------------------------------------------------------------------------

SEC_BASE_URL = "https://efts.sec.gov/LATEST"
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"


def _sec_headers() -> dict[str, str]:
    return {"User-Agent": settings.sec_user_agent, "Accept": "application/json"}


def _fmp_params(**kwargs) -> dict:
    params = {"apikey": settings.fmp_api_key}
    params.update(kwargs)
    return params


# ---------------------------------------------------------------------------
# SEC EDGAR
# ---------------------------------------------------------------------------

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException)),
)
async def fetch_sec_filings_list(
    symbol: str,
    filing_type: str = "10-K",
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Search SEC EDGAR EFTS for filings by symbol and type.

    Per §6.1: Use https://efts.sec.gov/LATEST/search-index endpoint.
    Rate limit: max 10 requests/second to SEC.
    """
    params = {"q": symbol, "forms": filing_type}
    if start_date:
        params["dateRange"] = "custom"
        params["startdt"] = start_date
    if end_date:
        params["enddt"] = end_date

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{SEC_BASE_URL}/search-index",
            params=params,
            headers=_sec_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    hits = data.get("hits", {}).get("hits", [])
    results = []
    for hit in hits[:limit]:
        src = hit.get("_source", {})
        results.append({
            "accession_number": src.get("file_num", ""),
            "filing_type": src.get("form_type", filing_type),
            "filing_date": src.get("file_date", ""),
            "company_name": src.get("display_names", [""])[0] if src.get("display_names") else "",
            "filing_url": f"https://www.sec.gov/Archives/edgar/data/{src.get('entity_id', '')}/{src.get('file_num', '')}",
        })
    return results


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException)),
)
async def fetch_filing_document(url: str) -> str:
    """Download a raw SEC filing document (HTML) from its URL."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(url, headers=_sec_headers())
        resp.raise_for_status()
        return resp.text


# ---------------------------------------------------------------------------
# yfinance wrappers
# ---------------------------------------------------------------------------

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
    retry=retry_if_exception_type(Exception),
)
def fetch_yfinance_info(symbol: str) -> dict:
    """Fetch stock info from yfinance with retry (per §6.2)."""
    ticker = yf.Ticker(symbol)
    info = ticker.info
    if not info or info.get("regularMarketPrice") is None:
        # yfinance may return empty dict on failure
        raise ValueError(f"No data returned for {symbol}")
    return info


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
    retry=retry_if_exception_type(Exception),
)
def fetch_yfinance_history(symbol: str, period: str = "1y", interval: str = "1d") -> list[dict]:
    """Fetch OHLCV history from yfinance with retry."""
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    if df.empty:
        raise ValueError(f"No history returned for {symbol}")
    records = []
    for idx, row in df.iterrows():
        records.append({
            "date": idx.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 4),
            "high": round(float(row["High"]), 4),
            "low": round(float(row["Low"]), 4),
            "close": round(float(row["Close"]), 4),
            "volume": int(row["Volume"]),
        })
    return records


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
    retry=retry_if_exception_type(Exception),
)
def fetch_yfinance_financials(symbol: str) -> dict:
    """Fetch financial statements from yfinance."""
    ticker = yf.Ticker(symbol)
    return {
        "info": ticker.info or {},
        "financials": ticker.financials.to_dict() if ticker.financials is not None and not ticker.financials.empty else {},
        "balance_sheet": ticker.balance_sheet.to_dict() if ticker.balance_sheet is not None and not ticker.balance_sheet.empty else {},
        "cashflow": ticker.cashflow.to_dict() if ticker.cashflow is not None and not ticker.cashflow.empty else {},
    }


# ---------------------------------------------------------------------------
# FMP API
# ---------------------------------------------------------------------------

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException)),
)
async def fetch_fmp_earnings_transcript(
    symbol: str, year: int, quarter: int
) -> dict | None:
    """Fetch earnings call transcript from FMP API (per §6.5)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{FMP_BASE_URL}/earning_call_transcript/{symbol}",
            params=_fmp_params(year=year, quarter=quarter),
        )
        resp.raise_for_status()
        data = resp.json()

    if not data:
        return None
    transcript = data[0] if isinstance(data, list) else data
    return {
        "symbol": symbol,
        "year": year,
        "quarter": quarter,
        "date": transcript.get("date", ""),
        "content": transcript.get("content", ""),
    }


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException)),
)
async def fetch_fmp_financial_ratios(symbol: str) -> list[dict]:
    """Fetch financial ratios from FMP as fallback for yfinance."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{FMP_BASE_URL}/ratios/{symbol}",
            params=_fmp_params(limit=5),
        )
        resp.raise_for_status()
        return resp.json()
