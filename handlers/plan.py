# handlers/plan.py
"""
/plan command and activity logging handlers
"""
import logging
from datetime import date
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
    TASKS,
    ACTIVITY_CATEGORIES,
    CATEGORY_EMOJI_MAP,
    CATEGORY_NAMES_MAP
)

logger = logging.getLogger(__name__)

HABIT_CATEGORY_MAP = {
    "daily_habit": "mindfulness",
    "meal_habit": "nature",
    "communication_habit": "service",
}

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

    sun = get_sun_times(
        user_data["lat"], user_data["lon"], user_data["tz"], user_data["city"]
    )
    sunrise = sun.get("sunrise").strftime("%H:%M:%S") if sun.get("sunrise") else "н/д"
    sunset = sun.get("sunset").strftime("%H:%M:%S") if sun.get("sunset") else "н/д"

    status = await get_daily_activity_status(user_id)
    rings = []
    for c in ACTIVITY_CATEGORIES:
        emoji = CATEGORY_EMOJI_MAP[c]
        name = CATEGORY_NAMES_MAP[c]
        done = "🟢" if status.get(c) else "⚪️"
        rings.append(f"{emoji} {done} {escape_md(name)}")
    rings_text = " \\| ".join(rings)

    phase = user_data.get("current_phase", DEFAULT_PHASE)
    main_task = TASKS.get(phase, {}).get("daily_habit", "Практика дня")
    main_cat = HABIT_CATEGORY_MAP.get("daily_habit", "mindfulness")
    main_emoji = CATEGORY_EMOJI_MAP[main_cat]
    main_name = CATEGORY_NAMES_MAP[main_cat]

    # Экранируем скобки \( и \) в MarkdownV2
    plan_text = f"""🗓️ *План на {escape_md(date.today().strftime('%d.%m.%Y'))}* \\({escape_md(user_data['city'])}\\)

🌅 *Утренний ритуал*:
   – Мантра: "{escape_md(main_task)}"
🔔 Время рассвета: `{escape_md(sunrise)}`

🏃 *Природный фитнес*

🌍 *Дневная практика*: {main_emoji} {escape_md(main_name)}

🔔 Время заката: `{escape_md(sunset)}`

💚 *Прогресс дня:* {escape_md(rings_text)}
"""

    buttons = [
        InlineKeyboardButton(
            text=f"{'✅' if status.get(c) else CATEGORY_EMOJI_MAP[c]} {CATEGORY_NAMES_MAP[c]}",
            callback_data=f"log_activity:{c}"
        )
        for c in ACTIVITY_CATEGORIES
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
    await callback_query.answer(f"✅ {CATEGORY_NAMES_MAP[cat]} отмечено!")
    await callback_query.message.delete()
    await handle_plan(callback_query.message)
