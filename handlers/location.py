# handlers/location.py
"""
Location handlers: prompt for and process user geolocation
"""
import logging
from aiogram import F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    ContentType
)
from geopy.extra.rate_limiter import RateLimiter
from astral.geocoder import lookup as AstralLookup, database as astral_database
from db import update_user_location
from config import DEFAULT_TIMEZONE
from utils import escape_md
from keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)

def register_location_handler(dp, geocode: RateLimiter, astral_geo: AstralLookup) -> None:
    """Register location-related handlers with access to geocode and astral_geo."""
    @dp.message(F.text == "📍 Локация")
    async def handle_location_button(message: Message) -> None:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📍 Отправить мою геолокацию", request_location=True)],
                [KeyboardButton(text="🚫 Отмена")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        prompt = (
            "Чтобы точнее показывать время восхода/заката, нужна твоя геолокация 🌍.\n"
            "Нажми кнопку 'Отправить...' или 'Отмена' 👇"
        )
        await message.answer(prompt, parse_mode=None, reply_markup=keyboard)

    @dp.message(F.text == "🚫 Отмена")
    async def handle_location_cancel(message: Message) -> None:
        await message.answer(
            "Отмена. Возвращаемся в главное меню.",
            parse_mode=None,
            reply_markup=get_main_menu_keyboard()
        )

    @dp.message(F.content_type == ContentType.LOCATION)
    async def handle_user_location_wrapper(message: Message) -> None:
        # wrapper to pass geocode and astral_geo into the logic
        await handle_user_location(message, geocode, astral_geo)

async def handle_user_location(
    message: Message,
    geocode: RateLimiter,
    astral_geo: AstralLookup
) -> None:
    """Process user-sent location: reverse geocode, save, confirm."""
    user_id = message.from_user.id
    lat = message.location.latitude
    lon = message.location.longitude
    logger.info(f"Received location from user {user_id}: lat={lat}, lon={lon}")

    await message.answer(
        "⏳ Определяю город и часовой пояс...",
        parse_mode=None,
        reply_markup=ReplyKeyboardRemove()
    )

    city = "Неизвестно"
    tz_str = DEFAULT_TIMEZONE

    # 1) geocode lookup
    try:
        location_info = geocode(
            f"{lat}, {lon}",
            language='ru',
            exactly_one=True,
            addressdetails=True,
            timeout=10
        )
        addr = location_info.raw.get('address', {}) if location_info else {}
        city = addr.get('city') or addr.get('town') or addr.get('village') or city
        country_code = addr.get('country_code', '').upper()
    except Exception as err:
        logger.error(f"Geopy error: {err}")
        await message.answer(
            "Не удалось определить город по координатам. Попробуйте позже.",
            parse_mode=None,
            reply_markup=get_main_menu_keyboard()
        )
        return

    # 2) astral lookup city
    try:
        astral_loc = astral_geo(city, astral_database())
        if astral_loc:
            tz_str = astral_loc.timezone
    except Exception as err:
        logger.debug(f"Astral lookup by city failed: {err}")

    # 3) astral lookup country if needed
    if tz_str == DEFAULT_TIMEZONE and country_code:
        try:
            astral_loc_c = astral_geo(country_code, astral_database())
            if astral_loc_c:
                tz_str = astral_loc_c.timezone
        except Exception as err:
            logger.debug(f"Astral lookup by country failed: {err}")

    # save to DB and confirm
    await update_user_location(user_id, lat, lon, city, tz_str)
    confirmation = (
        f"📍 Локация сохранена: {escape_md(city)}\n"
        f"Часовой пояс: {escape_md(tz_str)}\n"
        "Спасибо! 🙏"
    )
    await message.answer(
        confirmation,
        parse_mode=None,
        reply_markup=get_main_menu_keyboard()
    )
