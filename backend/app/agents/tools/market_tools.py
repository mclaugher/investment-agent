"""Market data tools for agent use (per §6.2).

All tools are @tool decorated, stateless, and return typed dicts.
yfinance calls wrapped in tenacity retry via data_ingestion service.
"""

from langchain_core.tools import tool

from app.services.data_ingestion import fetch_yfinance_info, fetch_yfinance_history

# Sector ETF mapping per §6.2
SECTOR_ETF_MAP = {
    "technology": "XLK",
    "healthcare": "XLV",
    "financials": "XLF",
    "energy": "XLE",
    "consumer_discretionary": "XLY",
    "consumer_staples": "XLP",
    "consumer": "XLY",
    "industrials": "XLI",
    "real_estate": "XLRE",
    "utilities": "XLU",
}

MARKET_INDICES = ["SPY", "QQQ", "DIA", "IWM"]
VIX_SYMBOL = "^VIX"


@tool
def get_stock_price(symbol: str) -> dict:
    """Get current stock price, volume, day change, 52-week range via yfinance.
    Returns: {symbol, price, change, change_pct, volume, high_52w, low_52w, market_cap}"""
    info = fetch_yfinance_info(symbol)
    price = info.get("regularMarketPrice") or info.get("currentPrice", 0)
    prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose", price)
    change = round(price - prev_close, 4)
    change_pct = round((change / prev_close) * 100, 2) if prev_close else 0
    return {
        "symbol": symbol,
        "price": price,
        "change": change,
        "change_pct": change_pct,
        "volume": info.get("regularMarketVolume") or info.get("volume", 0),
        "high_52w": info.get("fiftyTwoWeekHigh", 0),
        "low_52w": info.get("fiftyTwoWeekLow", 0),
        "market_cap": info.get("marketCap", 0),
    }


@tool
def get_price_history(symbol: str, period: str = "1y", interval: str = "1d") -> dict:
    """Get historical OHLCV data. period: 1mo,3mo,6mo,1y,2y,5y. interval: 1d,1wk,1mo.
    Returns: {symbol, period, data: [{date, open, high, low, close, volume}]}"""
    valid_periods = {"1mo", "3mo", "6mo", "1y", "2y", "5y"}
    valid_intervals = {"1d", "1wk", "1mo"}
    if period not in valid_periods:
        period = "1y"
    if interval not in valid_intervals:
        interval = "1d"

    data = fetch_yfinance_history(symbol, period=period, interval=interval)
    return {"symbol": symbol, "period": period, "data": data}


@tool
def get_market_overview() -> dict:
    """Get major market indices (SPY, QQQ, DIA, IWM), VIX, sector ETF performance.
    Returns: {indices: [...], vix: float, sectors: [...]}"""
    indices = []
    for idx_symbol in MARKET_INDICES:
        try:
            info = fetch_yfinance_info(idx_symbol)
            price = info.get("regularMarketPrice") or info.get("currentPrice", 0)
            prev = info.get("regularMarketPreviousClose") or info.get("previousClose", price)
            change = round(price - prev, 4) if prev else 0
            change_pct = round((change / prev) * 100, 2) if prev else 0
            indices.append({
                "symbol": idx_symbol,
                "price": price,
                "change": change,
                "change_pct": change_pct,
            })
        except Exception:
            indices.append({"symbol": idx_symbol, "price": 0, "change": 0, "change_pct": 0})

    # VIX
    vix = 0.0
    try:
        vix_info = fetch_yfinance_info(VIX_SYMBOL)
        vix = vix_info.get("regularMarketPrice") or vix_info.get("currentPrice", 0)
    except Exception:
        pass

    # Sector ETFs
    sectors = []
    sector_etfs = {"XLK", "XLV", "XLF", "XLE", "XLY", "XLP", "XLI", "XLRE", "XLU"}
    for etf in sorted(sector_etfs):
        try:
            info = fetch_yfinance_info(etf)
            price = info.get("regularMarketPrice") or info.get("currentPrice", 0)
            prev = info.get("regularMarketPreviousClose") or info.get("previousClose", price)
            change_pct = round(((price - prev) / prev) * 100, 2) if prev else 0
            sectors.append({"symbol": etf, "price": price, "change_pct": change_pct})
        except Exception:
            sectors.append({"symbol": etf, "price": 0, "change_pct": 0})

    return {"indices": indices, "vix": vix, "sectors": sectors}


@tool
def get_sector_etf_performance(sector: str) -> dict:
    """Get performance data for a specific sector's representative ETF.
    Sector mapping: technology->XLK, healthcare->XLV, financials->XLF, energy->XLE,
    consumer->XLY+XLP, industrials->XLI, real_estate->XLRE, utilities->XLU"""
    etf = SECTOR_ETF_MAP.get(sector.lower())
    if not etf:
        return {"error": f"Unknown sector: {sector}", "known_sectors": list(SECTOR_ETF_MAP.keys())}

    info = fetch_yfinance_info(etf)
    price = info.get("regularMarketPrice") or info.get("currentPrice", 0)
    prev = info.get("regularMarketPreviousClose") or info.get("previousClose", price)
    change_pct = round(((price - prev) / prev) * 100, 2) if prev else 0

    history = fetch_yfinance_history(etf, period="1y", interval="1d")

    # Calculate period returns from history
    returns = {}
    if history:
        current = history[-1]["close"]
        for label, days in [("1mo", 21), ("3mo", 63), ("6mo", 126), ("1y", 252)]:
            if len(history) >= days:
                past = history[-days]["close"]
                returns[label] = round(((current - past) / past) * 100, 2)

    return {
        "sector": sector,
        "etf_symbol": etf,
        "price": price,
        "daily_change_pct": change_pct,
        "returns": returns,
        "high_52w": info.get("fiftyTwoWeekHigh", 0),
        "low_52w": info.get("fiftyTwoWeekLow", 0),
    }
