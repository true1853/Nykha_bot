# handlers/start.py
"""
/start command handler
"""
import logging
from aiogram import types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from html import escape

from db import add_user_if_not_exists
from keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)

async def cmd_start(
    message: types.Message,
    state: FSMContext
) -> None:
    """Handle /start command."""
    user_id = message.from_user.id
    user_name = escape(message.from_user.first_name or "друг")
    logger.info(f"User {user_id} issued /start, name={user_name}")

    # Register user and reset state
    await add_user_if_not_exists(user_id, user_name)
    await state.clear()

    # Prepare greeting and keyboard
    keyboard = get_main_menu_keyboard()
    greeting = f"""👋 Привет, <b>{user_name}</b>!\n\n"""
    greeting += (
        "Добро пожаловать в бот «Ныхас-Фарн» —\n"
        "твой помощник по ежедневным практикам:\n\n"
        "🌅 <b>Утренний ритуал</b>: мантры и настройка на день\n"
        "🏃 <b>Природный фитнес</b>: движение в гармонии с природой\n"
        "🌍 <b>Дневные практики</b>: осознанность, связь с природой, служение\n"
        "🌙 <b>Вечерний ритуал</b>: благодарность и рефлексия\n\n"
        "🚀 <i>Готов начать? Выбери одну из кнопок ниже.</i>"
    )

    # Remove old keyboard (e.g., stale buttons like "Девиз")
    await message.answer(
        "Обновляю меню…",
        reply_markup=ReplyKeyboardRemove()
    )

    # Send greeting with new main menu keyboard
    await message.answer(
        greeting,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
