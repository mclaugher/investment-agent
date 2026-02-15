"""Market data models: PriceHistory, FundamentalSnapshot (per §4.3)."""

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Date, Integer, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class PriceHistory(TimestampMixin, Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    high: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    low: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_price_history_symbol_date"),
    )


class FundamentalSnapshot(TimestampMixin, Base):
    __tablename__ = "fundamental_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    pe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    pb_ratio: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    ps_ratio: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    ev_ebitda: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    roe: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    roa: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    debt_to_equity: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    current_ratio: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    revenue_ttm: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    net_income_ttm: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    free_cash_flow_ttm: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    market_cap: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    dividend_yield: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    beta: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSON, server_default="{}", nullable=False)
