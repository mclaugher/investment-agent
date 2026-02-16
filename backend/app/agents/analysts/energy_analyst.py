"""Energy sector analyst team (per §7.1).

Covers: XOM, CVX, COP, SLB, EOG, MPC, PSX, VLO, OXY, HAL
"""

from app.agents.analysts.base_analyst import create_sector_team

ENERGY_ADDITIONS = """
SECTOR-SPECIFIC FOCUS (Energy):
- Breakeven oil/gas prices per basin and production cost curves
- Reserve replacement ratio and proved reserves (PV-10)
- Capex discipline: maintenance vs growth capex split
- Refining crack spreads and utilization rates (for refiners)
- OPEC+ production decisions and spare capacity estimates
- Energy transition exposure: renewables investment, carbon intensity targets
- Midstream contract structure: take-or-pay, fee-based vs commodity-exposed
- Free cash flow yield and shareholder return programs (buybacks + dividends)
"""

ENERGY_SYMBOLS = ["XOM", "CVX", "COP", "SLB", "EOG",
                  "MPC", "PSX", "VLO", "OXY", "HAL"]


def build_energy_team():
    """Build the energy sector analyst team."""
    return create_sector_team(
        sector_name="energy",
        tracked_symbols=ENERGY_SYMBOLS,
        sector_specific_additions=ENERGY_ADDITIONS,
    )
