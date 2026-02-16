"""Financials sector analyst team (per §7.1).

Covers: JPM, BAC, WFC, GS, MS, BLK, SCHW, AXP, C, USB
"""

from app.agents.analysts.base_analyst import create_sector_team

FINANCIALS_ADDITIONS = """
SECTOR-SPECIFIC FOCUS (Financials):
- Net interest margin (NIM) trends and rate sensitivity
- Loan loss provisions and charge-off rates
- CET1 capital ratios and stress test results (CCAR/DFAST)
- Trading revenue volatility (for investment banks)
- Assets under management (AUM) growth and fee compression
- Credit quality metrics: NPL ratio, delinquency rates
- Regulatory capital requirements and return on tangible equity (ROTCE)
- Deposit mix: non-interest-bearing vs interest-bearing, deposit beta
"""

FINANCIALS_SYMBOLS = ["JPM", "BAC", "WFC", "GS", "MS",
                      "BLK", "SCHW", "AXP", "C", "USB"]


def build_financials_team():
    """Build the financials sector analyst team."""
    return create_sector_team(
        sector_name="financials",
        tracked_symbols=FINANCIALS_SYMBOLS,
        sector_specific_additions=FINANCIALS_ADDITIONS,
    )
