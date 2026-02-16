"""Real estate sector analyst team (per §7.1).

Covers: PLD, AMT, CCI, EQIX, SPG, PSA, O, WELL, DLR, AVB
"""

from app.agents.analysts.base_analyst import create_sector_team

REALESTATE_ADDITIONS = """
SECTOR-SPECIFIC FOCUS (Real Estate / REITs):
- FFO and AFFO per share trends (primary REIT valuation metrics)
- Occupancy rates and lease renewal spreads
- Weighted average lease term (WALT) and tenant quality
- Cap rate trends vs interest rates — NAV discount/premium
- Development pipeline: projects under construction, expected yields
- Debt maturity profile and variable-rate exposure
- Dividend payout ratio (as % of AFFO) and distribution coverage
- Sub-sector dynamics: data center demand, industrial logistics, office return-to-work
"""

REALESTATE_SYMBOLS = ["PLD", "AMT", "CCI", "EQIX", "SPG",
                      "PSA", "O", "WELL", "DLR", "AVB"]


def build_realestate_team():
    """Build the real estate sector analyst team."""
    return create_sector_team(
        sector_name="real_estate",
        tracked_symbols=REALESTATE_SYMBOLS,
        sector_specific_additions=REALESTATE_ADDITIONS,
    )
