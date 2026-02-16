"""Settings API router (per §10.1).

Risk profile management, watchlist, and schedule configuration.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import verify_token
from app.database import get_db
from app.models.portfolio import Holding, RiskProfile
from app.schemas.settings import (
    RiskProfileResponse,
    RiskProfileUpdate,
    ScheduleEntry,
    ScheduleResponse,
    WatchlistItem,
    WatchlistResponse,
)

router = APIRouter(prefix="/api/settings", tags=["settings"], dependencies=[Depends(verify_token)])

# In-memory watchlist (would use DB table in production)
_watchlist: list[str] = []


@router.get("/risk-profile", response_model=RiskProfileResponse)
async def get_risk_profile(db: AsyncSession = Depends(get_db)):
    """Current risk profile (per §10.1)."""
    result = await db.execute(select(RiskProfile).order_by(RiskProfile.id.desc()).limit(1))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="No risk profile configured")

    return RiskProfileResponse(
        aggressiveness=profile.aggressiveness,
        max_single_position_pct=float(profile.max_single_position_pct),
        max_sector_pct=float(profile.max_sector_pct),
        min_cash_pct=float(profile.min_cash_pct),
        target_equity_pct=float(profile.target_equity_pct),
        target_fixed_income_pct=float(profile.target_fixed_income_pct),
        target_cash_pct=float(profile.target_cash_pct),
        updated_by=profile.updated_by,
        notes=profile.notes,
    )


@router.put("/risk-profile", response_model=RiskProfileResponse)
async def update_risk_profile(update: RiskProfileUpdate, db: AsyncSession = Depends(get_db)):
    """Update risk profile with partial update support (per §10.1)."""
    result = await db.execute(select(RiskProfile).order_by(RiskProfile.id.desc()).limit(1))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="No risk profile configured")

    # Apply partial updates
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(profile, field, value)

    profile.updated_by = "human"
    profile.updated_at = datetime.now(timezone.utc)

    # Validate allocation sum if any allocation field was changed
    allocation_fields = {"target_equity_pct", "target_fixed_income_pct", "target_cash_pct"}
    if allocation_fields & set(update_data.keys()):
        total = float(profile.target_equity_pct) + float(profile.target_fixed_income_pct) + float(profile.target_cash_pct)
        if abs(total - 100.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Allocation targets must sum to 100% (currently {total:.2f}%)",
            )

    await db.commit()
    await db.refresh(profile)

    return RiskProfileResponse(
        aggressiveness=profile.aggressiveness,
        max_single_position_pct=float(profile.max_single_position_pct),
        max_sector_pct=float(profile.max_sector_pct),
        min_cash_pct=float(profile.min_cash_pct),
        target_equity_pct=float(profile.target_equity_pct),
        target_fixed_income_pct=float(profile.target_fixed_income_pct),
        target_cash_pct=float(profile.target_cash_pct),
        updated_by=profile.updated_by,
        notes=profile.notes,
    )


@router.get("/watchlist", response_model=WatchlistResponse)
async def get_watchlist():
    """Current watchlist (per §10.1)."""
    return WatchlistResponse(symbols=_watchlist)


@router.post("/watchlist", response_model=WatchlistResponse)
async def add_to_watchlist(item: WatchlistItem):
    """Add symbol to watchlist (per §10.1)."""
    symbol = item.symbol.upper()
    if symbol not in _watchlist:
        _watchlist.append(symbol)
    return WatchlistResponse(symbols=_watchlist)


@router.delete("/watchlist/{symbol}", response_model=WatchlistResponse)
async def remove_from_watchlist(symbol: str):
    """Remove from watchlist (per §10.1)."""
    symbol = symbol.upper()
    if symbol in _watchlist:
        _watchlist.remove(symbol)
    else:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not in watchlist")
    return WatchlistResponse(symbols=_watchlist)


@router.get("/schedule", response_model=ScheduleResponse)
async def get_schedule():
    """Current Celery beat schedule (per §10.1)."""
    schedules = [
        ScheduleEntry(
            name="refresh-market-data",
            task="app.tasks.data_refresh.refresh_market_data",
            schedule="Every 15 min during market hours (9-16 ET, Mon-Fri)",
            description="Update prices for all holdings and watchlist symbols",
        ),
        ScheduleEntry(
            name="refresh-after-hours",
            task="app.tasks.data_refresh.refresh_market_data",
            schedule="Hourly after market hours (17-8 ET, Mon-Fri)",
            description="Hourly price refresh outside market hours",
        ),
        ScheduleEntry(
            name="refresh-fundamentals",
            task="app.tasks.data_refresh.refresh_fundamentals",
            schedule="6:30 PM ET weekdays",
            description="Pull latest fundamental data for all tracked symbols",
        ),
        ScheduleEntry(
            name="check-new-filings",
            task="app.tasks.filing_monitor.check_new_filings",
            schedule="Every 30 min during business hours (8-20 ET, Mon-Fri)",
            description="Check SEC EDGAR for new filings",
        ),
        ScheduleEntry(
            name="daily-analysis-cycle",
            task="app.tasks.analysis_cycle.run_full_analysis",
            schedule="7 PM ET weekdays",
            description="Run full multi-agent analysis cycle",
        ),
        ScheduleEntry(
            name="weekly-cleanup",
            task="app.tasks.cleanup.cleanup_old_data",
            schedule="3 AM Sunday",
            description="Archive old reports, prune stale data",
        ),
    ]
    return ScheduleResponse(schedules=schedules)
