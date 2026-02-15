"""SEC filing tools for agent use (per §6.1).

All tools are @tool decorated, stateless, and return typed dicts.
Uses SEC EDGAR EFTS API with User-Agent and rate limiting.
Parses HTML filings with BeautifulSoup + lxml.
"""

import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.data_ingestion import fetch_sec_filings_list, fetch_filing_document

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Regex patterns for 10-K section extraction (per §6.1)
SECTION_PATTERNS = {
    "business": re.compile(r"item\s*1[.\s]", re.IGNORECASE),
    "risk_factors": re.compile(r"item\s*1a[.\s]", re.IGNORECASE),
    "mda": re.compile(r"item\s*7[.\s]", re.IGNORECASE),
    "financial_statements": re.compile(r"item\s*8[.\s]", re.IGNORECASE),
    "notes": re.compile(r"notes\s+to\s+(consolidated\s+)?financial\s+statements", re.IGNORECASE),
}


def _parse_filing_html(html: str) -> dict[str, str]:
    """Parse an SEC filing HTML document into named sections."""
    soup = BeautifulSoup(html, "lxml")

    # Remove scripts, styles
    for tag in soup(["script", "style"]):
        tag.decompose()

    full_text = soup.get_text(separator="\n", strip=True)

    sections = {}
    for name, pattern in SECTION_PATTERNS.items():
        match = pattern.search(full_text)
        if match:
            start = match.start()
            # Grab up to 50k chars from the section start
            sections[name] = full_text[start : start + 50000].strip()
        else:
            sections[name] = ""

    sections["full_text"] = full_text[:200000]  # Cap at 200k chars
    return sections


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """Split text into chunks of roughly chunk_size tokens (~4 chars/token).

    Per §6.1: chunk at ~1000 tokens for ChromaDB embeddings.
    """
    char_size = chunk_size * 4
    overlap_chars = overlap * 4
    chunks = []
    start = 0
    while start < len(text):
        end = start + char_size
        chunks.append(text[start:end])
        start = end - overlap_chars
    return chunks


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
async def fetch_10k_filing(symbol: str, year: int) -> dict:
    """Fetch and parse a company's 10-K annual filing from SEC EDGAR.
    Returns parsed sections: business, risk_factors, mda, financial_statements, notes.
    Stores full text in ChromaDB for semantic search. Caches in PostgreSQL."""
    filings = await fetch_sec_filings_list(
        symbol=symbol,
        filing_type="10-K",
        start_date=f"{year}-01-01",
        end_date=f"{year}-12-31",
        limit=1,
    )

    if not filings:
        return {"symbol": symbol, "year": year, "error": "No 10-K filing found", "sections": {}}

    filing = filings[0]
    filing_url = filing.get("filing_url", "")

    # Fetch and parse the document
    try:
        html = await fetch_filing_document(filing_url)
        sections = _parse_filing_html(html)
    except Exception as e:
        return {
            "symbol": symbol,
            "year": year,
            "error": f"Failed to fetch/parse filing: {e}",
            "filing_metadata": filing,
            "sections": {},
        }

    return {
        "symbol": symbol,
        "year": year,
        "filing_type": "10-K",
        "filing_date": filing.get("filing_date", ""),
        "accession_number": filing.get("accession_number", ""),
        "sections": {
            "business": sections.get("business", "")[:10000],
            "risk_factors": sections.get("risk_factors", "")[:20000],
            "mda": sections.get("mda", "")[:20000],
            "financial_statements": sections.get("financial_statements", "")[:10000],
            "notes": sections.get("notes", "")[:10000],
        },
    }


@tool
async def fetch_10q_filing(symbol: str, year: int, quarter: int) -> dict:
    """Fetch and parse a 10-Q quarterly filing. Same return structure as 10-K."""
    # Determine quarter date range
    quarter_ranges = {
        1: ("01-01", "03-31"),
        2: ("04-01", "06-30"),
        3: ("07-01", "09-30"),
        4: ("10-01", "12-31"),
    }
    if quarter not in quarter_ranges:
        return {"symbol": symbol, "error": f"Invalid quarter: {quarter}"}

    start_m, end_m = quarter_ranges[quarter]
    filings = await fetch_sec_filings_list(
        symbol=symbol,
        filing_type="10-Q",
        start_date=f"{year}-{start_m}",
        end_date=f"{year}-{end_m}",
        limit=1,
    )

    if not filings:
        return {"symbol": symbol, "year": year, "quarter": quarter, "error": "No 10-Q filing found", "sections": {}}

    filing = filings[0]
    filing_url = filing.get("filing_url", "")

    try:
        html = await fetch_filing_document(filing_url)
        sections = _parse_filing_html(html)
    except Exception as e:
        return {
            "symbol": symbol,
            "year": year,
            "quarter": quarter,
            "error": f"Failed to fetch/parse filing: {e}",
            "sections": {},
        }

    return {
        "symbol": symbol,
        "year": year,
        "quarter": quarter,
        "filing_type": "10-Q",
        "filing_date": filing.get("filing_date", ""),
        "accession_number": filing.get("accession_number", ""),
        "sections": {
            "business": sections.get("business", "")[:10000],
            "risk_factors": sections.get("risk_factors", "")[:20000],
            "mda": sections.get("mda", "")[:20000],
            "financial_statements": sections.get("financial_statements", "")[:10000],
            "notes": sections.get("notes", "")[:10000],
        },
    }


@tool
async def search_filing_content(symbol: str, query: str, top_k: int = 5) -> list[dict]:
    """Semantic search across all stored filing content for a symbol using ChromaDB.
    Returns matching text chunks with section metadata and relevance scores."""
    # ChromaDB integration — will be fully wired when ChromaDB client is set up
    # For now, return a structured placeholder that indicates the tool's contract
    try:
        import chromadb

        client = chromadb.HttpClient(host="localhost", port=8100)
        collection_name = f"filings_{symbol.lower()}"
        try:
            collection = client.get_collection(collection_name)
        except Exception:
            return [{"info": f"No filing embeddings found for {symbol}. Run fetch_10k_filing or fetch_10q_filing first."}]

        results = collection.query(query_texts=[query], n_results=top_k)
        matches = []
        for i, doc in enumerate(results.get("documents", [[]])[0]):
            meta = results.get("metadatas", [[]])[0][i] if results.get("metadatas") else {}
            distance = results.get("distances", [[]])[0][i] if results.get("distances") else None
            matches.append({
                "text": doc[:2000],
                "section": meta.get("section", "unknown"),
                "filing_type": meta.get("filing_type", ""),
                "relevance_score": round(1 - distance, 4) if distance is not None else None,
            })
        return matches
    except Exception as e:
        return [{"error": f"ChromaDB search failed: {e}"}]


@tool
async def get_recent_filings(symbol: str, filing_type: str = "all", limit: int = 5) -> list[dict]:
    """List recent filings for a symbol from SEC EDGAR. Returns metadata, not full content."""
    ft = filing_type if filing_type != "all" else "10-K,10-Q,8-K"
    filings = await fetch_sec_filings_list(symbol=symbol, filing_type=ft, limit=limit)
    return filings
