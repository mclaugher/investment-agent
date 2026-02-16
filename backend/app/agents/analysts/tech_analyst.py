"""Technology sector analyst team (per §7.1).

Covers: AAPL, MSFT, NVDA, GOOGL, META, AVGO, ADBE, CRM, AMD, INTC
"""

from app.agents.analysts.base_analyst import create_sector_team

TECH_ADDITIONS = """
SECTOR-SPECIFIC FOCUS (Technology):
- R&D spending as % of revenue — trend over 3+ years
- Cloud/SaaS revenue mix and growth rates (ARR, NRR, RPO)
- Patent portfolio changes and IP litigation exposure
- AI/ML capital expenditure and monetization progress
- Semiconductor cycle positioning (for chip companies)
- Regulatory risk: antitrust, data privacy (GDPR, state laws)
- Customer concentration and platform dependency risks
- Stock-based compensation as % of revenue (dilution concern)
"""

TECH_SYMBOLS = ["AAPL", "MSFT", "NVDA", "GOOGL", "META",
                "AVGO", "ADBE", "CRM", "AMD", "INTC"]


def build_tech_team():
    """Build the technology sector analyst team."""
    return create_sector_team(
        sector_name="technology",
        tracked_symbols=TECH_SYMBOLS,
        sector_specific_additions=TECH_ADDITIONS,
    )
