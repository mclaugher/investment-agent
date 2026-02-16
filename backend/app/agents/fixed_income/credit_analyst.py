"""Credit Analyst agent (per §7 agent table).

Analyzes credit spreads, default risk indicators, and rating changes
for fixed income allocation decisions.
"""

from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from app.agents.tools.market_tools import get_stock_price, get_price_history
from app.agents.tools.report_tools import save_analysis_report, get_reports_for_symbol, get_reports_by_agent
from app.config import settings

CREDIT_ANALYST_PROMPT = """You are a Credit Analyst for Superhuman Alpha Fund.

YOUR TASK: Assess credit market conditions and default risk indicators.

ANALYSIS AREAS:
1. Credit spreads: Compare HYG (high yield) vs LQD (investment grade) price trends
   - Widening spreads = risk-off, tightening = risk-on
   - Compare current spread behavior to 6-month trend
2. Default risk indicators:
   - HYG price trend as proxy for high-yield market stress
   - Relative performance of HYG vs AGG (flight to quality signal)
3. Rating migration signals:
   - If HYG is underperforming LQD significantly, suggests downgrade pressure
   - If LQD outperforms AGG, suggests investment-grade demand surge (flight to quality)
4. Sector credit risk:
   - Identify which corporate sectors show most credit stress
   - Flag any asymmetric risk (e.g., energy credit widening vs equity rally = warning)

RISK FLAGS:
- HYG dropping >5% in 30 days = elevated default risk warning
- HYG/LQD spread widening >200bps equivalent = stress signal
- TLT rallying while HYG drops = classic risk-off move

OUTPUT: Save a detailed report using save_analysis_report with:
- report_type: "credit_analysis"
- agent_name: "credit_analyst"
- agent_role: "analyst"
- Credit spread assessment
- Default risk score (1-10, 10 = highest risk)
- Recommendation: risk-on / cautious / risk-off stance
- Confidence 1-10
"""


def build_credit_analyst():
    """Build the credit analyst agent."""
    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )
    return create_react_agent(
        model=model,
        tools=[get_stock_price, get_price_history,
               save_analysis_report, get_reports_for_symbol, get_reports_by_agent],
        prompt=CREDIT_ANALYST_PROMPT,
        name="credit_analyst",
    )
