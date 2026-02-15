"""Sentiment analysis tools for agent use (per §6.4).

Social sentiment: pyfin-sentiment.
News sentiment: FinBERT via transformers.
Insider trading: SEC EDGAR Form 4 / FMP API.
"""

import httpx
from langchain_core.tools import tool
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.services.sentiment_service import analyze_text_finbert, analyze_social_text


@tool
def get_social_sentiment(symbol: str) -> dict:
    """Analyze social media sentiment for a stock using pyfin-sentiment.
    Returns: {symbol, bullish_pct, bearish_pct, neutral_pct, sample_size,
              notable_posts, trend}"""
    # In production, this would scrape Reddit/Twitter. For now, use yfinance news as proxy.
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        news = ticker.news or []
        texts = [item.get("title", "") for item in news[:20] if item.get("title")]
    except Exception:
        texts = []

    if not texts:
        return {
            "symbol": symbol,
            "bullish_pct": 0,
            "bearish_pct": 0,
            "neutral_pct": 100,
            "sample_size": 0,
            "notable_posts": [],
            "trend": "stable",
        }

    results = analyze_social_text(texts)

    bullish = sum(1 for r in results if r["sentiment"] == "Bullish")
    bearish = sum(1 for r in results if r["sentiment"] == "Bearish")
    neutral = sum(1 for r in results if r["sentiment"] == "Neutral")
    total = len(results)

    bullish_pct = round(bullish / total * 100, 1) if total else 0
    bearish_pct = round(bearish / total * 100, 1) if total else 0
    neutral_pct = round(neutral / total * 100, 1) if total else 0

    # Simple trend determination
    if bullish_pct > 60:
        trend = "improving"
    elif bearish_pct > 60:
        trend = "declining"
    else:
        trend = "stable"

    notable = [r for r in results if abs(r.get("score", 0)) > 0.5][:5]

    return {
        "symbol": symbol,
        "bullish_pct": bullish_pct,
        "bearish_pct": bearish_pct,
        "neutral_pct": neutral_pct,
        "sample_size": total,
        "notable_posts": [{"text": n["text"], "sentiment": n["sentiment"], "source": "news"} for n in notable],
        "trend": trend,
    }


@tool
def get_news_sentiment(symbol: str, days: int = 7) -> dict:
    """Analyze recent news headlines using FinBERT.
    Returns: {symbol, avg_sentiment, positive_count, negative_count,
              neutral_count, headlines}"""
    # Fetch news headlines via yfinance
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        news = ticker.news or []
        headlines = [
            {"title": item.get("title", ""), "source": item.get("publisher", ""), "date": item.get("providerPublishTime", "")}
            for item in news[:20]
            if item.get("title")
        ]
    except Exception:
        headlines = []

    if not headlines:
        return {
            "symbol": symbol,
            "avg_sentiment": 0.0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "headlines": [],
        }

    texts = [h["title"] for h in headlines]
    results = analyze_text_finbert(texts)

    pos_count = 0
    neg_count = 0
    neu_count = 0
    sentiment_sum = 0.0

    enriched_headlines = []
    for h, r in zip(headlines, results):
        label = r.get("label", "neutral").lower()
        score = r.get("score", 0.5)

        if label == "positive":
            pos_count += 1
            sentiment_sum += score
        elif label == "negative":
            neg_count += 1
            sentiment_sum -= score
        else:
            neu_count += 1

        enriched_headlines.append({
            "title": h["title"],
            "sentiment": label,
            "score": round(score, 4),
            "source": h["source"],
            "date": h.get("date", ""),
        })

    total = len(results)
    avg_sentiment = round(sentiment_sum / total, 4) if total else 0.0

    return {
        "symbol": symbol,
        "avg_sentiment": avg_sentiment,
        "positive_count": pos_count,
        "negative_count": neg_count,
        "neutral_count": neu_count,
        "headlines": enriched_headlines,
    }


@tool
async def get_insider_trading(symbol: str, months: int = 6) -> dict:
    """Get recent insider trading activity (Form 4 filings).
    Returns: {symbol, net_insider_sentiment, total_buys, total_sells, notable}"""
    # Try FMP API first
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"https://financialmodelingprep.com/api/v3/insider-trading",
                params={"symbol": symbol, "apikey": settings.fmp_api_key, "limit": 50},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        data = []

    if not data:
        return {
            "symbol": symbol,
            "net_insider_sentiment": "neutral",
            "total_buys": 0,
            "total_sells": 0,
            "notable": [],
        }

    total_buys = 0
    total_sells = 0
    notable = []

    for entry in data[:50]:
        action = (entry.get("transactionType") or "").upper()
        if "PURCHASE" in action or "BUY" in action:
            total_buys += 1
        elif "SALE" in action or "SELL" in action:
            total_sells += 1

        if len(notable) < 10:
            notable.append({
                "name": entry.get("reportingName", ""),
                "title": entry.get("typeOfOwner", ""),
                "action": action,
                "shares": entry.get("securitiesTransacted", 0),
                "value": entry.get("price", 0) * entry.get("securitiesTransacted", 0),
                "date": entry.get("filingDate", ""),
            })

    if total_buys > total_sells * 1.5:
        sentiment = "buying"
    elif total_sells > total_buys * 1.5:
        sentiment = "selling"
    else:
        sentiment = "neutral"

    return {
        "symbol": symbol,
        "net_insider_sentiment": sentiment,
        "total_buys": total_buys,
        "total_sells": total_sells,
        "notable": notable,
    }
