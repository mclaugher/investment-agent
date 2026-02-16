"""Sector Supervisors (per §7 agent table).

Two sector supervisors split the 8 sectors:
- Supervisor A: technology, healthcare, financials
- Supervisor B: energy, consumer, industrials, real_estate, utilities

Each synthesizes reports from their sector teams and provides ranked recommendations to the CIO.
"""

from langchain_anthropic import ChatAnthropic
from langgraph_supervisor import create_supervisor

from app.agents.analysts.tech_analyst import build_tech_team
from app.agents.analysts.healthcare_analyst import build_healthcare_team
from app.agents.analysts.financials_analyst import build_financials_team
from app.agents.analysts.energy_analyst import build_energy_team
from app.agents.analysts.consumer_analyst import build_consumer_team
from app.agents.analysts.industrials_analyst import build_industrials_team
from app.agents.analysts.realestate_analyst import build_realestate_team
from app.agents.analysts.utilities_analyst import build_utilities_team
from app.config import settings


SECTOR_SUPERVISOR_A_PROMPT = """You are Sector Supervisor A for Superhuman Alpha Fund.

YOUR SECTORS: Technology, Healthcare, Financials

YOUR TASK: After each sector team has completed their analysis, synthesize findings
across your 3 sectors into a unified set of recommendations for the CIO.

PROCESS:
1. Review each sector team's overview report
2. Cross-compare opportunities across sectors — which sectors have the best risk/reward?
3. Rank all stocks across your sectors from strongest to weakest opportunity
4. Identify sector rotation signals (is money flowing between your sectors?)
5. Flag any cross-sector risks (e.g., rate sensitivity affecting both tech and financials)

OUTPUT: Save a report using save_analysis_report with:
- report_type: "sector_supervisor_overview"
- agent_name: "sector_supervisor_a"
- agent_role: "supervisor"
- Ranked stock recommendations across all 3 sectors
- Sector allocation recommendations (overweight/neutral/underweight each)
- Cross-sector themes and risks
- Confidence 1-10
"""

SECTOR_SUPERVISOR_B_PROMPT = """You are Sector Supervisor B for Superhuman Alpha Fund.

YOUR SECTORS: Energy, Consumer, Industrials, Real Estate, Utilities

YOUR TASK: After each sector team has completed their analysis, synthesize findings
across your 5 sectors into a unified set of recommendations for the CIO.

PROCESS:
1. Review each sector team's overview report
2. Cross-compare opportunities across sectors — which sectors have the best risk/reward?
3. Rank all stocks across your sectors from strongest to weakest opportunity
4. Identify sector rotation signals and economic cycle positioning
5. Flag cross-sector risks (e.g., rate sensitivity in REITs and utilities)

OUTPUT: Save a report using save_analysis_report with:
- report_type: "sector_supervisor_overview"
- agent_name: "sector_supervisor_b"
- agent_role: "supervisor"
- Ranked stock recommendations across all 5 sectors
- Sector allocation recommendations (overweight/neutral/underweight each)
- Cross-sector themes and risks
- Economic cycle implications for your sectors
- Confidence 1-10
"""


def build_sector_supervisor_a():
    """Build sector supervisor A (technology, healthcare, financials)."""
    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )

    tech_team = build_tech_team()
    healthcare_team = build_healthcare_team()
    financials_team = build_financials_team()

    supervisor = create_supervisor(
        agents=[tech_team, healthcare_team, financials_team],
        model=model,
        prompt=SECTOR_SUPERVISOR_A_PROMPT,
        supervisor_name="sector_supervisor_a",
    )

    return supervisor.compile(name="sector_group_a")


def build_sector_supervisor_b():
    """Build sector supervisor B (energy, consumer, industrials, real_estate, utilities)."""
    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )

    energy_team = build_energy_team()
    consumer_team = build_consumer_team()
    industrials_team = build_industrials_team()
    realestate_team = build_realestate_team()
    utilities_team = build_utilities_team()

    supervisor = create_supervisor(
        agents=[energy_team, consumer_team, industrials_team, realestate_team, utilities_team],
        model=model,
        prompt=SECTOR_SUPERVISOR_B_PROMPT,
        supervisor_name="sector_supervisor_b",
    )

    return supervisor.compile(name="sector_group_b")
