"""Macro Supervisor (per §7 agent table).

Coordinates macro analyst and geopolitical analyst, synthesizes economic environment.
Reports directly to CEO.
"""

from langchain_anthropic import ChatAnthropic
from langgraph_supervisor import create_supervisor

from app.agents.macro.macro_analyst import build_macro_analyst
from app.agents.macro.geopolitical_analyst import build_geopolitical_analyst
from app.config import settings

MACRO_SUPERVISOR_PROMPT = """You are the Macro Supervisor for Superhuman Alpha Fund.

YOUR TASK: Coordinate the macro analyst and geopolitical analyst, then synthesize
their findings into a comprehensive economic backdrop for the CEO's decisions.

PROCESS:
1. Review the Macro Analyst's economic cycle and market risk assessment
2. Review the Geopolitical Analyst's risk assessment and sector-specific flags
3. Synthesize into a unified macro outlook that informs portfolio positioning

SYNTHESIS:
- Economic cycle positioning and what it means for sector allocation
- Key macro risks that could trigger portfolio adjustments
- Geopolitical risks that affect specific holdings
- Overall risk environment assessment
- Whether current conditions favor risk-on or risk-off positioning

OUTPUT: Save a report using save_analysis_report with:
- report_type: "macro_overview"
- agent_name: "macro_supervisor"
- agent_role: "supervisor"
- Economic cycle: early/mid/late/recession
- Risk environment: risk-on/neutral/risk-off
- Top 3 macro risks ranked by portfolio impact
- Sector allocation implications
- 30-day outlook
- Confidence 1-10
"""


def build_macro_team():
    """Build the macro supervisor with its 2 analysts."""
    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )

    macro_analyst = build_macro_analyst()
    geopolitical_analyst = build_geopolitical_analyst()

    supervisor = create_supervisor(
        agents=[macro_analyst, geopolitical_analyst],
        model=model,
        prompt=MACRO_SUPERVISOR_PROMPT,
        supervisor_name="macro_supervisor",
    )

    return supervisor.compile(name="macro_team")
