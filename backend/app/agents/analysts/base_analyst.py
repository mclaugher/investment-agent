"""Sector team factory — creates a 3-agent analyst team + supervisor (per §7.1).

Each sector team is a LangGraph subgraph with:
1. Filing Analyst — SEC filing analysis
2. Earnings Analyst — earnings transcript analysis
3. Quantitative Analyst — financial modeling + sentiment

The sector supervisor coordinates these agents and synthesizes findings.
"""

from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from app.agents.tools.sec_tools import fetch_10k_filing, fetch_10q_filing, search_filing_content, get_recent_filings
from app.agents.tools.transcript_tools import get_earnings_transcript, analyze_transcript_sentiment, compare_guidance
from app.agents.tools.fundamental_tools import get_financial_ratios, run_dcf_analysis, get_comparable_analysis
from app.agents.tools.market_tools import get_stock_price, get_price_history, get_sector_etf_performance
from app.agents.tools.sentiment_tools import get_social_sentiment, get_news_sentiment, get_insider_trading
from app.agents.tools.report_tools import save_analysis_report, get_reports_for_symbol, get_reports_by_agent, get_latest_sector_reports
from app.config import settings


# ---------------------------------------------------------------------------
# System prompt templates (per §7.2)
# ---------------------------------------------------------------------------

FILING_ANALYST_PROMPT = """You are a filing analyst specializing in the {sector} sector.

YOUR TASK: Analyze SEC 10-K and 10-Q filings for {symbols}.

FOR EACH FILING YOU ANALYZE:
1. Extract key financial metrics: revenue, operating income, net income, FCF, margins
2. Identify YoY trends in these metrics
3. Read Risk Factors (Item 1A) — flag any NEW risks not in prior filings
4. Read MD&A (Item 7) — summarize management's explanation of results
5. Check for: restatements, auditor changes, going concern language, unusual items
6. Note any significant changes in accounting policies

OUTPUT: Save a detailed report using save_analysis_report with:
- report_type: "filing_analysis"
- Specific numbers and direct quotes from filings
- Clear BUY/SELL/HOLD recommendation with confidence 1-10
- key_metrics dict with extracted numbers

{sector_specific_additions}"""

EARNINGS_ANALYST_PROMPT = """You are an earnings call analyst specializing in the {sector} sector.

YOUR TASK: Analyze earnings call transcripts for {symbols}.

FOR EACH TRANSCRIPT:
1. Summarize CEO's key messages (prepared remarks)
2. Summarize CFO's financial commentary
3. Analyze the Q&A section — what are analysts most concerned about?
4. Detect tone: confident vs hedging, specific vs vague guidance
5. Compare guidance to previous quarter — raised, lowered, maintained?
6. Identify management buzzwords and strategic themes
7. Flag any analyst questions that were deflected or poorly answered

OUTPUT: Save a detailed report using save_analysis_report with:
- report_type: "earnings_analysis"
- Specific quotes from transcript
- Guidance comparison vs prior quarter
- Tone assessment with examples

{sector_specific_additions}"""

QUANT_ANALYST_PROMPT = """You are a quantitative analyst specializing in the {sector} sector.

YOUR TASK: Build a quantitative picture for {symbols}.

FOR EACH STOCK:
1. Pull current financial ratios and compare to 5-year averages
2. Run DCF analysis with bull/base/bear scenarios
3. Compare valuation multiples against sector peers
4. Analyze price momentum (50-day vs 200-day MA, RSI equivalent)
5. Overlay social media and news sentiment
6. Check insider trading patterns (last 6 months)

OUTPUT: Save a detailed report using save_analysis_report with:
- report_type: "quant_analysis"
- DCF fair value and current price comparison
- Peer comparison table
- Sentiment summary
- Clear valuation call: undervalued/fairly valued/overvalued

{sector_specific_additions}"""

SECTOR_SUPERVISOR_PROMPT = """You are the supervisor for the {sector} sector analyst team.

YOUR TASK: After your team of analysts has completed their work, synthesize their findings.

PROCESS:
1. Review each analyst's report for your covered stocks ({symbols})
2. For each stock: aggregate the filing analysis + earnings analysis + quant analysis
3. Identify where analysts agree (high conviction) vs disagree (flag for discussion)
4. Rank all stocks in your sector: best opportunities to worst
5. Provide sector-level outlook (bullish/neutral/bearish) with reasoning

OUTPUT: Save a sector overview report using save_analysis_report with:
- report_type: "sector_overview"
- Ranked stock list with synthesized recommendation and confidence
- Sector outlook paragraph
- Key risks and catalysts for the sector
- Any analyst disagreements highlighted"""


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def _get_model() -> ChatAnthropic:
    """Get the configured LLM instance (per §2: claude-sonnet-4-20250514)."""
    return ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )


def create_sector_team(
    sector_name: str,
    tracked_symbols: list[str],
    sector_specific_additions: str = "",
) -> "CompiledStateGraph":
    """Factory that creates a 3-agent analyst team + supervisor for a market sector.

    Per §7.1: Creates Filing Analyst, Earnings Analyst, Quantitative Analyst,
    and a Sector Supervisor that coordinates them.

    Args:
        sector_name: e.g., "technology", "healthcare"
        tracked_symbols: e.g., ["AAPL", "MSFT", "NVDA", ...]
        sector_specific_additions: Extra prompt text for this sector's analysts

    Returns:
        Compiled LangGraph that can be used as a node in the parent graph.
    """
    model = _get_model()
    symbols_str = ", ".join(tracked_symbols)

    # 1. Filing Analyst
    filing_analyst = create_react_agent(
        model=model,
        tools=[fetch_10k_filing, fetch_10q_filing, search_filing_content, get_recent_filings, save_analysis_report],
        prompt=FILING_ANALYST_PROMPT.format(
            sector=sector_name,
            symbols=symbols_str,
            sector_specific_additions=sector_specific_additions,
        ),
        name=f"{sector_name}_filing_analyst",
    )

    # 2. Earnings Analyst
    earnings_analyst = create_react_agent(
        model=model,
        tools=[get_earnings_transcript, analyze_transcript_sentiment, compare_guidance, save_analysis_report],
        prompt=EARNINGS_ANALYST_PROMPT.format(
            sector=sector_name,
            symbols=symbols_str,
            sector_specific_additions=sector_specific_additions,
        ),
        name=f"{sector_name}_earnings_analyst",
    )

    # 3. Quantitative Analyst
    quant_analyst = create_react_agent(
        model=model,
        tools=[
            get_financial_ratios, run_dcf_analysis, get_comparable_analysis,
            get_stock_price, get_price_history, get_sector_etf_performance,
            get_social_sentiment, get_news_sentiment, get_insider_trading,
            save_analysis_report,
        ],
        prompt=QUANT_ANALYST_PROMPT.format(
            sector=sector_name,
            symbols=symbols_str,
            sector_specific_additions=sector_specific_additions,
        ),
        name=f"{sector_name}_quant_analyst",
    )

    # 4. Sector Supervisor — coordinates the 3 analysts
    supervisor = create_supervisor(
        agents=[filing_analyst, earnings_analyst, quant_analyst],
        model=model,
        prompt=SECTOR_SUPERVISOR_PROMPT.format(
            sector=sector_name,
            symbols=symbols_str,
        ),
        supervisor_name=f"{sector_name}_supervisor",
    )

    return supervisor.compile(name=f"{sector_name}_team")
