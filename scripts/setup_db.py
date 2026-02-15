#!/usr/bin/env python
"""Create DB tables, run migrations, and seed initial data (per §3, §17 Phase 1).

Usage:
    python -m scripts.setup_db          # from repo root
    python scripts/setup_db.py          # direct invocation

Requires a running PostgreSQL instance matching DATABASE_URL in config.
"""

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

# Ensure backend/ is on sys.path so `app.*` imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy import select, text

from app.config import settings
from app.database import Base, engine, async_session
from app.models.portfolio import CashBalance, RiskProfile

# Import all models to register them with Base.metadata
import app.models  # noqa: F401


async def run_migrations() -> None:
    """Run Alembic migrations programmatically."""
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config(str(Path(__file__).resolve().parent.parent / "backend" / "alembic.ini"))
    alembic_cfg.set_main_option(
        "script_location",
        str(Path(__file__).resolve().parent.parent / "backend" / "alembic"),
    )
    command.upgrade(alembic_cfg, "head")
    print("[setup_db] Alembic migrations applied.")


async def seed_initial_data() -> None:
    """Seed the initial CashBalance and RiskProfile rows if they don't already exist."""
    async with async_session() as session:
        # --- CashBalance ---
        result = await session.execute(select(CashBalance).limit(1))
        if result.scalar_one_or_none() is None:
            session.add(CashBalance(balance=Decimal(str(settings.initial_cash_balance))))
            print(f"[setup_db] Seeded CashBalance: ${settings.initial_cash_balance:,}")
        else:
            print("[setup_db] CashBalance already exists, skipping.")

        # --- RiskProfile (balanced defaults for aggressiveness=5) ---
        result = await session.execute(select(RiskProfile).limit(1))
        if result.scalar_one_or_none() is None:
            session.add(
                RiskProfile(
                    aggressiveness=settings.default_aggressiveness,
                    max_single_position_pct=Decimal("5.00"),
                    max_sector_pct=Decimal("25.00"),
                    min_cash_pct=Decimal("5.00"),
                    target_equity_pct=Decimal("60.00"),
                    target_fixed_income_pct=Decimal("30.00"),
                    target_cash_pct=Decimal("10.00"),
                    updated_by="system",
                    notes="Initial default risk profile (aggressiveness=5, balanced).",
                )
            )
            print(f"[setup_db] Seeded RiskProfile: aggressiveness={settings.default_aggressiveness}")
        else:
            print("[setup_db] RiskProfile already exists, skipping.")

        await session.commit()


async def verify_tables() -> None:
    """Print all tables visible in the database."""
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT tablename FROM pg_catalog.pg_tables "
                "WHERE schemaname = 'public' ORDER BY tablename"
            )
        )
        tables = [row[0] for row in result]
        print(f"[setup_db] Tables in database ({len(tables)}): {tables}")


async def main() -> None:
    print(f"[setup_db] DATABASE_URL = {settings.database_url.split('@')[1] if '@' in settings.database_url else '(hidden)'}")

    # 1. Run Alembic migrations (creates tables)
    await run_migrations()

    # 2. Verify tables exist
    await verify_tables()

    # 3. Seed initial data
    await seed_initial_data()

    print("[setup_db] Done.")


if __name__ == "__main__":
    asyncio.run(main())
