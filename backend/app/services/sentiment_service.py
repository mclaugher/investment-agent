"""Sentiment analysis pipeline — social + news (per §17 Phase 2, §6.4).

Social sentiment: pyfin-sentiment model.
News sentiment: FinBERT via transformers.
"""

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# FinBERT (lazy-loaded singleton)
# ---------------------------------------------------------------------------

_finbert_pipeline = None


def get_finbert_pipeline():
    """Lazy-load the FinBERT sentiment pipeline (per §6.4)."""
    global _finbert_pipeline
    if _finbert_pipeline is None:
        try:
            from transformers import pipeline
            _finbert_pipeline = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert",
                device=-1,  # CPU
            )
            logger.info("FinBERT pipeline loaded successfully")
        except Exception as e:
            logger.warning("Failed to load FinBERT, falling back to simple sentiment", error=str(e))
            _finbert_pipeline = "fallback"
    return _finbert_pipeline


def analyze_text_finbert(texts: list[str]) -> list[dict]:
    """Analyze a list of texts with FinBERT. Returns [{label, score}]."""
    pipe = get_finbert_pipeline()
    if pipe == "fallback":
        # Simple keyword-based fallback
        results = []
        positive_words = {"strong", "growth", "beat", "exceeded", "bullish", "upgrade", "record"}
        negative_words = {"weak", "miss", "decline", "bearish", "downgrade", "loss", "risk"}
        for text in texts:
            words = set(text.lower().split())
            pos = len(words & positive_words)
            neg = len(words & negative_words)
            if pos > neg:
                results.append({"label": "positive", "score": 0.7})
            elif neg > pos:
                results.append({"label": "negative", "score": 0.7})
            else:
                results.append({"label": "neutral", "score": 0.7})
        return results

    # Truncate texts to model max length
    truncated = [t[:512] for t in texts]
    return pipe(truncated)


# ---------------------------------------------------------------------------
# pyfin-sentiment wrapper
# ---------------------------------------------------------------------------

def analyze_social_text(texts: list[str]) -> list[dict]:
    """Classify texts as Bullish/Bearish/Neutral using pyfin-sentiment."""
    try:
        from pyfin_sentiment.model import SentimentModel
        model = SentimentModel()
        results = []
        for text in texts:
            score = model.predict([text])[0]
            if score > 0.3:
                label = "Bullish"
            elif score < -0.3:
                label = "Bearish"
            else:
                label = "Neutral"
            results.append({"text": text[:200], "sentiment": label, "score": float(score)})
        return results
    except Exception as e:
        logger.warning("pyfin-sentiment failed, using fallback", error=str(e))
        return [{"text": t[:200], "sentiment": "Neutral", "score": 0.0} for t in texts]
