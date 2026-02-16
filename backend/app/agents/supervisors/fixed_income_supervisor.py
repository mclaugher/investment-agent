"""Fixed Income Supervisor (per §7 agent table).

Aggregates bond, credit, and rate analyst reports into a fixed income recommendation.
"""

from langchain_anthropic import ChatAnthropic
from langgraph_supervisor import create_supervisor

from app.agents.fixed_income.bond_analyst import build_bond_analyst
from app.agents.fixed_income.credit_analyst import build_credit_analyst
from app.agents.fixed_income.rate_analyst import build_rate_analyst
from app.config import settings

FI_SUPERVISOR_PROMPT = """You are the Fixed Income Supervisor for Superhuman Alpha Fund.

YOUR TASK: Coordinate bond, credit, and rate analysts, then synthesize their findings
into a unified fixed income recommendation for the CIO.

PROCESS:
1. Review the Bond Analyst's report on Treasury and corporate bond ETF performance
2. Review the Credit Analyst's assessment of credit spreads and default risk
3. Review the Rate Analyst's yield curve and inflation expectations analysis
4. Synthesize into a cohesive fixed income outlook

SYNTHESIS FRAMEWORK:
- Duration positioning: aggregate the rate and bond analysts' views
- Credit quality allocation: weight credit analyst's risk assessment
- Overall fixed income allocation recommendation: overweight/neutral/underweight vs target
- Identify where analysts agree (high conviction) vs disagree

OUTPUT: Save a report using save_analysis_report with:
- report_type: "fixed_income_overview"
- agent_name: "fixed_income_supervisor"
- agent_role: "supervisor"
- Recommended FI allocation (% of portfolio)
- Duration stance: short/neutral/long
- Credit stance: risk-on/cautious/risk-off
- Key risks to fixed income portfolio
- Confidence 1-10
"""


def build_fixed_income_team():
    """Build the fixed income supervisor with its 3 analysts."""
    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )

    bond_analyst = build_bond_analyst()
    credit_analyst = build_credit_analyst()
    rate_analyst = build_rate_analyst()

    supervisor = create_supervisor(
        agents=[bond_analyst, credit_analyst, rate_analyst],
        model=model,
        prompt=FI_SUPERVISOR_PROMPT,
        supervisor_name="fixed_income_supervisor",
    )

    return supervisor.compile(name="fixed_income_team")
