"""Settings request/response schemas (per §10.1)."""

from pydantic import BaseModel, Field


class RiskProfileResponse(BaseModel):
    aggressiveness: int
    max_single_position_pct: float
    max_sector_pct: float
    min_cash_pct: float
    target_equity_pct: float
    target_fixed_income_pct: float
    target_cash_pct: float
    updated_by: str
    notes: str | None


class RiskProfileUpdate(BaseModel):
    aggressiveness: int | None = Field(None, ge=1, le=10)
    max_single_position_pct: float | None = Field(None, ge=0, le=100)
    max_sector_pct: float | None = Field(None, ge=0, le=100)
    min_cash_pct: float | None = Field(None, ge=0, le=100)
    target_equity_pct: float | None = Field(None, ge=0, le=100)
    target_fixed_income_pct: float | None = Field(None, ge=0, le=100)
    target_cash_pct: float | None = Field(None, ge=0, le=100)
    notes: str | None = None


class WatchlistItem(BaseModel):
    symbol: str


class WatchlistResponse(BaseModel):
    symbols: list[str]


class ScheduleEntry(BaseModel):
    name: str
    task: str
    schedule: str
    description: str


class ScheduleResponse(BaseModel):
    schedules: list[ScheduleEntry]
