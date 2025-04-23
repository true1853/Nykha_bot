from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🗓️ План дня"), KeyboardButton(text="✨ Мантра")],
        [KeyboardButton(text="✍️ Дневник"), KeyboardButton(text="📍 Локация")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🌄 Чекпоинты")], 
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
