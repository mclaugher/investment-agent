"""Portfolio API router (per §10.1).

Endpoints for portfolio summary, holdings, performance, and transactions.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import verify_token
from app.database import get_db
from app.models.portfolio import CashBalance, Holding, Transaction
from app.schemas.portfolio import (
    HoldingResponse,
    PaginatedTransactions,
    PerformanceResponse,
    PortfolioSummaryResponse,
    TransactionResponse,
)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"], dependencies=[Depends(verify_token)])


@router.get("", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(db: AsyncSession = Depends(get_db)):
    """Portfolio summary with total value, P&L, allocation (per §10.1)."""
    # Get all holdings
    result = await db.execute(select(Holding))
    holdings = result.scalars().all()

    # Get cash balance
    cash_result = await db.execute(select(CashBalance).order_by(CashBalance.id.desc()).limit(1))
    cash = cash_result.scalar_one_or_none()
    cash_balance = float(cash.balance) if cash else 0.0

    # Calculate totals
    total_equity_value = sum(float(h.shares) * float(h.current_price) for h in holdings)
    total_cost = sum(float(h.shares) * float(h.avg_cost_basis) for h in holdings)
    total_value = total_equity_value + cash_balance
    total_return = total_equity_value - total_cost
    total_return_pct = (total_return / total_cost * 100) if total_cost > 0 else 0.0

    # Allocation by sector
    allocation: dict[str, float] = {}
    for h in holdings:
        sector = h.sector or "other"
        market_val = float(h.shares) * float(h.current_price)
        allocation[sector] = allocation.get(sector, 0.0) + market_val

    # Normalize to percentages
    if total_value > 0:
        allocation = {k: round(v / total_value * 100, 2) for k, v in allocation.items()}
        allocation["cash"] = round(cash_balance / total_value * 100, 2)

    return PortfolioSummaryResponse(
        total_value=round(total_value, 2),
        daily_pnl=0.0,  # Would need previous close data
        daily_pnl_pct=0.0,
        total_return=round(total_return, 2),
        total_return_pct=round(total_return_pct, 2),
        cash_balance=round(cash_balance, 2),
        allocation=allocation,
    )


@router.get("/holdings", response_model=list[HoldingResponse])
async def get_holdings(db: AsyncSession = Depends(get_db)):
    """All holdings with P&L and weight (per §10.1)."""
    result = await db.execute(select(Holding))
    holdings = result.scalars().all()

    # Calculate total portfolio value for weights
    cash_result = await db.execute(select(CashBalance).order_by(CashBalance.id.desc()).limit(1))
    cash = cash_result.scalar_one_or_none()
    cash_balance = float(cash.balance) if cash else 0.0

    total_value = sum(float(h.shares) * float(h.current_price) for h in holdings) + cash_balance

    responses = []
    for h in holdings:
        market_value = float(h.shares) * float(h.current_price)
        cost_value = float(h.shares) * float(h.avg_cost_basis)
        pnl = market_value - cost_value
        pnl_pct = (pnl / cost_value * 100) if cost_value > 0 else 0.0

        responses.append(HoldingResponse(
            symbol=h.symbol,
            asset_type=h.asset_type,
            shares=float(h.shares),
            avg_cost_basis=float(h.avg_cost_basis),
            current_price=float(h.current_price),
            market_value=round(market_value, 2),
            unrealized_pnl=round(pnl, 2),
            unrealized_pnl_pct=round(pnl_pct, 2),
            weight_pct=round(market_value / total_value * 100, 2) if total_value > 0 else 0.0,
            sector=h.sector,
        ))

    return responses


@router.get("/performance", response_model=PerformanceResponse)
async def get_performance(period: str = Query("1y", pattern="^(1M|3M|6M|1Y|ALL)$", alias="period")):
    """Performance time series (per §10.1). Placeholder — requires historical NAV tracking."""
    # This would need a NAV history table for real implementation
    return PerformanceResponse(dates=[], values=[], benchmark=[])


@router.get("/transactions", response_model=PaginatedTransactions)
async def get_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Paginated transaction history (per §10.1)."""
    offset = (page - 1) * limit

    # Count total
    count_result = await db.execute(select(func.count(Transaction.id)))
    total = count_result.scalar() or 0

    # Fetch page
    result = await db.execute(
        select(Transaction)
        .order_by(Transaction.executed_at.desc())
        .offset(offset)
        .limit(limit)
    )
    transactions = result.scalars().all()

    items = [
        TransactionResponse(
            id=t.id,
            symbol=t.symbol,
            action=t.action,
            shares=float(t.shares),
            price_per_share=float(t.price_per_share),
            total_amount=float(t.total_amount),
            fees=float(t.fees) if t.fees else 0.0,
            agent_decision_id=t.agent_decision_id,
            executed_at=t.executed_at,
        )
        for t in transactions
    ]

    return PaginatedTransactions(items=items, total=total, page=page, limit=limit)
