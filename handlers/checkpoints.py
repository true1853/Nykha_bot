# handlers/checkpoints.py
"""
Handlers for 🌄 Чекпоинты button: send list of sunrise/sunset mantras
"""
import logging
from aiogram import types, F
from aiogram.types import Message
from utils import escape_md

logger = logging.getLogger(__name__)

# List of checkpoint mantras
CHECKPOINT_MANTRAS = [
    "Стыр Хуыцау, Табу Дæхицæн\\!",
    "Стыр Хуыцау, хъару нын ратт\\!",
    "Стыр Хуыцау, абоны хорзæх\\!",
    "Стыр Хуыцау, нæхи цæрæнбон\\!",
    "Стыр Хуыцау, нæ зæххы фарн\\!",
    "Стыр Хуыцау, стыр бæркад\\!",
    "Стыр Хуыцау, раст фæндаг\\!"
]

async def send_checkpoints(message: types.Message) -> None:
    """Send sunrise/sunset mantras list."""
    logger.info(f"User {message.from_user.id} requested checkpoints")
    text = "*Мантры для встречи восхода и проводов заката:* \n\n"
    for idx, mantra in enumerate(CHECKPOINT_MANTRAS, start=1):
        text += f"{idx}\\) {escape_md(mantra)}\n"
    await message.answer(text, parse_mode="MarkdownV2")
