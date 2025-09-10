# handlers/help.py
"""
/help command handler
"""
import logging
from aiogram import types
from aiogram.filters import Command
from utils import escape_md
from keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)

async def cmd_help(message: types.Message) -> None:
    """Handle /help command."""
    logger.info(f"User {message.from_user.id} issued /help")
    help_text = escape_md(
    '''🌿 Как пользоваться ботом 'Ныхас-Фарн':

🗓️ План дня - Задачи и мантры на день, отметка прогресса.
✨ Мантра - Случайная мудрость Учения.
✍️ Дневник - Запись мыслей и благодарностей.
📍 Локация - Установка местоположения для восхода/заката.
📊 Статистика - Ваш прогресс и статистика сообщества.
❓ Помощь - Это сообщение.

/start - Перезапуск бота.'''
)
    await message.answer(help_text, reply_markup=get_main_menu_keyboard())