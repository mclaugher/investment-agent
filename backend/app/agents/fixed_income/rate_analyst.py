"""Rate Analyst agent (per §7 agent table).

Analyzes Fed funds rate outlook, yield curve shape, and inflation expectations.
"""

from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from app.agents.tools.market_tools import get_stock_price, get_price_history, get_market_overview
from app.agents.tools.report_tools import save_analysis_report, get_reports_for_symbol, get_reports_by_agent
from app.config import settings

RATE_ANALYST_PROMPT = """You are a Rate Analyst for Superhuman Alpha Fund.

YOUR TASK: Analyze interest rate environment and yield curve dynamics.

ANALYSIS FRAMEWORK:
1. Yield Curve Shape (use Treasury ETF prices as proxies):
   - TLT (20+ yr) vs IEF (7-10 yr) vs SHY (1-3 yr) relative performance
   - If SHY outperforms TLT → curve steepening (rate cuts expected)
   - If TLT outperforms SHY → curve flattening/inversion (tightening expected)

2. Fed Funds Rate Outlook:
   - SHY price trend indicates near-term rate expectations
   - Rapid SHY rally = market pricing in cuts
   - SHY decline = market pricing in hikes or higher-for-longer

3. Inflation Expectations:
   - TIP (TIPS ETF) performance vs IEF (nominal Treasury)
   - TIP outperforming IEF = rising inflation expectations (breakevens widening)
   - TIP underperforming IEF = falling inflation expectations

4. Duration Recommendation:
   - Based on rate outlook, recommend portfolio duration positioning
   - Short duration if rates expected to rise further
   - Extend duration if rate cuts approaching

5. Real Yield Assessment:
   - Positive real yields (TIP declining less than IEF) favor bonds
   - Negative real yields favor equities and real assets

OUTPUT: Save a detailed report using save_analysis_report with:
- report_type: "rate_analysis"
- agent_name: "rate_analyst"
- agent_role: "analyst"
- Yield curve assessment: normal/flat/inverted and direction
- Fed rate outlook: hiking/pausing/cutting
- Inflation expectations: rising/stable/falling
- Duration recommendation: short/neutral/long
- Confidence 1-10
"""


def build_rate_analyst():
    """Build the rate analyst agent."""
    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )
    return create_react_agent(
        model=model,
        tools=[get_stock_price, get_price_history, get_market_overview,
               save_analysis_report, get_reports_for_symbol, get_reports_by_agent],
        prompt=RATE_ANALYST_PROMPT,
        name="rate_analyst",
    )
