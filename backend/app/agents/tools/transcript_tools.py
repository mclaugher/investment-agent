"""Earnings transcript tools for agent use (per §6.5).

Primary source: FMP API. Store in EarningsTranscript table + ChromaDB.
"""

import re

from langchain_core.tools import tool

from app.services.data_ingestion import fetch_fmp_earnings_transcript
from app.services.sentiment_service import analyze_text_finbert


def _extract_speaker_sections(text: str) -> dict[str, str]:
    """Parse transcript for CEO/CFO remarks and Q&A section."""
    sections = {"ceo_remarks": "", "cfo_remarks": "", "qa_section": ""}

    # Look for Q&A section
    qa_patterns = [
        re.compile(r"(question[- ]and[- ]answer|q\s*&\s*a\s+session|operator:.*question)", re.IGNORECASE),
    ]
    for pattern in qa_patterns:
        match = pattern.search(text)
        if match:
            sections["qa_section"] = text[match.start():][:30000]
            break

    # Look for CEO/CFO remarks in prepared remarks
    ceo_pattern = re.compile(
        r"(chief executive officer|ceo|president).*?(?=chief financial|cfo|operator|question|$)",
        re.IGNORECASE | re.DOTALL,
    )
    cfo_pattern = re.compile(
        r"(chief financial officer|cfo).*?(?=operator|question|chief executive|$)",
        re.IGNORECASE | re.DOTALL,
    )

    ceo_match = ceo_pattern.search(text[:len(text) // 2])  # Usually in first half
    if ceo_match:
        sections["ceo_remarks"] = ceo_match.group(0)[:20000]

    cfo_match = cfo_pattern.search(text[:len(text) // 2])
    if cfo_match:
        sections["cfo_remarks"] = cfo_match.group(0)[:20000]

    return sections


@tool
async def get_earnings_transcript(symbol: str, year: int, quarter: int) -> dict:
    """Fetch earnings call transcript from FMP API.
    Returns: {symbol, year, quarter, date, full_text, sections}"""
    result = await fetch_fmp_earnings_transcript(symbol, year, quarter)

    if not result or not result.get("content"):
        return {
            "symbol": symbol,
            "year": year,
            "quarter": quarter,
            "error": "Transcript not available",
            "full_text": "",
            "sections": {},
        }

    full_text = result["content"]
    sections = _extract_speaker_sections(full_text)

    return {
        "symbol": symbol,
        "year": year,
        "quarter": quarter,
        "date": result.get("date", ""),
        "full_text": full_text[:50000],  # Cap for context window
        "sections": {
            "ceo_remarks": sections["ceo_remarks"][:10000],
            "cfo_remarks": sections["cfo_remarks"][:10000],
            "qa_section": sections["qa_section"][:15000],
        },
    }


@tool
def analyze_transcript_sentiment(transcript_text: str) -> dict:
    """Run NLP sentiment analysis on earnings call text.
    Returns: {overall_sentiment, confidence_indicators, hedging_language_count,
              forward_looking_statements, key_phrases}"""
    if not transcript_text:
        return {"overall_sentiment": 0.0, "error": "Empty transcript text"}

    # Split into sentences for analysis
    sentences = [s.strip() for s in transcript_text.split(".") if len(s.strip()) > 20][:50]

    if not sentences:
        return {"overall_sentiment": 0.0, "error": "No analyzable sentences"}

    results = analyze_text_finbert(sentences)

    # Overall sentiment
    sentiment_sum = 0.0
    for r in results:
        label = r.get("label", "neutral").lower()
        score = r.get("score", 0.5)
        if label == "positive":
            sentiment_sum += score
        elif label == "negative":
            sentiment_sum -= score

    overall = round(sentiment_sum / len(results), 4) if results else 0.0

    # Detect confidence indicators
    confidence_words = ["confident", "strong", "robust", "excellent", "outstanding", "record"]
    confidence_indicators = [
        s for s in sentences
        if any(w in s.lower() for w in confidence_words)
    ][:5]

    # Count hedging language
    hedging_words = ["may", "might", "could", "potentially", "uncertain", "challenging", "headwind"]
    hedging_count = sum(
        1 for s in sentences
        if any(w in s.lower() for w in hedging_words)
    )

    # Forward-looking statements
    forward_words = ["expect", "anticipate", "outlook", "guidance", "forecast", "project", "target"]
    forward_count = sum(
        1 for s in sentences
        if any(w in s.lower() for w in forward_words)
    )

    # Key phrases with sentiment
    key_phrases = []
    for s, r in zip(sentences[:20], results[:20]):
        score = r.get("score", 0.5)
        label = r.get("label", "neutral").lower()
        if score > 0.7 and label != "neutral":
            key_phrases.append({
                "phrase": s[:200],
                "sentiment": label,
                "context": "earnings_call",
            })

    return {
        "overall_sentiment": overall,
        "confidence_indicators": confidence_indicators,
        "hedging_language_count": hedging_count,
        "forward_looking_statements": forward_count,
        "key_phrases": key_phrases[:10],
    }


@tool
async def compare_guidance(symbol: str, current_quarter: dict | None = None) -> dict:
    """Compare current quarter guidance language against previous 4 quarters.
    Detects: raised/lowered/maintained guidance, tone shifts, new risk mentions.
    Returns: {guidance_trend, quarter_comparison, notable_changes}"""
    # Fetch up to 5 quarters of transcripts
    import datetime

    now = datetime.date.today()
    year = now.year
    quarter = (now.month - 1) // 3 + 1

    quarters_to_check = []
    y, q = year, quarter
    for _ in range(5):
        quarters_to_check.append((y, q))
        q -= 1
        if q == 0:
            q = 4
            y -= 1

    transcripts = []
    for yr, qr in quarters_to_check:
        try:
            result = await fetch_fmp_earnings_transcript(symbol, yr, qr)
            if result and result.get("content"):
                transcripts.append({"year": yr, "quarter": qr, "content": result["content"]})
        except Exception:
            continue

    if len(transcripts) < 2:
        return {
            "symbol": symbol,
            "guidance_trend": "insufficient_data",
            "quarter_comparison": [],
            "notable_changes": ["Not enough transcript data for comparison"],
        }

    # Analyze each transcript
    quarter_comparison = []
    guidance_words = ["guidance", "outlook", "expect", "target", "forecast", "raise", "lower", "maintain"]

    for t in transcripts:
        sentences = [s.strip() for s in t["content"].split(".") if len(s.strip()) > 20]
        guidance_mentions = [
            s for s in sentences
            if any(w in s.lower() for w in guidance_words)
        ]

        # Simple tone scoring
        results = analyze_text_finbert(guidance_mentions[:10]) if guidance_mentions else []
        tone = 0.0
        for r in results:
            if r.get("label", "").lower() == "positive":
                tone += r.get("score", 0)
            elif r.get("label", "").lower() == "negative":
                tone -= r.get("score", 0)
        tone = round(tone / max(len(results), 1), 4)

        quarter_comparison.append({
            "quarter": f"Q{t['quarter']} {t['year']}",
            "key_metrics_mentioned": len(guidance_mentions),
            "tone_score": tone,
        })

    # Determine trend from tone scores
    if len(quarter_comparison) >= 2:
        recent = quarter_comparison[0]["tone_score"]
        prior = quarter_comparison[1]["tone_score"]
        if recent > prior + 0.1:
            trend = "improving"
        elif recent < prior - 0.1:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    notable = []
    if trend == "improving":
        notable.append("Management tone has become more positive in recent quarters")
    elif trend == "declining":
        notable.append("Management tone has shifted more cautious/negative recently")

    return {
        "symbol": symbol,
        "guidance_trend": trend,
        "quarter_comparison": quarter_comparison,
        "notable_changes": notable,
    }
