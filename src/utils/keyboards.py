"""
Keyboard utilities for FarnPathBot.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    buttons = [
        [KeyboardButton(text="🗓️ План дня"), KeyboardButton(text="✨ Мантра")],
        [KeyboardButton(text="✍️ Дневник Ныхас"), KeyboardButton(text="📍 Локация")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🌄 Встреча восхода и заката")], 
        [KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="🚀 Mini App", web_app=WebAppInfo(url="https://e0dfaa5fc43a.ngrok-free.app"))]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
