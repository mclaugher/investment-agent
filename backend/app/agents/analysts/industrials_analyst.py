"""Industrials sector analyst team (per §7.1).

Covers: CAT, DE, UNP, HON, BA, RTX, GE, LMT, MMM, UPS
"""

from app.agents.analysts.base_analyst import create_sector_team

INDUSTRIALS_ADDITIONS = """
SECTOR-SPECIFIC FOCUS (Industrials):
- Order backlog trends and book-to-bill ratios
- Capacity utilization rates and capital expenditure cycles
- Defense budget exposure and government contract pipeline (for defense)
- Supply chain normalization: lead times, input availability
- PMI correlation and economic cycle positioning
- Aftermarket/services revenue as % of total (recurring revenue quality)
- Infrastructure spending tailwinds: IIJA, CHIPS Act allocations
- Labor availability and wage inflation in manufacturing
"""

INDUSTRIALS_SYMBOLS = ["CAT", "DE", "UNP", "HON", "BA",
                       "RTX", "GE", "LMT", "MMM", "UPS"]


def build_industrials_team():
    """Build the industrials sector analyst team."""
    return create_sector_team(
        sector_name="industrials",
        tracked_symbols=INDUSTRIALS_SYMBOLS,
        sector_specific_additions=INDUSTRIALS_ADDITIONS,
    )
