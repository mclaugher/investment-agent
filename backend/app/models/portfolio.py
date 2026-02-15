"""Portfolio models: Holding, Transaction, CashBalance, RiskProfile (per §4.1)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, Text, DateTime, Integer, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class Holding(TimestampMixin, Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False)  # equity, etf, bond_etf, money_market
    shares: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    avg_cost_basis: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(50), nullable=True)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # updated_at comes from TimestampMixin


class Transaction(TimestampMixin, Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(4), nullable=False)  # BUY or SELL only
    shares: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    price_per_share: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    fees: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    agent_decision_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("agent_decisions.id"), nullable=True
    )
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("action IN ('BUY', 'SELL')", name="ck_transaction_action"),
        CheckConstraint("shares > 0", name="ck_transaction_shares_positive"),
    )


class CashBalance(Base):
    __tablename__ = "cash_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_cash_balance_non_negative"),
    )


class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aggressiveness: Mapped[int] = mapped_column(Integer, nullable=False)
    max_single_position_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("5.00")
    )
    max_sector_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("25.00")
    )
    min_cash_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("5.00")
    )
    target_equity_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    target_fixed_income_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    target_cash_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_by: Mapped[str] = mapped_column(String(20), nullable=False)  # "human" or "system"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("aggressiveness >= 1 AND aggressiveness <= 10", name="ck_risk_aggressiveness"),
    )
