"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-15

Creates all tables per specifications.md §4 Database Schema.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension for GIN trigram index on analysis_reports.content
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # --- agent_decisions (created first — referenced by transactions FK) ---
    op.create_table(
        "agent_decisions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("decision_type", sa.String(20), nullable=False),
        sa.Column("symbol", sa.String(10), nullable=True),
        sa.Column("action", sa.String(4), nullable=True),
        sa.Column("recommended_shares", sa.Numeric(18, 8), nullable=True),
        sa.Column("recommended_amount", sa.Numeric(18, 4), nullable=True),
        sa.Column("reasoning", sa.Text, nullable=False),
        sa.Column("confidence", sa.Integer, nullable=False),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("supporting_report_ids", postgresql.JSONB, nullable=False),
        sa.Column("dissenting_opinions", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="proposed"),
        sa.Column("human_override", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("human_notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("action IS NULL OR action IN ('BUY', 'SELL')", name="ck_decision_action"),
        sa.CheckConstraint("confidence >= 1 AND confidence <= 10", name="ck_decision_confidence"),
    )

    # --- analysis_reports ---
    op.create_table(
        "analysis_reports",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("agent_role", sa.String(50), nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("symbol", sa.String(10), nullable=True),
        sa.Column("sector", sa.String(50), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("recommendation", sa.String(20), nullable=True),
        sa.Column("confidence", sa.Integer, nullable=True),
        sa.Column("key_metrics", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("parent_report_id", sa.Integer, sa.ForeignKey("analysis_reports.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidence IS NULL OR (confidence >= 1 AND confidence <= 10)", name="ck_report_confidence"),
    )
    op.create_index("ix_analysis_reports_agent_name", "analysis_reports", ["agent_name"])
    op.create_index("ix_analysis_reports_symbol", "analysis_reports", ["symbol"])
    op.create_index("ix_analysis_reports_sector", "analysis_reports", ["sector"])
    op.create_index(
        "ix_analysis_reports_content_gin",
        "analysis_reports",
        ["content"],
        postgresql_using="gin",
        postgresql_ops={"content": "gin_trgm_ops"},
    )

    # --- holdings ---
    op.create_table(
        "holdings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(10), nullable=False),
        sa.Column("asset_type", sa.String(20), nullable=False),
        sa.Column("shares", sa.Numeric(18, 8), nullable=False),
        sa.Column("avg_cost_basis", sa.Numeric(18, 4), nullable=False),
        sa.Column("current_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("sector", sa.String(50), nullable=True),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_holdings_symbol", "holdings", ["symbol"])

    # --- transactions ---
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(10), nullable=False),
        sa.Column("action", sa.String(4), nullable=False),
        sa.Column("shares", sa.Numeric(18, 8), nullable=False),
        sa.Column("price_per_share", sa.Numeric(18, 4), nullable=False),
        sa.Column("total_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("fees", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("agent_decision_id", sa.Integer, sa.ForeignKey("agent_decisions.id"), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("action IN ('BUY', 'SELL')", name="ck_transaction_action"),
        sa.CheckConstraint("shares > 0", name="ck_transaction_shares_positive"),
    )
    op.create_index("ix_transactions_symbol", "transactions", ["symbol"])

    # --- cash_balances ---
    op.create_table(
        "cash_balances",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("balance", sa.Numeric(18, 4), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("balance >= 0", name="ck_cash_balance_non_negative"),
    )

    # --- risk_profiles ---
    op.create_table(
        "risk_profiles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("aggressiveness", sa.Integer, nullable=False),
        sa.Column("max_single_position_pct", sa.Numeric(5, 2), nullable=False, server_default="5.00"),
        sa.Column("max_sector_pct", sa.Numeric(5, 2), nullable=False, server_default="25.00"),
        sa.Column("min_cash_pct", sa.Numeric(5, 2), nullable=False, server_default="5.00"),
        sa.Column("target_equity_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("target_fixed_income_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("target_cash_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.CheckConstraint("aggressiveness >= 1 AND aggressiveness <= 10", name="ck_risk_aggressiveness"),
    )

    # --- price_history ---
    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(10), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("open", sa.Numeric(18, 4), nullable=True),
        sa.Column("high", sa.Numeric(18, 4), nullable=True),
        sa.Column("low", sa.Numeric(18, 4), nullable=True),
        sa.Column("close", sa.Numeric(18, 4), nullable=False),
        sa.Column("volume", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("symbol", "date", name="uq_price_history_symbol_date"),
    )

    # --- fundamental_snapshots ---
    op.create_table(
        "fundamental_snapshots",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(10), nullable=False),
        sa.Column("snapshot_date", sa.Date, nullable=False),
        sa.Column("pe_ratio", sa.Numeric(10, 2), nullable=True),
        sa.Column("pb_ratio", sa.Numeric(10, 2), nullable=True),
        sa.Column("ps_ratio", sa.Numeric(10, 2), nullable=True),
        sa.Column("ev_ebitda", sa.Numeric(10, 2), nullable=True),
        sa.Column("roe", sa.Numeric(10, 4), nullable=True),
        sa.Column("roa", sa.Numeric(10, 4), nullable=True),
        sa.Column("debt_to_equity", sa.Numeric(10, 4), nullable=True),
        sa.Column("current_ratio", sa.Numeric(10, 4), nullable=True),
        sa.Column("revenue_ttm", sa.Numeric(18, 2), nullable=True),
        sa.Column("net_income_ttm", sa.Numeric(18, 2), nullable=True),
        sa.Column("free_cash_flow_ttm", sa.Numeric(18, 2), nullable=True),
        sa.Column("market_cap", sa.Numeric(18, 2), nullable=True),
        sa.Column("dividend_yield", sa.Numeric(10, 4), nullable=True),
        sa.Column("beta", sa.Numeric(10, 4), nullable=True),
        sa.Column("raw_data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_fundamental_snapshots_symbol", "fundamental_snapshots", ["symbol"])

    # --- sec_filings ---
    op.create_table(
        "sec_filings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(10), nullable=False),
        sa.Column("cik", sa.String(10), nullable=False),
        sa.Column("filing_type", sa.String(10), nullable=False),
        sa.Column("filing_date", sa.Date, nullable=False),
        sa.Column("accession_number", sa.String(25), nullable=False, unique=True),
        sa.Column("filing_url", sa.String(500), nullable=False),
        sa.Column("is_processed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sec_filings_symbol", "sec_filings", ["symbol"])

    # --- earnings_transcripts ---
    op.create_table(
        "earnings_transcripts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(10), nullable=False),
        sa.Column("fiscal_year", sa.Integer, nullable=False),
        sa.Column("fiscal_quarter", sa.Integer, nullable=False),
        sa.Column("event_date", sa.Date, nullable=False),
        sa.Column("full_text", sa.Text, nullable=False),
        sa.Column("ceo_remarks", sa.Text, nullable=True),
        sa.Column("cfo_remarks", sa.Text, nullable=True),
        sa.Column("qa_section", sa.Text, nullable=True),
        sa.Column("sentiment_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("is_processed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("symbol", "fiscal_year", "fiscal_quarter", name="uq_transcript_symbol_year_quarter"),
        sa.CheckConstraint("fiscal_quarter >= 1 AND fiscal_quarter <= 4", name="ck_transcript_quarter"),
    )
    op.create_index("ix_earnings_transcripts_symbol", "earnings_transcripts", ["symbol"])


def downgrade() -> None:
    op.drop_table("earnings_transcripts")
    op.drop_table("sec_filings")
    op.drop_table("fundamental_snapshots")
    op.drop_table("price_history")
    op.drop_table("risk_profiles")
    op.drop_table("cash_balances")
    op.drop_table("transactions")
    op.drop_table("holdings")
    op.drop_table("analysis_reports")
    op.drop_table("agent_decisions")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
