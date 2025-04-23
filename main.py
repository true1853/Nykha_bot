#!/usr/bin/env python3
"""
Refactored entry point for the Telegram bot using Aiogram, Geopy, Astral, and APScheduler.
Improvements:
 - PEP8 conformance
 - Dependency injection
 - Clear separation of concerns
 - Type hints
 - Modular configuration loading
 - Enhanced logging
"""
import asyncio
import logging
import os
from typing import Callable

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from astral.geocoder import lookup as astral_lookup

from config import API_TOKEN, GEOPY_USER_AGENT
from db import init_db, populate_mantras_if_empty
from handlers import register_all_handlers

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_geocoder(user_agent: str, min_delay: float = 1.1, error_wait: float = 5.0) -> Callable:
    """
    Create a reverse geocode function with rate limiting.
    """
    geolocator = Nominatim(user_agent=user_agent)
    return RateLimiter(
        geolocator.reverse,
        min_delay_seconds=min_delay,
        error_wait_seconds=error_wait,
    )


def create_scheduler() -> AsyncIOScheduler:
    """
    Initialize and return an AsyncIO scheduler.
    """
    scheduler = AsyncIOScheduler()
    scheduler.start()
    logger.info("Scheduler started.")
    return scheduler


async def init_application() -> None:
    """
    Initialize DB, scheduler, and other resources.
    """
    await init_db()
    await populate_mantras_if_empty()


async def main() -> None:
    # Validate configuration
    if not API_TOKEN:
        logger.error("API_TOKEN is missing in environment.")
        raise RuntimeError("API_TOKEN must be set in environment variables.")

    # Setup geocoding utilities
    geocode = create_geocoder(GEOPY_USER_AGENT)
    logger.info("Geocoder initialized.")

    # Astral lookup alias
    astral_geo = astral_lookup
    logger.info("Astral geocoder ready.")

    # Setup bot and dispatcher
    bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="MarkdownV2"))
    dp = Dispatcher(storage=MemoryStorage())

    # Initialize application components
    await init_application()

    # Setup scheduler for periodic tasks
    scheduler = create_scheduler()
    # You can pass scheduler into setup_scheduler if needed
    # setup_scheduler(scheduler)

    # Register handlers with dependencies
    register_all_handlers(dp=dp, geocode=geocode, astral_geo=astral_geo)

    # Start polling
    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()
        scheduler.shutdown()
        logger.info("Bot and scheduler shut down.")


if __name__ == "__main__":  # pragma: no cover
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
