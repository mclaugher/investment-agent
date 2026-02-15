#!/usr/bin/env python
"""Seed the stock universe by GICS sector + major bond ETFs (per §3, §5.1, §17 Phase 1).

This populates a `stock_universe` table-like structure used by the orchestrator
to know which symbols each sector team covers.  For Phase 1 we store the universe
as holdings with shares=0 (watchlist mode) so the existing model layer can query it.

Alternatively the orchestrator can import STOCK_UNIVERSE directly from this module.

Usage:
    python -m scripts.seed_universe          # from repo root
    python scripts/seed_universe.py          # direct invocation
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

# ---------------------------------------------------------------------------
# Canonical stock universe — S&P 500 representative picks per sector + bond ETFs
# The orchestrator reads this dict to build sector teams (per §8.1).
# ---------------------------------------------------------------------------

STOCK_UNIVERSE: dict[str, list[str]] = {
    "technology": [
        "AAPL", "MSFT", "NVDA", "GOOGL", "META",
        "AVGO", "ADBE", "CRM", "AMD", "INTC",
    ],
    "healthcare": [
        "UNH", "JNJ", "LLY", "PFE", "ABBV",
        "MRK", "TMO", "ABT", "DHR", "BMY",
    ],
    "financials": [
        "JPM", "BAC", "WFC", "GS", "MS",
        "BLK", "SCHW", "AXP", "C", "USB",
    ],
    "energy": [
        "XOM", "CVX", "COP", "SLB", "EOG",
        "MPC", "PSX", "VLO", "OXY", "HAL",
    ],
    "consumer": [
        "AMZN", "TSLA", "HD", "MCD", "NKE",
        "SBUX", "PG", "KO", "PEP", "COST",
    ],
    "industrials": [
        "CAT", "DE", "UNP", "HON", "BA",
        "RTX", "GE", "LMT", "MMM", "UPS",
    ],
    "real_estate": [
        "PLD", "AMT", "CCI", "EQIX", "SPG",
        "PSA", "O", "WELL", "DLR", "AVB",
    ],
    "utilities": [
        "NEE", "DUK", "SO", "D", "AEP",
        "EXC", "SRE", "XEL", "ED", "WEC",
    ],
}

BOND_ETFS: list[str] = [
    "AGG",   # iShares Core U.S. Aggregate Bond
    "BND",   # Vanguard Total Bond Market
    "TLT",   # iShares 20+ Year Treasury Bond
    "IEF",   # iShares 7-10 Year Treasury Bond
    "LQD",   # iShares Investment Grade Corporate Bond
    "HYG",   # iShares High Yield Corporate Bond
    "TIP",   # iShares TIPS Bond
    "SHY",   # iShares 1-3 Year Treasury Bond
]

# Sector ETF mapping (used by market_tools.get_sector_etf_performance, §6.2)
SECTOR_ETFS: dict[str, str] = {
    "technology": "XLK",
    "healthcare": "XLV",
    "financials": "XLF",
    "energy": "XLE",
    "consumer": "XLY",
    "industrials": "XLI",
    "real_estate": "XLRE",
    "utilities": "XLU",
}


def print_universe_summary() -> None:
    """Print a summary of the stock universe."""
    total = sum(len(syms) for syms in STOCK_UNIVERSE.values())
    print(f"[seed_universe] Stock universe: {total} equities across {len(STOCK_UNIVERSE)} sectors")
    for sector, symbols in STOCK_UNIVERSE.items():
        print(f"  {sector:15s} ({len(symbols):2d}): {', '.join(symbols)}")
    print(f"[seed_universe] Bond ETFs ({len(BOND_ETFS)}): {', '.join(BOND_ETFS)}")
    print(f"[seed_universe] Sector ETFs ({len(SECTOR_ETFS)}): {', '.join(f'{k}={v}' for k, v in SECTOR_ETFS.items())}")


if __name__ == "__main__":
    print_universe_summary()
    print("\n[seed_universe] Universe data is available as STOCK_UNIVERSE, BOND_ETFS, SECTOR_ETFS.")
    print("[seed_universe] The orchestrator imports these directly — no DB write needed for Phase 1.")
