# handlers/plan.py
"""
/plan command and activity logging handlers
Ежедневный план вынесен в сущность Day с ритуалами и статусом
"""
import logging
from datetime import date
from dataclasses import dataclass, field
from typing import List
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db import (
    get_user_data,
    get_daily_activity_status,
    log_daily_activity
)
from utils import escape_md, get_sun_times
from data import (
    DEFAULT_PHASE,

    CATEGORY_EMOJI_MAP
)

# Названия для кнопок (рус.)
CATEGORY_NAMES_MAP = {
    "morning_ritual": "Мантра Восхода",
    "water_prayer": "Молитва перед водой",
    "meal_prayer": "Молитва перед завтраком, обедом и ужином",
    "evening_ritual": "Мантра Заката",
    "monthly_fast": "Ежемесячный пост"
}


logger = logging.getLogger(__name__)

# Категории ритуалов для логирования
ACTIVITY_CATEGORIES = [
    "morning_ritual", 
    "water_prayer", 
    "meal_prayer", 
    "evening_ritual", 
    "monthly_fast"
]

# Тексты ритуалов
RITUAL_TEXT = {
    "morning_ritual": "Мантра Восхода: \"Рухс хуры, рухс зæрдæ\"",
    "water_prayer": "Молитва перед водой: \"Дон – фарн\"",
    "meal_prayer": "Молитва перед завтраком, обедом и ужином: \"Зæххы фарнæй цæр\"",
    "evening_ritual": "Мантра заката: \"Ныхасæй баст, Фарнæй дзаг\"",
    "monthly_fast": "Ежемесячный пост: 24 ч только вода + молитвы"
}

@dataclass
class Ritual:
    code: str
    text: str
    emoji: str
    name: str
    done: bool = False

@dataclass
class DayPlan:
    date: date
    rituals: List[Ritual] = field(default_factory=list)

async def handle_plan(message: types.Message) -> None:
    """Handle /plan command: show daily plan with tasks and status."""
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)
    if not user_data:
        await message.answer(
            escape_md("Не нашёл ваши данные. Попробуйте /start."),
            parse_mode="MarkdownV2"
        )
        return

    # Получение времени рассвета/заката
    sun = get_sun_times(
        user_data["lat"], user_data["lon"], user_data["tz"], user_data["city"]
    )
    sunrise = sun.get("sunrise").strftime("%H:%M") if sun.get("sunrise") else "н\/д"
    sunset = sun.get("sunset").strftime("%H:%M") if sun.get("sunset") else "н\/д"

    # Статус выполнения ритуалов
    status = await get_daily_activity_status(user_id)

    # Собираем DayPlan
    today_plan = DayPlan(date=date.today())
    for code in ACTIVITY_CATEGORIES:
        emoji = {
        "morning_ritual": "🌄",
        "water_prayer": "💧",
        "meal_prayer": "🍽",
        "evening_ritual": "🌙",
        "monthly_fast": "⏳"
    }.get(code, "🔸")
        name = CATEGORY_NAMES_MAP.get(code, code)
        done = bool(status.get(code, False))
        text = RITUAL_TEXT.get(code, name)
        today_plan.rituals.append(Ritual(code, text, emoji, name, done))

    # Данные для заголовка
    date_str = escape_md(today_plan.date.strftime('%d.%m.%Y'))
    city = escape_md(user_data.get('city', ''))
    leader = escape_md(user_data.get('leader_name', ''))

    # Формируем сообщение
    plan_lines = []
    plan_lines.append(f"🗓️ *План на {date_str}* — {city}")
    plan_lines.append(f"🌅 Восход: `{sunrise}` \\| Закат: `{sunset}`")
    plan_lines.append("")
    for r in today_plan.rituals:
        # ежемесячный пост выводим только в первый день месяца
        if r.code == 'monthly_fast' and today_plan.date.day != 1:
            continue
        status_emoji = "🟢" if r.done else "⚪️"
        plan_lines.append(f"{r.emoji} {status_emoji} {escape_md(r.text)}")
    plan_text = "\n".join(plan_lines)

    # Кнопки для логирования
    buttons = [
        InlineKeyboardButton(
            text=f"{r.emoji} {r.name}",
            callback_data=f"log_activity:{r.code}"
        ) for r in today_plan.rituals if not (r.code == 'monthly_fast' and today_plan.date.day != 1)
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=[buttons])

    await message.answer(
        plan_text,
        reply_markup=markup,
        parse_mode="MarkdownV2"
    )

async def handle_log_activity(callback_query: types.CallbackQuery) -> None:
    """Handle activity logging from inline buttons."""
    cat = callback_query.data.split(":", 1)[1]
    user_id = callback_query.from_user.id
    await log_daily_activity(user_id, cat)
    await callback_query.answer(f"✅ {CATEGORY_NAMES_MAP.get(cat, cat)} отмечено!")
    # После логирования перерисовываем план
    await callback_query.message.delete()
    await handle_plan(callback_query.message)
