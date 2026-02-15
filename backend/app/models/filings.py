"""Filing models: SECFiling, EarningsTranscript (per §4.4)."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class SECFiling(TimestampMixin, Base):
    __tablename__ = "sec_filings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    cik: Mapped[str] = mapped_column(String(10), nullable=False)
    filing_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 10-K, 10-Q, 8-K
    filing_date: Mapped[date] = mapped_column(Date, nullable=False)
    accession_number: Mapped[str] = mapped_column(String(25), nullable=False, unique=True)
    filing_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EarningsTranscript(TimestampMixin, Base):
    __tablename__ = "earnings_transcripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    ceo_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    cfo_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    qa_section: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint(
            "symbol", "fiscal_year", "fiscal_quarter",
            name="uq_transcript_symbol_year_quarter",
        ),
        CheckConstraint(
            "fiscal_quarter >= 1 AND fiscal_quarter <= 4",
            name="ck_transcript_quarter",
        ),
    )
