"""Utilities sector analyst team (per §7.1).

Covers: NEE, DUK, SO, D, AEP, EXC, SRE, XEL, ED, WEC
"""

from app.agents.analysts.base_analyst import create_sector_team

UTILITIES_ADDITIONS = """
SECTOR-SPECIFIC FOCUS (Utilities):
- Rate case outcomes and allowed ROE from regulators
- Regulated vs unregulated earnings mix
- Renewable energy transition: solar/wind capacity additions, IRA tax credits
- Capital expenditure plans: grid modernization, transmission buildout
- Fuel mix and exposure to natural gas price volatility
- Dividend growth rate sustainability and payout ratio
- Load growth trends: data center demand, EV charging, electrification
- Wildfire/weather liability exposure and insurance costs
"""

UTILITIES_SYMBOLS = ["NEE", "DUK", "SO", "D", "AEP",
                     "EXC", "SRE", "XEL", "ED", "WEC"]


def build_utilities_team():
    """Build the utilities sector analyst team."""
    return create_sector_team(
        sector_name="utilities",
        tracked_symbols=UTILITIES_SYMBOLS,
        sector_specific_additions=UTILITIES_ADDITIONS,
    )
