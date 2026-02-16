"""Healthcare sector analyst team (per §7.1).

Covers: UNH, JNJ, LLY, PFE, ABBV, MRK, TMO, ABT, DHR, BMY
"""

from app.agents.analysts.base_analyst import create_sector_team

HEALTHCARE_ADDITIONS = """
SECTOR-SPECIFIC FOCUS (Healthcare):
- Pipeline analysis: Phase I/II/III drugs, probability of approval
- Patent cliff exposure — key drug expiration dates and revenue at risk
- FDA approval/rejection catalysts and PDUFA dates
- Pricing pressure: PBM negotiations, IRA drug price provisions
- M&A activity: bolt-on acquisitions, pipeline purchases
- Medicare/Medicaid reimbursement rate changes
- Biosimilar competition for off-patent biologics
- Medical device regulatory clearance (510(k) vs PMA pathway)
"""

HEALTHCARE_SYMBOLS = ["UNH", "JNJ", "LLY", "PFE", "ABBV",
                      "MRK", "TMO", "ABT", "DHR", "BMY"]


def build_healthcare_team():
    """Build the healthcare sector analyst team."""
    return create_sector_team(
        sector_name="healthcare",
        tracked_symbols=HEALTHCARE_SYMBOLS,
        sector_specific_additions=HEALTHCARE_ADDITIONS,
    )
