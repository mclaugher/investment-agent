"""Celery application configuration with beat schedule (per §9.1).

Uses Redis as broker and result backend.
"""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery = Celery(
    "superhuman_alpha_fund",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.data_refresh",
        "app.tasks.filing_monitor",
        "app.tasks.analysis_cycle",
        "app.tasks.cleanup",
    ],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="US/Eastern",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)

# Per §9.1: Beat schedule for automated data ingestion and analysis
celery.conf.beat_schedule = {
    "refresh-market-data": {
        "task": "app.tasks.data_refresh.refresh_market_data",
        "schedule": crontab(minute="*/15", hour="9-16", day_of_week="1-5"),
    },
    "refresh-after-hours": {
        "task": "app.tasks.data_refresh.refresh_market_data",
        "schedule": crontab(minute="0", hour="17-23,0-8", day_of_week="1-5"),
    },
    "refresh-fundamentals": {
        "task": "app.tasks.data_refresh.refresh_fundamentals",
        "schedule": crontab(minute="30", hour="18", day_of_week="1-5"),
    },
    "check-new-filings": {
        "task": "app.tasks.filing_monitor.check_new_filings",
        "schedule": crontab(minute="*/30", hour="8-20", day_of_week="1-5"),
    },
    "daily-analysis-cycle": {
        "task": "app.tasks.analysis_cycle.run_full_analysis",
        "schedule": crontab(minute="0", hour="19", day_of_week="1-5"),
    },
    "weekly-cleanup": {
        "task": "app.tasks.cleanup.cleanup_old_data",
        "schedule": crontab(minute="0", hour="3", day_of_week="0"),
    },
}
