"""Portfolio tools for agent use (per §6.6).

CRITICAL: validate_trade and execute_trade enforce all hard constraints from §18:
- No margin trading, no short selling
- Cash balance >= 0
- Position limits, sector limits, minimum cash reserve
"""

from datetime import datetime, timezone
from decimal import Decimal

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.portfolio import CashBalance, Holding, RiskProfile, Transaction
from app.models.reports import AgentDecision


async def _get_session() -> AsyncSession:
    """Get a new async session. Tools are stateless — each call gets its own session."""
    return async_session()


@tool
async def get_current_holdings() -> list[dict]:
    """Get all current portfolio holdings with P&L calculations.
    Returns: [{symbol, shares, avg_cost, current_price, market_value,
               unrealized_pnl, unrealized_pnl_pct, sector, asset_type, weight_pct}]"""
    async with async_session() as session:
        result = await session.execute(select(Holding).where(Holding.shares > 0))
        holdings = result.scalars().all()

        if not holdings:
            return []

        total_value = sum(float(h.shares * h.current_price) for h in holdings)

        # Add cash to total for weight calculation
        cash_result = await session.execute(select(CashBalance).limit(1))
        cash = cash_result.scalar_one_or_none()
        cash_balance = float(cash.balance) if cash else 0
        portfolio_total = total_value + cash_balance

        output = []
        for h in holdings:
            market_value = float(h.shares * h.current_price)
            cost_basis_total = float(h.shares * h.avg_cost_basis)
            pnl = market_value - cost_basis_total
            pnl_pct = (pnl / cost_basis_total * 100) if cost_basis_total > 0 else 0

            output.append({
                "symbol": h.symbol,
                "shares": float(h.shares),
                "avg_cost": float(h.avg_cost_basis),
                "current_price": float(h.current_price),
                "market_value": round(market_value, 2),
                "unrealized_pnl": round(pnl, 2),
                "unrealized_pnl_pct": round(pnl_pct, 2),
                "sector": h.sector,
                "asset_type": h.asset_type,
                "weight_pct": round(market_value / portfolio_total * 100, 2) if portfolio_total > 0 else 0,
            })

        return output


@tool
async def get_cash_balance() -> dict:
    """Get current cash balance and reserve requirements.
    Returns: {balance, min_reserve, available_for_investment, pct_of_portfolio}"""
    async with async_session() as session:
        cash_result = await session.execute(select(CashBalance).limit(1))
        cash = cash_result.scalar_one_or_none()
        balance = float(cash.balance) if cash else 0

        rp_result = await session.execute(select(RiskProfile).limit(1))
        rp = rp_result.scalar_one_or_none()

        # Calculate total portfolio value
        holdings_result = await session.execute(select(Holding).where(Holding.shares > 0))
        holdings = holdings_result.scalars().all()
        holdings_value = sum(float(h.shares * h.current_price) for h in holdings)
        portfolio_total = holdings_value + balance

        min_cash_pct = float(rp.min_cash_pct) / 100 if rp else 0.05
        min_reserve = portfolio_total * min_cash_pct
        available = max(balance - min_reserve, 0)

        return {
            "balance": round(balance, 2),
            "min_reserve": round(min_reserve, 2),
            "available_for_investment": round(available, 2),
            "pct_of_portfolio": round(balance / portfolio_total * 100, 2) if portfolio_total > 0 else 100,
        }


@tool
async def get_risk_profile() -> dict:
    """Get current risk profile settings.
    Returns all RiskProfile fields as dict."""
    async with async_session() as session:
        result = await session.execute(select(RiskProfile).limit(1))
        rp = result.scalar_one_or_none()

        if not rp:
            return {"error": "No risk profile configured"}

        return {
            "aggressiveness": rp.aggressiveness,
            "max_single_position_pct": float(rp.max_single_position_pct),
            "max_sector_pct": float(rp.max_sector_pct),
            "min_cash_pct": float(rp.min_cash_pct),
            "target_equity_pct": float(rp.target_equity_pct),
            "target_fixed_income_pct": float(rp.target_fixed_income_pct),
            "target_cash_pct": float(rp.target_cash_pct),
            "updated_by": rp.updated_by,
            "notes": rp.notes,
        }


@tool
async def get_portfolio_metrics() -> dict:
    """Calculate portfolio-level risk and return metrics.
    Returns: {total_value, daily_pnl, total_return_pct, sector_weights,
              top_5_positions, concentration_hhi}"""
    async with async_session() as session:
        holdings_result = await session.execute(select(Holding).where(Holding.shares > 0))
        holdings = holdings_result.scalars().all()

        cash_result = await session.execute(select(CashBalance).limit(1))
        cash = cash_result.scalar_one_or_none()
        cash_balance = float(cash.balance) if cash else 0

        if not holdings:
            return {
                "total_value": cash_balance,
                "daily_pnl": 0,
                "total_return_pct": 0,
                "sector_weights": {},
                "top_5_positions": [],
                "concentration_hhi": 0,
            }

        holdings_value = sum(float(h.shares * h.current_price) for h in holdings)
        cost_basis_total = sum(float(h.shares * h.avg_cost_basis) for h in holdings)
        total_value = holdings_value + cash_balance

        total_return_pct = ((holdings_value - cost_basis_total) / cost_basis_total * 100) if cost_basis_total > 0 else 0

        # Sector weights
        sector_weights: dict[str, float] = {}
        for h in holdings:
            sector = h.sector or "unknown"
            mv = float(h.shares * h.current_price)
            sector_weights[sector] = sector_weights.get(sector, 0) + mv
        sector_weights = {k: round(v / total_value * 100, 2) for k, v in sector_weights.items()}

        # Top 5 positions
        positions = []
        for h in holdings:
            mv = float(h.shares * h.current_price)
            positions.append({
                "symbol": h.symbol,
                "market_value": round(mv, 2),
                "weight_pct": round(mv / total_value * 100, 2),
            })
        positions.sort(key=lambda x: x["market_value"], reverse=True)

        # HHI (Herfindahl-Hirschman Index) for concentration
        weights = [p["weight_pct"] for p in positions]
        hhi = round(sum(w ** 2 for w in weights), 2)

        return {
            "total_value": round(total_value, 2),
            "daily_pnl": 0,  # Requires price history comparison — implemented in Phase 3+
            "total_return_pct": round(total_return_pct, 2),
            "sector_weights": sector_weights,
            "top_5_positions": positions[:5],
            "concentration_hhi": hhi,
        }


@tool
async def validate_trade(action: str, symbol: str, shares: float, estimated_price: float) -> dict:
    """Validate a proposed trade against all constraints.
    Checks: sufficient cash (buys), sufficient shares (sells), position limits,
    sector limits, minimum cash reserve, NO MARGIN, NO SHORT SELLING.
    Returns: {valid, errors, warnings, post_trade_position_pct, post_trade_cash}"""
    errors = []
    warnings = []

    # §18 HARD CONSTRAINT: Only BUY or SELL allowed
    if action not in ("BUY", "SELL"):
        errors.append(f"Invalid action '{action}'. Only BUY and SELL are allowed. No margin, no short selling.")
        return {"valid": False, "errors": errors, "warnings": [], "post_trade_position_pct": 0, "post_trade_cash": 0}

    if shares <= 0:
        errors.append("Shares must be positive")
        return {"valid": False, "errors": errors, "warnings": [], "post_trade_position_pct": 0, "post_trade_cash": 0}

    trade_amount = shares * estimated_price

    async with async_session() as session:
        # Get cash balance
        cash_result = await session.execute(select(CashBalance).limit(1))
        cash = cash_result.scalar_one_or_none()
        cash_balance = float(cash.balance) if cash else 0

        # Get risk profile
        rp_result = await session.execute(select(RiskProfile).limit(1))
        rp = rp_result.scalar_one_or_none()

        # Get all holdings
        holdings_result = await session.execute(select(Holding).where(Holding.shares > 0))
        holdings = holdings_result.scalars().all()

        holdings_value = sum(float(h.shares * h.current_price) for h in holdings)
        portfolio_total = holdings_value + cash_balance

        # Find existing holding for this symbol
        existing = next((h for h in holdings if h.symbol == symbol), None)
        existing_shares = float(existing.shares) if existing else 0
        existing_sector = existing.sector if existing else None

        if action == "BUY":
            # §18: Cash balance must remain >= 0
            post_trade_cash = cash_balance - trade_amount
            if post_trade_cash < 0:
                errors.append(
                    f"Insufficient cash. Balance: ${cash_balance:,.2f}, "
                    f"Trade cost: ${trade_amount:,.2f}. NO MARGIN TRADING ALLOWED."
                )

            # §18: Minimum cash reserve
            if rp:
                min_cash = portfolio_total * float(rp.min_cash_pct) / 100
                if post_trade_cash < min_cash:
                    errors.append(
                        f"Post-trade cash ${post_trade_cash:,.2f} would be below minimum "
                        f"reserve ${min_cash:,.2f} ({float(rp.min_cash_pct)}% of portfolio)"
                    )

            # Post-trade position size
            new_position_value = (existing_shares + shares) * estimated_price
            post_position_pct = (new_position_value / portfolio_total * 100) if portfolio_total > 0 else 0

            # §18: Position limit
            if rp and post_position_pct > float(rp.max_single_position_pct):
                errors.append(
                    f"Post-trade position {post_position_pct:.1f}% exceeds max "
                    f"{float(rp.max_single_position_pct)}% limit"
                )

            # §18: Sector limit
            if rp and existing_sector:
                sector_value = sum(
                    float(h.shares * h.current_price)
                    for h in holdings if h.sector == existing_sector
                )
                post_sector_value = sector_value + trade_amount
                post_sector_pct = (post_sector_value / portfolio_total * 100) if portfolio_total > 0 else 0
                if post_sector_pct > float(rp.max_sector_pct):
                    errors.append(
                        f"Post-trade sector '{existing_sector}' weight {post_sector_pct:.1f}% "
                        f"exceeds max {float(rp.max_sector_pct)}% limit"
                    )

        elif action == "SELL":
            post_trade_cash = cash_balance + trade_amount

            # §18: Must own sufficient shares (NO SHORT SELLING)
            if existing_shares < shares:
                errors.append(
                    f"Insufficient shares. Own {existing_shares}, trying to sell {shares}. "
                    f"NO SHORT SELLING ALLOWED."
                )

            new_position_value = max((existing_shares - shares), 0) * estimated_price
            post_position_pct = (new_position_value / portfolio_total * 100) if portfolio_total > 0 else 0

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "post_trade_position_pct": round(post_position_pct, 2),
            "post_trade_cash": round(post_trade_cash, 2),
        }


@tool
async def execute_trade(action: str, symbol: str, shares: float, price: float, decision_id: int) -> dict:
    """Execute a validated trade. Updates holdings, cash balance, creates transaction record.
    REJECTS: any action other than BUY or SELL, any trade that would make cash negative.
    Returns: {success, transaction_id, new_cash_balance, error}"""

    # §18 HARD CONSTRAINT: Only BUY or SELL
    if action not in ("BUY", "SELL"):
        return {"success": False, "transaction_id": None, "new_cash_balance": None,
                "error": f"REJECTED: Invalid action '{action}'. Only BUY and SELL allowed."}

    if shares <= 0:
        return {"success": False, "transaction_id": None, "new_cash_balance": None,
                "error": "REJECTED: Shares must be positive."}

    total_amount = Decimal(str(shares)) * Decimal(str(price))

    async with async_session() as session:
        async with session.begin():
            # Get cash balance
            cash_result = await session.execute(select(CashBalance).limit(1))
            cash = cash_result.scalar_one_or_none()
            if not cash:
                return {"success": False, "transaction_id": None, "new_cash_balance": None,
                        "error": "No cash balance record found."}

            # Get existing holding
            holding_result = await session.execute(
                select(Holding).where(Holding.symbol == symbol)
            )
            holding = holding_result.scalar_one_or_none()

            now = datetime.now(timezone.utc)

            if action == "BUY":
                # §18: Cash balance must not go negative
                new_balance = cash.balance - total_amount
                if new_balance < 0:
                    return {"success": False, "transaction_id": None, "new_cash_balance": float(cash.balance),
                            "error": f"REJECTED: Trade would make cash negative (${float(new_balance):,.2f}). NO MARGIN."}

                cash.balance = new_balance

                if holding:
                    # Update existing holding with new average cost basis
                    old_cost = holding.shares * holding.avg_cost_basis
                    new_shares = holding.shares + Decimal(str(shares))
                    new_cost = old_cost + total_amount
                    holding.shares = new_shares
                    holding.avg_cost_basis = new_cost / new_shares if new_shares > 0 else Decimal("0")
                    holding.current_price = Decimal(str(price))
                else:
                    # Create new holding
                    holding = Holding(
                        symbol=symbol,
                        asset_type="equity",
                        shares=Decimal(str(shares)),
                        avg_cost_basis=Decimal(str(price)),
                        current_price=Decimal(str(price)),
                        acquired_at=now,
                    )
                    session.add(holding)

            elif action == "SELL":
                # §18: Cannot sell more than owned (NO SHORT SELLING)
                if not holding or holding.shares < Decimal(str(shares)):
                    owned = float(holding.shares) if holding else 0
                    return {"success": False, "transaction_id": None, "new_cash_balance": float(cash.balance),
                            "error": f"REJECTED: Insufficient shares. Own {owned}, trying to sell {shares}. NO SHORT SELLING."}

                cash.balance = cash.balance + total_amount
                holding.shares = holding.shares - Decimal(str(shares))
                holding.current_price = Decimal(str(price))

                # If fully sold, remove holding (set shares to 0, will be filtered)

            # Create transaction record
            txn = Transaction(
                symbol=symbol,
                action=action,
                shares=Decimal(str(shares)),
                price_per_share=Decimal(str(price)),
                total_amount=total_amount,
                agent_decision_id=decision_id,
                executed_at=now,
            )
            session.add(txn)

            await session.flush()

            return {
                "success": True,
                "transaction_id": txn.id,
                "new_cash_balance": round(float(cash.balance), 2),
                "error": None,
            }
