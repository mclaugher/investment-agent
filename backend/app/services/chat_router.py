"""Chat router service — intent classification and routing (per §11.1).

Uses a dedicated LLM call (not a full agent) to classify user intent before routing.
"""

import logging
from typing import Any

from langchain_anthropic import ChatAnthropic

from app.config import settings

logger = logging.getLogger(__name__)

# Intent types per §11.1
INTENTS = {
    "DECISION_QUERY": "Questions about past decisions (why buy/sell, explain decision)",
    "SETTINGS_CHANGE": "Change risk profile, allocation targets, position limits",
    "ANALYSIS_QUERY": "Questions about specific stocks or sectors",
    "PORTFOLIO_QUERY": "Questions about portfolio performance, holdings, cash",
    "TRIGGER_ANALYSIS": "Requests to run analysis on specific stock or sector",
    "GENERAL": "Market overview, greetings, general conversation",
}

CLASSIFY_PROMPT = """You are an intent classifier for an investment management system.

Classify the user message into ONE of these intents:
- DECISION_QUERY: Questions about past investment decisions ("Why did we buy AAPL?", "Explain the sell decision")
- SETTINGS_CHANGE: Requests to change risk settings ("Be more aggressive", "Set max position to 3%", "More bonds")
- ANALYSIS_QUERY: Questions about specific stocks or sectors ("What about TSLA?", "How's tech looking?")
- PORTFOLIO_QUERY: Questions about portfolio performance ("How are we doing?", "Biggest winner?", "Cash position?")
- TRIGGER_ANALYSIS: Explicit requests to run analysis ("Run analysis on NVDA", "Re-evaluate healthcare")
- GENERAL: Market overview, greetings, or anything that doesn't fit above

Respond with ONLY the intent label, nothing else.

User message: {message}"""

# Aggressiveness change mapping per §11.2
AGGRESSIVENESS_MAPPING = [
    (["much more aggressive", "maximum growth", "all in"], 3, 15, -15),
    (["more aggressive", "take more risk", "riskier"], 2, 10, -10),
    (["slightly more aggressive", "bit more risk"], 1, 5, -5),
    (["slightly more conservative", "bit less risk"], -1, -5, 5),
    (["more conservative", "reduce risk", "less risky"], -2, -10, 10),
    (["much more conservative", "safety first", "very conservative"], -3, -15, 15),
]


async def classify_intent(message: str) -> str:
    """Classify user message intent using LLM (per §11.1)."""
    try:
        model = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=settings.anthropic_api_key,
            max_tokens=20,
        )
        response = await model.ainvoke(CLASSIFY_PROMPT.format(message=message))
        intent = response.content.strip().upper()

        # Validate intent
        if intent in INTENTS:
            return intent
        return "GENERAL"

    except Exception as e:
        logger.warning(f"Intent classification failed: {e}")
        return "GENERAL"


async def route_query(message: str, intent: str) -> dict[str, Any]:
    """Route a classified query to the appropriate handler (per §11.1)."""
    handlers = {
        "DECISION_QUERY": _handle_decision_query,
        "SETTINGS_CHANGE": _handle_settings_change,
        "ANALYSIS_QUERY": _handle_analysis_query,
        "PORTFOLIO_QUERY": _handle_portfolio_query,
        "TRIGGER_ANALYSIS": _handle_trigger_analysis,
        "GENERAL": _handle_general,
    }

    handler = handlers.get(intent, _handle_general)
    return await handler(message)


async def _handle_decision_query(message: str) -> dict[str, Any]:
    """Fetch decision trail and format as readable response."""
    from app.database import async_session
    from app.models.reports import AgentDecision
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(
            select(AgentDecision).order_by(AgentDecision.created_at.desc()).limit(5)
        )
        decisions = result.scalars().all()

    if not decisions:
        return {"agent": "system", "response": "No investment decisions have been made yet."}

    lines = ["Here are the recent investment decisions:\n"]
    for d in decisions:
        lines.append(
            f"- **{d.action or 'HOLD'} {d.symbol}** (Confidence: {d.confidence}/10) "
            f"— Status: {d.status}\n  {d.reasoning[:200] if d.reasoning else 'No reasoning recorded'}..."
        )

    return {
        "agent": "system",
        "response": "\n".join(lines),
        "report_ids": [d.id for d in decisions],
    }


async def _handle_settings_change(message: str) -> dict[str, Any]:
    """Parse natural language settings change (per §11.2)."""
    msg_lower = message.lower()

    # Try to match aggressiveness patterns
    for phrases, aggr_delta, equity_delta, fi_delta in AGGRESSIVENESS_MAPPING:
        if any(phrase in msg_lower for phrase in phrases):
            return {
                "agent": "system",
                "response": (
                    f"I'll update your risk profile:\n"
                    f"- Aggressiveness: {'+' if aggr_delta > 0 else ''}{aggr_delta}\n"
                    f"- Target equity: {'+' if equity_delta > 0 else ''}{equity_delta}%\n"
                    f"- Target fixed income: {'+' if fi_delta > 0 else ''}{fi_delta}%\n"
                    f"\nShall I apply these changes?"
                ),
                "data": {
                    "pending_change": {
                        "aggressiveness_delta": aggr_delta,
                        "equity_delta": equity_delta,
                        "fi_delta": fi_delta,
                    }
                },
            }

    return {
        "agent": "system",
        "response": "I can adjust your risk profile. Try saying things like 'be more aggressive', "
                     "'reduce risk', or 'set max position to 3%'.",
    }


async def _handle_analysis_query(message: str) -> dict[str, Any]:
    """Find latest reports for a queried stock or sector."""
    from app.database import async_session
    from app.models.reports import AnalysisReport
    from sqlalchemy import select

    # Try to extract a symbol from the message
    msg_upper = message.upper()
    from scripts.seed_universe import STOCK_UNIVERSE

    found_symbol = None
    found_sector = None

    for sector, symbols in STOCK_UNIVERSE.items():
        if sector in message.lower():
            found_sector = sector
            break
        for sym in symbols:
            if sym in msg_upper:
                found_symbol = sym
                found_sector = sector
                break

    if not found_symbol and not found_sector:
        return {"agent": "system", "response": "Which stock or sector would you like to know about?"}

    async with async_session() as session:
        query = select(AnalysisReport).order_by(AnalysisReport.created_at.desc()).limit(5)
        if found_symbol:
            query = query.where(AnalysisReport.symbol == found_symbol)
        elif found_sector:
            query = query.where(AnalysisReport.sector == found_sector)

        result = await session.execute(query)
        reports = result.scalars().all()

    if not reports:
        target = found_symbol or found_sector
        return {"agent": "system", "response": f"No analysis reports found for {target} yet."}

    lines = [f"Latest analysis for **{found_symbol or found_sector}**:\n"]
    for r in reports:
        lines.append(
            f"- [{r.agent_name}] **{r.title}** — {r.recommendation or 'N/A'} "
            f"(Confidence: {r.confidence or 'N/A'}/10)"
        )

    return {
        "agent": "system",
        "response": "\n".join(lines),
        "report_ids": [r.id for r in reports],
    }


async def _handle_portfolio_query(message: str) -> dict[str, Any]:
    """Query portfolio data and format response."""
    from app.database import async_session
    from app.models.portfolio import CashBalance, Holding
    from sqlalchemy import select

    async with async_session() as session:
        holdings_result = await session.execute(select(Holding))
        holdings = holdings_result.scalars().all()

        cash_result = await session.execute(
            select(CashBalance).order_by(CashBalance.id.desc()).limit(1)
        )
        cash = cash_result.scalar_one_or_none()

    cash_balance = float(cash.balance) if cash else 0.0
    total_value = sum(float(h.shares) * float(h.current_price) for h in holdings) + cash_balance

    # Find best and worst performers
    performers = []
    for h in holdings:
        cost = float(h.shares) * float(h.avg_cost_basis)
        current = float(h.shares) * float(h.current_price)
        pnl_pct = ((current - cost) / cost * 100) if cost > 0 else 0
        performers.append((h.symbol, pnl_pct, current - cost))

    performers.sort(key=lambda x: x[1], reverse=True)

    lines = [
        f"**Portfolio Summary:**",
        f"- Total value: ${total_value:,.2f}",
        f"- Cash: ${cash_balance:,.2f}",
        f"- Holdings: {len(holdings)} positions",
    ]

    if performers:
        best = performers[0]
        worst = performers[-1]
        lines.append(f"- Best performer: **{best[0]}** ({best[1]:+.1f}%)")
        lines.append(f"- Worst performer: **{worst[0]}** ({worst[1]:+.1f}%)")

    return {"agent": "system", "response": "\n".join(lines)}


async def _handle_trigger_analysis(message: str) -> dict[str, Any]:
    """Trigger targeted or sector analysis."""
    from scripts.seed_universe import STOCK_UNIVERSE
    from app.tasks.analysis_cycle import run_targeted_analysis, run_full_analysis

    msg_upper = message.upper()

    # Check for specific symbol
    for sector, symbols in STOCK_UNIVERSE.items():
        for sym in symbols:
            if sym in msg_upper:
                task = run_targeted_analysis.delay(sym)
                return {
                    "agent": "system",
                    "response": f"Triggered analysis for **{sym}** ({sector} sector). Task ID: {task.id}",
                }

    # Check for sector
    for sector in STOCK_UNIVERSE:
        if sector in message.lower():
            task = run_targeted_analysis.delay(STOCK_UNIVERSE[sector][0])
            return {
                "agent": "system",
                "response": f"Triggered analysis for **{sector}** sector. Task ID: {task.id}",
            }

    # Full analysis
    if "full" in message.lower() or "all" in message.lower():
        task = run_full_analysis.delay()
        return {"agent": "system", "response": f"Triggered full analysis cycle. Task ID: {task.id}"}

    return {"agent": "system", "response": "Which stock or sector should I analyze?"}


async def _handle_general(message: str) -> dict[str, Any]:
    """Handle general queries with LLM."""
    try:
        model = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=settings.anthropic_api_key,
            max_tokens=500,
        )
        response = await model.ainvoke(
            f"You are an investment fund assistant. Respond briefly to: {message}"
        )
        return {"agent": "system", "response": response.content}

    except Exception as e:
        return {"agent": "system", "response": "I'm here to help with your investment portfolio. What would you like to know?"}
