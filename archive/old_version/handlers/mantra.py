# handlers/mantra.py
"""
/mantra command handler and category selection
"""
import logging
from aiogram import types
from aiogram.filters import Command
from aiogram import F

from db import get_mantra_categories, get_random_mantra_by_category
from utils import escape_md
from handlers.start import get_main_menu_keyboard

logger = logging.getLogger(__name__)

async def handle_mantra(message: types.Message) -> None:
    """Entry point for /mantra command or button press."""
    # Show categories keyboard
    categories = await get_mantra_categories()
    if not categories:
        await message.answer("Категории мантр не найдены.")
        return

    keyboard = [[types.KeyboardButton(text=escape_md(cat))] for cat in categories]
    keyboard.append([types.KeyboardButton(text="❌ Главное меню")])

    kb = types.ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("🌿 Выберите категорию мантры:", reply_markup=kb)

async def handle_mantra_category(message: types.Message) -> None:
    """Handle selected mantra category or return to main menu."""
    text = message.text
    if text == "❌ Главное меню":
        await message.answer("Главное меню:", reply_markup=get_main_menu_keyboard())
        return

    categories = await get_mantra_categories()
    if text not in categories:
        return

    mantra = await get_random_mantra_by_category(text)
    if not mantra:
        await message.answer("Не удалось найти мантру в этой категории.")
        return

    resp = f"🌿 *{escape_md(mantra['category'])}*\n\n"
    resp += f"{escape_md(mantra['ossetian'])}\n"
    if mantra.get('russian'):
        resp += f"_{escape_md(mantra['russian'])}_"

    kb_back = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="❌ Главное меню")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(resp, reply_markup=kb_back, parse_mode="MarkdownV2")

# In your register_all_handlers, bind:
# dp.register_message_handler(handle_mantra, Command("mantra"))
# dp.register_message_handler(handle_mantra, F.text.in_(["✨ Мантра", "Мантры"]))
# dp.register_message_handler(handle_mantra_category)
