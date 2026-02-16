"""Bond Analyst agent (per §7 agent table).

Analyzes Treasury yields, corporate bond ETF performance, and duration risk
for the fixed income portfolio allocation.
"""

from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from app.agents.tools.market_tools import get_stock_price, get_price_history, get_sector_etf_performance
from app.agents.tools.report_tools import save_analysis_report, get_reports_for_symbol, get_reports_by_agent
from app.config import settings

BOND_ETFS = ["AGG", "BND", "TLT", "IEF", "LQD", "HYG", "TIP", "SHY"]

BOND_ANALYST_PROMPT = f"""You are a Bond Analyst for Superhuman Alpha Fund.

YOUR TASK: Analyze fixed income ETFs and Treasury market conditions.

COVERED INSTRUMENTS: {', '.join(BOND_ETFS)}

FOR EACH BOND ETF:
1. Pull current price and recent price trend (30-day, 90-day)
2. Analyze yield changes by comparing price movements (inverse relationship)
3. Assess duration risk: how sensitive is each ETF to rate changes?
4. Compare investment-grade (LQD) vs high-yield (HYG) spread behavior
5. Evaluate Treasury curve: TLT vs IEF vs SHY price trends indicate curve shape
6. Check TIPS (TIP) for inflation expectations signal

ANALYSIS FRAMEWORK:
- Duration positioning: should we be long or short duration?
- Credit quality preference: investment grade vs high yield
- Curve positioning: steepener vs flattener implications
- Real yield assessment via TIPS performance

OUTPUT: Save a detailed report using save_analysis_report with:
- report_type: "bond_analysis"
- agent_name: "bond_analyst"
- agent_role: "analyst"
- Specific price data and yield proxies
- Duration risk assessment
- Recommendation: overweight/underweight/neutral for each segment
- Confidence 1-10
"""


def build_bond_analyst():
    """Build the bond analyst agent."""
    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )
    return create_react_agent(
        model=model,
        tools=[get_stock_price, get_price_history, get_sector_etf_performance,
               save_analysis_report, get_reports_for_symbol, get_reports_by_agent],
        prompt=BOND_ANALYST_PROMPT,
        name="bond_analyst",
    )
