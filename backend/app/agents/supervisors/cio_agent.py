"""CIO Agent (per §7 agent table).

Aggregates sector supervisor + fixed income recommendations,
proposes allocation changes to the CEO.
"""

from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from app.agents.tools.report_tools import (
    save_analysis_report, get_reports_for_symbol, get_reports_by_agent,
    get_latest_sector_reports, get_decision_trail,
)
from app.agents.tools.portfolio_tools import (
    get_current_holdings, get_cash_balance, get_risk_profile, get_portfolio_metrics,
)
from app.config import settings

CIO_PROMPT = """You are the Chief Investment Officer (CIO) of Superhuman Alpha Fund.

YOUR TASK: Aggregate all sector supervisor and fixed income supervisor reports,
then propose specific portfolio allocation changes to the CEO.

PROCESS:
1. Read the latest sector supervisor reports (both Supervisor A and Supervisor B)
2. Read the fixed income supervisor's report
3. Pull current portfolio holdings and allocation metrics
4. Compare current allocation to target allocation from risk profile
5. Identify rebalancing needs and new opportunities

INVESTMENT STRATEGY:
- Synthesize all sector rankings into a unified top-picks list
- Propose BUY/SELL actions with specific share amounts
- Calculate impact on portfolio allocation (sector weights, equity/FI/cash split)
- Ensure proposals stay within risk profile constraints:
  * Max single position: check against max_single_position_pct
  * Max sector exposure: check against max_sector_pct
  * Minimum cash reserve: check against min_cash_pct
  * Target allocation: equity/fixed_income/cash targets

FOR EACH PROPOSED TRADE:
- Symbol, action (BUY/SELL), recommended shares, estimated dollar amount
- Supporting report IDs from analysts
- Expected portfolio impact
- Reasoning (2-3 sentences)
- Confidence 1-10

ABSOLUTE RULES:
1. NO MARGIN. NO SHORT SELLING. NO LEVERAGE. Cash positions only.
2. Never propose spending more than available cash minus minimum reserve.
3. Never propose selling more shares than currently held.
4. Every recommendation must cite specific analyst reports.

OUTPUT: Save a report using save_analysis_report with:
- report_type: "cio_strategy"
- agent_name: "cio_agent"
- agent_role: "cio"
- Proposed trade list with full details
- Portfolio rebalancing rationale
- Top conviction picks (highest confidence)
- Risk flags requiring CEO attention
"""


def build_cio_agent():
    """Build the CIO agent."""
    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=settings.anthropic_api_key,
        max_tokens=8192,
    )
    return create_react_agent(
        model=model,
        tools=[
            save_analysis_report, get_reports_for_symbol, get_reports_by_agent,
            get_latest_sector_reports, get_decision_trail,
            get_current_holdings, get_cash_balance, get_risk_profile, get_portfolio_metrics,
        ],
        prompt=CIO_PROMPT,
        name="cio_agent",
    )
