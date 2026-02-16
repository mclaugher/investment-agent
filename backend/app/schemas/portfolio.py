"""Portfolio request/response schemas (per §10.1)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class HoldingResponse(BaseModel):
    symbol: str
    asset_type: str
    shares: float
    avg_cost_basis: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    weight_pct: float
    sector: str | None


class PortfolioSummaryResponse(BaseModel):
    total_value: float
    daily_pnl: float
    daily_pnl_pct: float
    total_return: float
    total_return_pct: float
    cash_balance: float
    allocation: dict[str, float]


class PerformancePoint(BaseModel):
    date: str
    value: float


class PerformanceResponse(BaseModel):
    dates: list[str]
    values: list[float]
    benchmark: list[float]


class TransactionResponse(BaseModel):
    id: int
    symbol: str
    action: str
    shares: float
    price_per_share: float
    total_amount: float
    fees: float
    agent_decision_id: int | None
    executed_at: datetime


class PaginatedTransactions(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    limit: int
