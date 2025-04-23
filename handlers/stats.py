# handlers/stats.py
"""
/stats command and community stats handling
"""
import logging
from aiogram import F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from db import (
    get_user_data,
    get_user_weekly_stats_detailed,
    get_group_weekly_stats_categorized
)
from utils import escape_md
from data import (
    ACTIVITY_CATEGORIES,
    CATEGORY_EMOJI_MAP,
    CATEGORY_NAMES_MAP,
)

logger = logging.getLogger(__name__)

async def handle_stats_button(message: types.Message) -> None:
    """Handle /stats command and 📊 Статистика button."""
    user_id = message.from_user.id
    logger.info(f"handle_stats_button invoked by user {user_id}")
    user_data = await get_user_data(user_id)
    stats = await get_user_weekly_stats_detailed(user_id)
    logger.debug(f"user_data={user_data}, stats_detailed={stats}")

    if not user_data:
        await message.answer(
            escape_md("Не нашел ваши данные. Попробуйте /start."),
            parse_mode="MarkdownV2"
        )
        return

    streak = user_data.get('streak', 0)

    # build text, escape parentheses in literal
    stats_text = (
        f"📊 *Твоя статистика за 7 дней:*\n\n"
        f"☀️ Активных дней: *{escape_md(stats['days_active'])}* из 7\n"
        f"✍️ Записей в дневнике: *{escape_md(stats['diary_entries'])}*\n"
        f"🔥 Текущий стрик: *{escape_md(streak)}* дня\(ей\)\n\n"
        "🎯 *Выполнено практик по категориям:*\n"
    )
    for cat in ACTIVITY_CATEGORIES:
        cnt = stats['categories_done'].get(cat, 0)
        emoji = CATEGORY_EMOJI_MAP.get(cat, "❓")
        name = CATEGORY_NAMES_MAP.get(cat, cat)
        stats_text += f"   {emoji} {escape_md(name)}: *{escape_md(cnt)}*\n"

    stats_text += f"\n📈 Общее число выполненных практик: *{escape_md(stats['tasks_done_total'])}*"
    logger.debug(f"stats_text={stats_text!r}")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Общая статистика", callback_data="show_group_stats")]
    ])

    await message.answer(
        stats_text,
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )

async def process_show_group_stats(callback_query: CallbackQuery) -> None:
    """Handle community stats callback."""
    user_id = callback_query.from_user.id
    logger.info(f"process_show_group_stats invoked by user {user_id}")
    stats = await get_group_weekly_stats_categorized()
    logger.debug(f"group_stats={stats}")

    response = (
        f"🌍 *Статистика сообщества за 7 дней:*\n\n"
        f"👥 Активных участников: *{escape_md(stats['total_users_active'])}*\n\n"
        "🎯 *Всего выполнено практик:*\n"
    )
    for cat in ACTIVITY_CATEGORIES:
        cnt = stats['categories_done'].get(cat, 0)
        if cnt > 0:
            emoji = CATEGORY_EMOJI_MAP.get(cat, "❓")
            name = CATEGORY_NAMES_MAP.get(cat, cat)
            response += f"   {emoji} {escape_md(name)}: *{escape_md(cnt)}*\n"

    response += f"\n📈 Общее число практик: *{escape_md(stats['total_tasks_done'])}*"
    logger.debug(f"group_response={response!r}")

    await callback_query.message.answer(response, parse_mode="MarkdownV2")
    await callback_query.answer()
