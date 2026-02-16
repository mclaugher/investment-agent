"""Tests for sector team factory and agent construction (per §16.3).

These tests verify that agents are built correctly with proper tools and prompts.
They do NOT call the LLM — they test the construction/wiring layer only.
"""

from unittest.mock import patch, MagicMock

import pytest


class TestCreateSectorTeam:
    """Test the create_sector_team factory function."""

    @patch("app.agents.analysts.base_analyst.ChatAnthropic")
    @patch("app.agents.analysts.base_analyst.create_supervisor")
    @patch("app.agents.analysts.base_analyst.create_react_agent")
    def test_creates_three_agents_and_supervisor(self, mock_react, mock_supervisor, mock_llm):
        """Factory should create filing, earnings, and quant agents + supervisor."""
        from app.agents.analysts.base_analyst import create_sector_team

        mock_compiled = MagicMock()
        mock_supervisor.return_value.compile.return_value = mock_compiled

        result = create_sector_team(
            sector_name="technology",
            tracked_symbols=["AAPL", "MSFT", "NVDA"],
        )

        # 3 react agents created
        assert mock_react.call_count == 3

        # Supervisor created with 3 agents
        mock_supervisor.assert_called_once()
        call_kwargs = mock_supervisor.call_args
        assert len(call_kwargs.kwargs["agents"]) == 3
        assert call_kwargs.kwargs["supervisor_name"] == "technology_supervisor"

        # Result is the compiled graph
        assert result == mock_compiled

    @patch("app.agents.analysts.base_analyst.ChatAnthropic")
    @patch("app.agents.analysts.base_analyst.create_supervisor")
    @patch("app.agents.analysts.base_analyst.create_react_agent")
    def test_agent_names_include_sector(self, mock_react, mock_supervisor, mock_llm):
        """Each agent name should include the sector name."""
        from app.agents.analysts.base_analyst import create_sector_team

        mock_supervisor.return_value.compile.return_value = MagicMock()

        create_sector_team(
            sector_name="healthcare",
            tracked_symbols=["UNH", "JNJ"],
        )

        agent_names = [call.kwargs["name"] for call in mock_react.call_args_list]
        assert "healthcare_filing_analyst" in agent_names
        assert "healthcare_earnings_analyst" in agent_names
        assert "healthcare_quant_analyst" in agent_names

    @patch("app.agents.analysts.base_analyst.ChatAnthropic")
    @patch("app.agents.analysts.base_analyst.create_supervisor")
    @patch("app.agents.analysts.base_analyst.create_react_agent")
    def test_prompts_include_symbols(self, mock_react, mock_supervisor, mock_llm):
        """Agent prompts should include the tracked symbols."""
        from app.agents.analysts.base_analyst import create_sector_team

        mock_supervisor.return_value.compile.return_value = MagicMock()

        create_sector_team(
            sector_name="energy",
            tracked_symbols=["XOM", "CVX"],
        )

        for call in mock_react.call_args_list:
            prompt = call.kwargs["prompt"]
            assert "XOM" in prompt
            assert "CVX" in prompt

    @patch("app.agents.analysts.base_analyst.ChatAnthropic")
    @patch("app.agents.analysts.base_analyst.create_supervisor")
    @patch("app.agents.analysts.base_analyst.create_react_agent")
    def test_sector_specific_additions_injected(self, mock_react, mock_supervisor, mock_llm):
        """Sector-specific additions should appear in agent prompts."""
        from app.agents.analysts.base_analyst import create_sector_team

        mock_supervisor.return_value.compile.return_value = MagicMock()

        create_sector_team(
            sector_name="technology",
            tracked_symbols=["AAPL"],
            sector_specific_additions="Focus on cloud revenue metrics.",
        )

        for call in mock_react.call_args_list:
            prompt = call.kwargs["prompt"]
            assert "cloud revenue metrics" in prompt

    @patch("app.agents.analysts.base_analyst.ChatAnthropic")
    @patch("app.agents.analysts.base_analyst.create_supervisor")
    @patch("app.agents.analysts.base_analyst.create_react_agent")
    def test_filing_analyst_has_sec_tools(self, mock_react, mock_supervisor, mock_llm):
        """Filing analyst should have SEC tools + save_analysis_report."""
        from app.agents.analysts.base_analyst import create_sector_team

        mock_supervisor.return_value.compile.return_value = MagicMock()

        create_sector_team(
            sector_name="technology",
            tracked_symbols=["AAPL"],
        )

        # First call is filing analyst
        filing_tools = mock_react.call_args_list[0].kwargs["tools"]
        tool_names = [t.name for t in filing_tools]
        assert "fetch_10k_filing" in tool_names
        assert "fetch_10q_filing" in tool_names
        assert "save_analysis_report" in tool_names

    @patch("app.agents.analysts.base_analyst.ChatAnthropic")
    @patch("app.agents.analysts.base_analyst.create_supervisor")
    @patch("app.agents.analysts.base_analyst.create_react_agent")
    def test_quant_analyst_has_market_and_sentiment_tools(self, mock_react, mock_supervisor, mock_llm):
        """Quant analyst should have market, fundamental, and sentiment tools."""
        from app.agents.analysts.base_analyst import create_sector_team

        mock_supervisor.return_value.compile.return_value = MagicMock()

        create_sector_team(
            sector_name="technology",
            tracked_symbols=["AAPL"],
        )

        # Third call is quant analyst
        quant_tools = mock_react.call_args_list[2].kwargs["tools"]
        tool_names = [t.name for t in quant_tools]
        assert "get_financial_ratios" in tool_names
        assert "run_dcf_analysis" in tool_names
        assert "get_social_sentiment" in tool_names
        assert "get_stock_price" in tool_names


class TestSectorTeamBuilders:
    """Test that each sector file's builder function works."""

    @patch("app.agents.analysts.base_analyst.ChatAnthropic")
    @patch("app.agents.analysts.base_analyst.create_supervisor")
    @patch("app.agents.analysts.base_analyst.create_react_agent")
    def test_tech_team_builder(self, mock_react, mock_supervisor, mock_llm):
        from app.agents.analysts.tech_analyst import build_tech_team
        mock_supervisor.return_value.compile.return_value = MagicMock()
        build_tech_team()
        # Verify prompts contain tech-specific content
        for call in mock_react.call_args_list:
            prompt = call.kwargs["prompt"]
            assert "technology" in prompt.lower()

    @patch("app.agents.analysts.base_analyst.ChatAnthropic")
    @patch("app.agents.analysts.base_analyst.create_supervisor")
    @patch("app.agents.analysts.base_analyst.create_react_agent")
    def test_healthcare_team_builder(self, mock_react, mock_supervisor, mock_llm):
        from app.agents.analysts.healthcare_analyst import build_healthcare_team
        mock_supervisor.return_value.compile.return_value = MagicMock()
        build_healthcare_team()
        for call in mock_react.call_args_list:
            prompt = call.kwargs["prompt"]
            assert "healthcare" in prompt.lower()

    @patch("app.agents.analysts.base_analyst.ChatAnthropic")
    @patch("app.agents.analysts.base_analyst.create_supervisor")
    @patch("app.agents.analysts.base_analyst.create_react_agent")
    def test_all_eight_sectors_buildable(self, mock_react, mock_supervisor, mock_llm):
        """All 8 sector builders should execute without error."""
        mock_supervisor.return_value.compile.return_value = MagicMock()

        from app.agents.analysts.tech_analyst import build_tech_team
        from app.agents.analysts.healthcare_analyst import build_healthcare_team
        from app.agents.analysts.financials_analyst import build_financials_team
        from app.agents.analysts.energy_analyst import build_energy_team
        from app.agents.analysts.consumer_analyst import build_consumer_team
        from app.agents.analysts.industrials_analyst import build_industrials_team
        from app.agents.analysts.realestate_analyst import build_realestate_team
        from app.agents.analysts.utilities_analyst import build_utilities_team

        builders = [
            build_tech_team, build_healthcare_team, build_financials_team,
            build_energy_team, build_consumer_team, build_industrials_team,
            build_realestate_team, build_utilities_team,
        ]

        for builder in builders:
            mock_react.reset_mock()
            mock_supervisor.reset_mock()
            builder()
            # Each should create 3 agents + 1 supervisor
            assert mock_react.call_count == 3
            assert mock_supervisor.call_count == 1


class TestFixedIncomeTeam:
    """Test fixed income team construction."""

    @patch("app.agents.fixed_income.bond_analyst.ChatAnthropic")
    @patch("app.agents.fixed_income.credit_analyst.ChatAnthropic")
    @patch("app.agents.fixed_income.rate_analyst.ChatAnthropic")
    @patch("app.agents.supervisors.fixed_income_supervisor.ChatAnthropic")
    @patch("app.agents.supervisors.fixed_income_supervisor.create_supervisor")
    @patch("app.agents.fixed_income.bond_analyst.create_react_agent")
    @patch("app.agents.fixed_income.credit_analyst.create_react_agent")
    @patch("app.agents.fixed_income.rate_analyst.create_react_agent")
    def test_fi_team_has_three_analysts(
        self, mock_rate_react, mock_credit_react, mock_bond_react,
        mock_fi_supervisor, mock_fi_llm, mock_rate_llm, mock_credit_llm, mock_bond_llm,
    ):
        from app.agents.supervisors.fixed_income_supervisor import build_fixed_income_team

        mock_fi_supervisor.return_value.compile.return_value = MagicMock()

        build_fixed_income_team()

        # Each analyst react agent created once
        assert mock_bond_react.call_count == 1
        assert mock_credit_react.call_count == 1
        assert mock_rate_react.call_count == 1

        # Supervisor receives 3 agents
        mock_fi_supervisor.assert_called_once()
        assert len(mock_fi_supervisor.call_args.kwargs["agents"]) == 3

    def test_bond_analyst_prompt_covers_etfs(self):
        from app.agents.fixed_income.bond_analyst import BOND_ANALYST_PROMPT, BOND_ETFS
        for etf in BOND_ETFS:
            assert etf in BOND_ANALYST_PROMPT


class TestMacroTeam:
    """Test macro team construction."""

    @patch("app.agents.macro.macro_analyst.ChatAnthropic")
    @patch("app.agents.macro.geopolitical_analyst.ChatAnthropic")
    @patch("app.agents.supervisors.macro_supervisor.ChatAnthropic")
    @patch("app.agents.supervisors.macro_supervisor.create_supervisor")
    @patch("app.agents.macro.macro_analyst.create_react_agent")
    @patch("app.agents.macro.geopolitical_analyst.create_react_agent")
    def test_macro_team_has_two_analysts(
        self, mock_geo_react, mock_macro_react,
        mock_macro_supervisor, mock_macro_sup_llm, mock_geo_llm, mock_macro_llm,
    ):
        from app.agents.supervisors.macro_supervisor import build_macro_team

        mock_macro_supervisor.return_value.compile.return_value = MagicMock()

        build_macro_team()

        assert mock_macro_react.call_count == 1
        assert mock_geo_react.call_count == 1

        mock_macro_supervisor.assert_called_once()
        assert len(mock_macro_supervisor.call_args.kwargs["agents"]) == 2


class TestExecutiveAgents:
    """Test CIO, Risk Manager, CEO agent construction."""

    @patch("app.agents.supervisors.cio_agent.ChatAnthropic")
    @patch("app.agents.supervisors.cio_agent.create_react_agent")
    def test_cio_has_report_and_portfolio_tools(self, mock_react, mock_llm):
        from app.agents.supervisors.cio_agent import build_cio_agent
        build_cio_agent()
        tools = mock_react.call_args.kwargs["tools"]
        tool_names = [t.name for t in tools]
        assert "save_analysis_report" in tool_names
        assert "get_current_holdings" in tool_names
        assert "get_risk_profile" in tool_names

    @patch("app.agents.supervisors.risk_manager.ChatAnthropic")
    @patch("app.agents.supervisors.risk_manager.create_react_agent")
    def test_risk_manager_has_market_and_portfolio_tools(self, mock_react, mock_llm):
        from app.agents.supervisors.risk_manager import build_risk_manager
        build_risk_manager()
        tools = mock_react.call_args.kwargs["tools"]
        tool_names = [t.name for t in tools]
        assert "get_stock_price" in tool_names
        assert "get_current_holdings" in tool_names
        assert "get_risk_profile" in tool_names
        assert "save_analysis_report" in tool_names

    @patch("app.agents.ceo_agent.ChatAnthropic")
    @patch("app.agents.ceo_agent.create_react_agent")
    def test_ceo_has_trade_execution_tools(self, mock_react, mock_llm):
        from app.agents.ceo_agent import build_ceo_agent
        build_ceo_agent()
        tools = mock_react.call_args.kwargs["tools"]
        tool_names = [t.name for t in tools]
        assert "validate_trade" in tool_names
        assert "execute_trade" in tool_names
        assert "save_analysis_report" in tool_names

    @patch("app.agents.ceo_agent.ChatAnthropic")
    @patch("app.agents.ceo_agent.create_react_agent")
    def test_ceo_prompt_has_hard_constraints(self, mock_react, mock_llm):
        from app.agents.ceo_agent import CEO_PROMPT
        assert "NO MARGIN" in CEO_PROMPT
        assert "NO SHORT SELLING" in CEO_PROMPT
        assert "NO LEVERAGE" in CEO_PROMPT


class TestOrchestratorConstruction:
    """Test orchestrator graph construction."""

    @patch("app.agents.orchestrator.build_ceo_agent")
    @patch("app.agents.orchestrator.build_risk_manager")
    @patch("app.agents.orchestrator.build_cio_agent")
    @patch("app.agents.orchestrator.build_macro_team")
    @patch("app.agents.orchestrator.build_fixed_income_team")
    @patch("app.agents.orchestrator.build_sector_supervisor_b")
    @patch("app.agents.orchestrator.build_sector_supervisor_a")
    @patch("app.agents.orchestrator.ChatAnthropic")
    @patch("app.agents.orchestrator.create_supervisor")
    def test_build_fund_graph(
        self, mock_supervisor, mock_llm,
        mock_sup_a, mock_sup_b, mock_fi, mock_macro,
        mock_cio, mock_risk, mock_ceo,
    ):
        from app.agents.orchestrator import build_fund_graph

        mock_compiled = MagicMock()
        mock_supervisor.return_value.compile.return_value = mock_compiled

        result = build_fund_graph()

        # Should create 3 supervisor levels: analysis, strategy, orchestrator
        assert mock_supervisor.call_count == 3

        # All team builders should be called
        mock_sup_a.assert_called_once()
        mock_sup_b.assert_called_once()
        mock_fi.assert_called_once()
        mock_macro.assert_called_once()
        mock_cio.assert_called_once()
        mock_risk.assert_called_once()
        mock_ceo.assert_called_once()

    @patch("app.agents.orchestrator.build_ceo_agent")
    @patch("app.agents.orchestrator.build_risk_manager")
    @patch("app.agents.orchestrator.ChatAnthropic")
    @patch("app.agents.orchestrator.create_supervisor")
    def test_build_review_graph(self, mock_supervisor, mock_llm, mock_risk, mock_ceo):
        from app.agents.orchestrator import build_review_graph

        mock_supervisor.return_value.compile.return_value = MagicMock()

        build_review_graph()

        # Only 1 supervisor (risk + ceo)
        mock_supervisor.assert_called_once()
        assert len(mock_supervisor.call_args.kwargs["agents"]) == 2
        mock_risk.assert_called_once()
        mock_ceo.assert_called_once()


class TestStateSchemas:
    """Test that state schemas are properly defined."""

    def test_agent_state_has_messages(self):
        from app.agents.state import AgentState
        assert "messages" in AgentState.__annotations__

    def test_sector_team_state_has_required_fields(self):
        from app.agents.state import SectorTeamState
        # TypedDict doesn't support issubclass; check fields directly
        all_annotations = SectorTeamState.__annotations__
        assert "messages" in all_annotations  # inherited from AgentState
        assert "sector" in all_annotations
        assert "symbols" in all_annotations

    def test_orchestrator_state_has_all_fields(self):
        from app.agents.state import OrchestratorState
        required = ["stock_universe", "sector_report_ids", "fixed_income_report_ids",
                     "macro_report_ids", "cio_report_ids", "risk_report_ids", "decisions"]
        for field in required:
            assert field in OrchestratorState.__annotations__

    def test_executive_state_has_decision_fields(self):
        from app.agents.state import ExecutiveState
        assert "decisions" in ExecutiveState.__annotations__
        assert "cio_report_ids" in ExecutiveState.__annotations__
        assert "risk_report_ids" in ExecutiveState.__annotations__
