"""TypedDict state schemas for all agent levels (per §7, §5.2).

LangGraph requires typed state schemas. Each level of the hierarchy
has its own state that flows through the graph.
"""

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Base state shared by all agents in the hierarchy.

    Uses LangGraph's message annotation for automatic message merging.
    """

    messages: Annotated[list[AnyMessage], add_messages]


class SectorTeamState(AgentState):
    """State for a sector analyst team (filing + earnings + quant + supervisor).

    Carries sector context and the symbols being analyzed.
    """

    sector: str
    symbols: list[str]
    report_ids: list[int]


class FixedIncomeState(AgentState):
    """State for the fixed income team (bond + credit + rate + supervisor)."""

    bond_etfs: list[str]
    report_ids: list[int]


class MacroState(AgentState):
    """State for the macro team (macro analyst + geopolitical + supervisor)."""

    report_ids: list[int]


class SupervisorState(AgentState):
    """State for mid-level supervisors (CIO, sector supervisors).

    Collects report IDs from child agents for aggregation.
    """

    sector_report_ids: list[int]
    fixed_income_report_ids: list[int]
    macro_report_ids: list[int]


class ExecutiveState(AgentState):
    """State for the CEO agent — top of the hierarchy.

    Receives aggregated inputs from CIO, Risk Manager, and Macro Supervisor.
    Produces final trade decisions.
    """

    cio_report_ids: list[int]
    risk_report_ids: list[int]
    macro_report_ids: list[int]
    decisions: list[dict[str, Any]]


class OrchestratorState(AgentState):
    """Top-level state for the full orchestrator graph.

    Holds the stock universe configuration and collects all outputs.
    """

    stock_universe: dict[str, list[str]]
    sector_report_ids: dict[str, list[int]]
    fixed_income_report_ids: list[int]
    macro_report_ids: list[int]
    cio_report_ids: list[int]
    risk_report_ids: list[int]
    decisions: list[dict[str, Any]]
