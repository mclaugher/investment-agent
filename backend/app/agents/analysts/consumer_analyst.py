"""Consumer sector analyst team (per §7.1).

Covers: AMZN, TSLA, HD, MCD, NKE, SBUX, PG, KO, PEP, COST
"""

from app.agents.analysts.base_analyst import create_sector_team

CONSUMER_ADDITIONS = """
SECTOR-SPECIFIC FOCUS (Consumer):
- Same-store sales growth (comps) and traffic vs ticket trends
- Consumer confidence correlation and spending pattern shifts
- Input cost pressures: commodities, labor, freight
- Pricing power: ability to pass through inflation without volume loss
- E-commerce penetration and omnichannel strategy execution
- Brand strength metrics: NPS, market share trends
- Inventory levels: days of inventory, markdown risk
- International revenue mix and FX headwinds/tailwinds
"""

CONSUMER_SYMBOLS = ["AMZN", "TSLA", "HD", "MCD", "NKE",
                    "SBUX", "PG", "KO", "PEP", "COST"]


def build_consumer_team():
    """Build the consumer sector analyst team."""
    return create_sector_team(
        sector_name="consumer",
        tracked_symbols=CONSUMER_SYMBOLS,
        sector_specific_additions=CONSUMER_ADDITIONS,
    )
