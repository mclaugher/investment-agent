"""Orchestrator — builds the complete multi-agent LangGraph hierarchy (per §8).

Three execution modes:
1. Full Analysis Cycle — all teams in parallel, then supervisors, then CEO
2. Targeted Analysis — single sector team → CIO → CEO
3. Portfolio Review — Risk Manager + CEO only (no new analysis)
"""

from typing import Any

from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, StateGraph
from langgraph_supervisor import create_supervisor

from app.agents.state import OrchestratorState
from app.agents.ceo_agent import build_ceo_agent
from app.agents.supervisors.cio_agent import build_cio_agent
from app.agents.supervisors.risk_manager import build_risk_manager
from app.agents.supervisors.sector_supervisor import build_sector_supervisor_a, build_sector_supervisor_b
from app.agents.supervisors.fixed_income_supervisor import build_fixed_income_team
from app.agents.supervisors.macro_supervisor import build_macro_team
from app.config import settings


# ---------------------------------------------------------------------------
# §8.1 — Full graph construction
# ---------------------------------------------------------------------------

def build_fund_graph() -> Any:
    """Build the complete Superhuman Alpha Fund agent hierarchy as a LangGraph.

    Per §8.1:
        1. All sector teams run in PARALLEL (they are independent)
        2. Fixed income team runs in PARALLEL with sector teams
        3. Macro team runs in PARALLEL with sector + FI teams
        4. After all teams complete → CIO aggregates + Risk Manager assesses (parallel)
        5. After CIO + Risk complete → CEO makes final decisions

    Returns:
        Compiled LangGraph ready for invocation.
    """
    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )

    # Build all teams
    sector_group_a = build_sector_supervisor_a()
    sector_group_b = build_sector_supervisor_b()
    fi_team = build_fixed_income_team()
    macro_team = build_macro_team()
    cio_agent = build_cio_agent()
    risk_manager = build_risk_manager()
    ceo_agent = build_ceo_agent()

    # Top-level supervisor coordinates the full hierarchy.
    # The langgraph-supervisor library handles routing between agents.
    # We build a two-level coordination:
    #   Level 1: Analysis teams (parallel) — sector groups, FI, macro
    #   Level 2: Strategy (parallel) — CIO + Risk Manager
    #   Level 3: Decision — CEO

    # Strategy layer supervisor: CIO + Risk Manager run in parallel, then CEO decides
    strategy_supervisor = create_supervisor(
        agents=[cio_agent, risk_manager, ceo_agent],
        model=model,
        prompt="""You are the executive coordinator for Superhuman Alpha Fund.

Your job is to orchestrate the strategy and decision phase:
1. First, have BOTH the cio_agent and risk_manager analyze the current reports and portfolio.
2. After both have completed, have the ceo_agent make final decisions based on their inputs.

IMPORTANT: The CIO and Risk Manager should run BEFORE the CEO.
Always delegate to cio_agent first, then risk_manager, then ceo_agent last.""",
        supervisor_name="strategy_coordinator",
    ).compile(name="strategy_layer")

    # Analysis layer supervisor: all analysis teams + macro
    analysis_supervisor = create_supervisor(
        agents=[sector_group_a, sector_group_b, fi_team, macro_team],
        model=model,
        prompt="""You are the analysis coordinator for Superhuman Alpha Fund.

Your job is to trigger all analysis teams. Delegate to ALL teams:
1. sector_group_a — technology, healthcare, financials analysis
2. sector_group_b — energy, consumer, industrials, real_estate, utilities analysis
3. fixed_income_team — bond, credit, rate analysis
4. macro_team — macro and geopolitical analysis

Trigger ALL teams. They are independent and should all run.""",
        supervisor_name="analysis_coordinator",
    ).compile(name="analysis_layer")

    # Top-level orchestrator: analysis first, then strategy
    orchestrator = create_supervisor(
        agents=[analysis_supervisor, strategy_supervisor],
        model=model,
        prompt="""You are the top-level orchestrator for Superhuman Alpha Fund.

EXECUTION ORDER (strict):
1. FIRST: Delegate to analysis_layer to run all analysis teams
2. AFTER analysis completes: Delegate to strategy_layer for CIO + Risk + CEO decisions

Always run analysis_layer FIRST, then strategy_layer SECOND.""",
        supervisor_name="orchestrator",
    )

    return orchestrator.compile(name="superhuman_alpha_fund")


# ---------------------------------------------------------------------------
# §8.2 — Targeted analysis (single sector)
# ---------------------------------------------------------------------------

def build_targeted_graph(sector_name: str) -> Any:
    """Build a targeted analysis graph for a single sector.

    Runs one sector team, then CIO → CEO for an updated decision.
    Used when a new filing is detected or human requests fresh analysis.

    Args:
        sector_name: The sector to analyze (e.g., "technology")

    Returns:
        Compiled LangGraph for targeted analysis.
    """
    from app.agents.analysts.base_analyst import create_sector_team
    from scripts.seed_universe import STOCK_UNIVERSE

    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )

    # Sector-specific additions mapping
    sector_additions = _get_sector_additions(sector_name)
    symbols = STOCK_UNIVERSE.get(sector_name, [])

    sector_team = create_sector_team(
        sector_name=sector_name,
        tracked_symbols=symbols,
        sector_specific_additions=sector_additions,
    )

    cio_agent = build_cio_agent()
    ceo_agent = build_ceo_agent()

    targeted = create_supervisor(
        agents=[sector_team, cio_agent, ceo_agent],
        model=model,
        prompt=f"""You are running a targeted analysis for the {sector_name} sector.

EXECUTION ORDER (strict):
1. FIRST: Delegate to {sector_name}_team to analyze {', '.join(symbols)}
2. THEN: Delegate to cio_agent to review the new sector report and propose actions
3. FINALLY: Delegate to ceo_agent to make final decisions

Always follow this exact order.""",
        supervisor_name="targeted_orchestrator",
    )

    return targeted.compile(name=f"targeted_{sector_name}")


# ---------------------------------------------------------------------------
# §8.2 — Portfolio review (no new analysis)
# ---------------------------------------------------------------------------

def build_review_graph() -> Any:
    """Build a portfolio review graph.

    Skips sector analysis, just runs Risk Manager + CEO with existing reports
    to re-evaluate current positions against updated risk profile.

    Returns:
        Compiled LangGraph for portfolio review.
    """
    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )

    risk_manager = build_risk_manager()
    ceo_agent = build_ceo_agent()

    review = create_supervisor(
        agents=[risk_manager, ceo_agent],
        model=model,
        prompt="""You are running a portfolio review for Superhuman Alpha Fund.

EXECUTION ORDER (strict):
1. FIRST: Delegate to risk_manager to assess current portfolio risks
2. THEN: Delegate to ceo_agent to review risk assessment and make any needed adjustments

No new sector analysis is needed — use existing reports only.""",
        supervisor_name="review_orchestrator",
    )

    return review.compile(name="portfolio_review")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_sector_additions(sector_name: str) -> str:
    """Get sector-specific prompt additions by importing from sector files."""
    additions_map = {
        "technology": "app.agents.analysts.tech_analyst",
        "healthcare": "app.agents.analysts.healthcare_analyst",
        "financials": "app.agents.analysts.financials_analyst",
        "energy": "app.agents.analysts.energy_analyst",
        "consumer": "app.agents.analysts.consumer_analyst",
        "industrials": "app.agents.analysts.industrials_analyst",
        "real_estate": "app.agents.analysts.realestate_analyst",
        "utilities": "app.agents.analysts.utilities_analyst",
    }

    module_path = additions_map.get(sector_name)
    if not module_path:
        return ""

    import importlib
    module = importlib.import_module(module_path)

    # Each module has a constant like TECH_ADDITIONS, HEALTHCARE_ADDITIONS, etc.
    for attr_name in dir(module):
        if attr_name.endswith("_ADDITIONS"):
            return getattr(module, attr_name, "")

    return ""
