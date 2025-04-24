# handlers/checkpoints.py
"""
Handlers for 🌄 Встреча восхода и заката: меню «Сегодня/Завтра/Мантры»
"""
import logging
from datetime import date, timedelta
from aiogram import types, F, Dispatcher
from aiogram.filters.command import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import get_user_data
from utils import escape_md, get_sun_times

logger = logging.getLogger(__name__)

# Список мантр для чекпоинтов
CHECKPOINT_MANTRAS = [
    "Стыр Хуыцау, Табу Дæхицæн!",
    "Стыр Хуыцау, хъару нын ратт!",
    "Стыр Хуыцау, абоны хорзæх!",
    "Стыр Хуыцау, нæхи цæрæнбон!",
    "Стыр Хуыцау, нæ зæххы фарн!",
    "Стыр Хуыцау, стыр бæркад!",
    "Стыр Хуыцау, раст фæндаг!",
]

async def send_checkpoints_menu(message: types.Message) -> None:
    """Show inline menu: Сегодня, Завтра, Мантры"""
    user_data = await get_user_data(message.from_user.id)
    if not user_data:
        await message.answer("Не найдены ваши данные. Используйте /start.")
        return

    text = "🌄 *Встреча восхода и заката*"
    buttons = [
        InlineKeyboardButton(text="Сегодня", callback_data="checkpoints:today"),
        InlineKeyboardButton(text="Завтра",  callback_data="checkpoints:tomorrow"),
        InlineKeyboardButton(text="Мантры", callback_data="checkpoints:mantras"),
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await message.answer(text, reply_markup=markup, parse_mode="MarkdownV2")

async def process_checkpoints_choice(callback_query: types.CallbackQuery) -> None:
    """Handle selection and display sun times or mantras"""
    await callback_query.answer()
    user_data = await get_user_data(callback_query.from_user.id)
    if not user_data:
        await callback_query.message.answer("Нет данных пользователя. Используйте /start.")
        return

    lat, lon, tz, city = user_data['lat'], user_data['lon'], user_data['tz'], user_data['city']
    choice = callback_query.data.split(':', 1)[1]
    target_date = date.today() + (timedelta(days=1) if choice == 'tomorrow' else timedelta(days=0))

    # Получаем времена для конкретной даты
    sun = get_sun_times(lat, lon, tz, city, target_date=target_date)
    sunrise = sun['sunrise'].strftime('%H:%M:%S') if sun['sunrise'] else 'н/д'
    sunset  = sun['sunset'].strftime('%H:%M:%S') if sun['sunset'] else 'н/д'

    if choice in ('today', 'tomorrow'):
        label = 'Сегодня' if choice == 'today' else 'Завтра'
        header = f"*{escape_md(city)}, {escape_md(target_date.strftime('%d.%m.%Y'))}*"
        body = (
            f"☀️ {label} восход: `{escape_md(sunrise)}`\n"
            f"🌙 {label} закат: `{escape_md(sunset)}`"
        )
        text = header + "\n\n" + body
        try:
            await callback_query.message.edit_text(text, parse_mode="MarkdownV2")
        except:
            await callback_query.message.answer(text, parse_mode="MarkdownV2")
    else:
        # Мантры
        text = "*Мантры для встречи восхода и проводов заката:*\n\n"
        for mantra in CHECKPOINT_MANTRAS:
            text += f"• _{escape_md(mantra)}_\n"
        try:
            await callback_query.message.edit_text(text, parse_mode="MarkdownV2")
        except:
            await callback_query.message.answer(text, parse_mode="MarkdownV2")

def register_checkpoints(dp: Dispatcher) -> None:
    """Register message and callback handlers for checkpoints"""
    dp.message.register(send_checkpoints_menu, Command('checkpoints'))
    dp.message.register(send_checkpoints_menu, F.text == '🌄 Чекпоинты')
    dp.callback_query.register(process_checkpoints_choice, F.data.startswith('checkpoints:'))