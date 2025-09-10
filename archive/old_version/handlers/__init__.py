# handlers/__init__.py
"""
Package initializer for handlers. Imports individual handlers and registers them.
"""
from aiogram import F
from aiogram.filters import Command
from aiogram.types import ContentType, Message
from geopy.extra.rate_limiter import RateLimiter
from astral.geocoder import lookup as AstralLookup

from .start import cmd_start
from .help import cmd_help
from .plan import handle_plan, handle_log_activity
from .mantra import handle_mantra, handle_mantra_category
from .diary import open_diary, process_diary_entry, cmd_mydiary, DiaryStates
from .location import register_location_handler
from .stats import handle_stats_button, process_show_group_stats
from db import get_mantra_categories


__all__ = [
    "cmd_start", "cmd_help",
    "handle_plan", "handle_log_activity",
    "handle_mantra", "handle_mantra_category",
    "open_diary", "process_diary_entry", "cmd_mydiary", "DiaryStates",
    "handle_location_button", "handle_location_cancel", "handle_user_location", "handle_location",
    "handle_stats_button", "process_show_group_stats",
    "register_all_handlers"
]

async def is_mantra_category(message: Message) -> bool:
    """Filter: message text matches a mantra category or cancel button."""
    categories = await get_mantra_categories()
    return message.text in categories or message.text == "❌ Главное меню"


def register_all_handlers(dp: any, geocode: RateLimiter, astral_geo: AstralLookup) -> None:
    """Register all handlers from this package using Aiogram v3 API."""
    # /start and help
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_help, F.text == "❓ Помощь")

    # plan
    dp.message.register(handle_plan, Command("plan"))
    dp.message.register(handle_plan, F.text.in_(["🗓️ План дня", "/today"]))
    dp.callback_query.register(handle_log_activity, F.data.startswith("log_activity:"))

    # mantra
    dp.message.register(handle_mantra, Command("mantra"))
    dp.message.register(handle_mantra, F.text.in_(["✨ Мантра", "Мантры"]))
    dp.message.register(handle_mantra_category, is_mantra_category)

    # diary
    dp.message.register(open_diary, Command("diary"))
    dp.message.register(open_diary, F.text.in_(["✍️ Дневник", "/diary"]))
    dp.message.register(process_diary_entry, DiaryStates.waiting_for_entry)
    dp.message.register(cmd_mydiary, Command("mydiary"))

    # location
    register_location_handler(dp, geocode, astral_geo)

    
    # stats
    dp.message.register(handle_stats_button, F.text == "📊 Статистика")
    dp.message.register(handle_stats_button, Command("stats"))
    dp.callback_query.register(process_show_group_stats, F.data == "show_group_stats")

    # Note: no generic text fallback to not intercept other handlers
