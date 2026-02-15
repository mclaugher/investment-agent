"""Report models: AnalysisReport, AgentDecision (per §4.2)."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    DateTime,
    Boolean,
    func,
)
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    agent_role: Mapped[str] = mapped_column(String(50), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    sector: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    key_metrics: Mapped[dict] = mapped_column(JSON, server_default="{}", nullable=False)
    parent_report_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("analysis_reports.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Self-referential relationships per §4.2
    children: Mapped[list["AnalysisReport"]] = relationship(
        "AnalysisReport", back_populates="parent", cascade="all, delete-orphan"
    )
    parent: Mapped[Optional["AnalysisReport"]] = relationship(
        "AnalysisReport", remote_side=[id], back_populates="children"
    )

    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 1 AND confidence <= 10)",
            name="ck_report_confidence",
        ),
        # GIN index on content for full-text search (per §4.2)
        Index(
            "ix_analysis_reports_content_gin",
            "content",
            postgresql_using="gin",
            postgresql_ops={"content": "gin_trgm_ops"},
        ),
    )


class AgentDecision(Base):
    __tablename__ = "agent_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_type: Mapped[str] = mapped_column(String(20), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(10), nullable=True)
    action: Mapped[str | None] = mapped_column(String(4), nullable=True)
    recommended_shares: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    recommended_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    supporting_report_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    dissenting_opinions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="proposed"
    )
    human_override: Mapped[bool] = mapped_column(Boolean, default=False)
    human_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "action IS NULL OR action IN ('BUY', 'SELL')",
            name="ck_decision_action",
        ),
        CheckConstraint("confidence >= 1 AND confidence <= 10", name="ck_decision_confidence"),
    )
