import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import reset_daily_activities_job

logger = logging.getLogger(__name__)

def setup_scheduler():
    """
    Настройка и запуск планировщика для ежедневного сброса активности.
    """
    scheduler = AsyncIOScheduler(timezone="UTC")
    # каждый день в 00:05 UTC удаляем старые записи активности
    scheduler.add_job(
        reset_daily_activities_job,
        trigger='cron',
        hour=0,
        minute=5,
        timezone='UTC'
    )
    scheduler.start()
    logger.info("Scheduler started for daily reset.")
    return scheduler
