# handlers/diary.py
"""
/diary command and diary entries handling
"""
import logging
from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove

from db import add_diary_entry, get_last_diary_entries
from utils import escape_md
from keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)

class DiaryStates(StatesGroup):
    waiting_for_entry = State()

async def open_diary(message: types.Message, state: FSMContext) -> None:
    """Prompt user to write diary entry."""
    logger.info(f"User {message.from_user.id} opened diary entry prompt")
    await message.answer(
        escape_md("📝 Что у тебя на сердце? Напиши:"),
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(DiaryStates.waiting_for_entry)

async def process_diary_entry(message: types.Message, state: FSMContext) -> None:
    """Save diary entry and return to main menu."""
    text = message.text.strip()
    logger.info(f"User {message.from_user.id} diary entry: {text}")
    if text:
        await add_diary_entry(message.from_user.id, text)
        await message.answer(
            escape_md("Запись сохранена 🙏"),
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer(
            escape_md("Пустая запись не сохранена."),
            reply_markup=get_main_menu_keyboard()
        )
    await state.clear()

async def cmd_mydiary(message: types.Message) -> None:
    """Show last 5 diary entries."""
    logger.info(f"User {message.from_user.id} requested diary history")
    entries = await get_last_diary_entries(message.from_user.id, limit=5)
    if not entries:
        await message.answer(
            escape_md("В вашем дневнике пока нет записей. Используйте кнопку '✍️ Дневник'."),
            reply_markup=get_main_menu_keyboard()
        )
        return

    header = escape_md("📖 Ваши последние 5 записей:") + "\n"
    body = ""
    for e in reversed(entries):
        ts = str(e["timestamp"]).split(".", 1)[0]
        body += f"\n*{escape_md(ts)}*\n{escape_md(e['text'])}\n"

    await message.answer(
        header + body,
        parse_mode="MarkdownV2",
        reply_markup=get_main_menu_keyboard()
    )

# handlers/location.py and others remain unchanged