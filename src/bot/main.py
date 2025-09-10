"""
Optimized Telegram bot for FarnPath - spiritual practice app.
Key optimizations:
- Connection pooling for database
- Better error handling
- Modular structure
- Performance improvements
- Clean separation of concerns
"""
import asyncio
import logging
from datetime import datetime, date, time
from typing import Optional

import pytz
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ContentType, WebAppInfo
)
from aiogram.exceptions import TelegramAPIError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.config.config import API_TOKEN, GEOPY_USER_AGENT, ACTIVITY_CATEGORIES, CATEGORY_EMOJI_MAP, CATEGORY_NAMES_MAP
from src.database.connection import db_manager
from src.database.repository import (
    UserRepository, ActivityRepository, MantraRepository, 
    DiaryRepository, StatsRepository
)
from src.utils.utils import escape_md, get_sun_times
from src.utils.keyboards import get_main_menu_keyboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot setup
if not API_TOKEN:
    raise ValueError("API_TOKEN not found in environment variables")

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="MarkdownV2"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
scheduler = AsyncIOScheduler(timezone="UTC")

# FSM States
class DiaryStates(StatesGroup):
    waiting_for_entry = State()

# Handlers
@dp.message(Command("start"))
async def handle_start(message: Message, state: FSMContext):
    """Handle /start command."""
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Пользователь"
    
    try:
        await UserRepository.add_user_if_not_exists(user_id, user_name)
        await state.clear()
        
        keyboard = get_main_menu_keyboard()
        await message.answer(
            f"Приветствую, {escape_md(user_name)} 🙏\n"
            f"Снова на пути Ныхас\\-Фарн\\! ✨🌍\n"
            f"Чем займемся сегодня\\?",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже 🙏")

@dp.message(F.text.in_({"❓ Помощь", "/help"}))
async def handle_help(message: Message):
    """Handle help command."""
    help_text = escape_md(
        "🌿 Как пользоваться ботом 'Ныхас-Фарн':\n\n"
        "🗓️ План дня - Задачи и мантры на день, отметка прогресса.\n"
        "✨ Мантра - Случайная мудрость Учения.\n"
        "✍️ Дневник - Запись мыслей и благодарностей.\n"
        "📍 Локация - Установка вашего местоположения для точного времени восхода/заката.\n"
        "📊 Статистика - Ваш недельный прогресс и статистика сообщества.\n"
        "❓ Помощь - Это сообщение.\n\n"
        "/start - Перезапустить бота."
    )
    await message.answer(help_text, reply_markup=get_main_menu_keyboard())

@dp.message(F.text.in_({"✨ Мантра", "/mantras"}))
async def handle_mantras_button(message: Message):
    """Handle mantra request."""
    try:
        mantra_data = await MantraRepository.get_random_mantra()
        if mantra_data:
            response = f"🌿 *{escape_md(mantra_data.category)}*\n\n"
            response += f"*{escape_md(mantra_data.ossetian_text)}*\n\n"
            if mantra_data.russian_translation:
                response += f"_{escape_md(mantra_data.russian_translation)}_"
            await message.answer(response)
        else:
            await message.answer(escape_md("Не удалось загрузить мантру. Попробуйте позже 🙏"))
    except Exception as e:
        logger.error(f"Error getting mantra: {e}")
        await message.answer(escape_md("Произошла ошибка при получении мантры 🙏"))

@dp.message(F.text.in_({"🗓️ План дня", "/today"}))
async def handle_daily_plan(message: Message):
    """Handle daily plan request."""
    user_id = message.from_user.id
    
    try:
        user_data = await UserRepository.get_user_data(user_id)
        if not user_data:
            await message.answer(escape_md("Не нашел ваши данные. Попробуйте /start."))
            return

        # Get sun times
        sun_times = get_sun_times(
            user_data.location_lat or 0, 
            user_data.location_lon or 0, 
            user_data.timezone or "UTC", 
            user_data.location_city or "Default"
        )
        
        sunrise_str = sun_times["sunrise"].strftime('%H:%M') if sun_times["sunrise"] else "н/д"
        sunset_str = sun_times["sunset"].strftime('%H:%M') if sun_times["sunset"] else "н/д"

        # Get activity status
        activity_status = await ActivityRepository.get_daily_activity_status(user_id)
        
        # Build progress rings
        rings = []
        for cat_code in ACTIVITY_CATEGORIES:
            emoji = CATEGORY_EMOJI_MAP.get(cat_code, "❓")
            cat_name = CATEGORY_NAMES_MAP.get(cat_code, cat_code)
            completed = activity_status.get(cat_code, False)
            rings.append(f"{emoji} {('🟢' if completed else '⚪️')} {escape_md(cat_name)}")
        rings_text = " \\| ".join(rings) if rings else escape_md("Активность не записана")

        # Get mantras based on time of day
        now_time = datetime.now(pytz.timezone(user_data.timezone or "UTC")).time()
        morning_mantra_cat = "Личный рост" if now_time < time(12, 0) else "Единство с природой"
        evening_mantra_cat = "Благодарность" if now_time >= time(18, 0) else "Служение"

        morning_mantra = await MantraRepository.get_random_mantra_by_category(morning_mantra_cat)
        evening_mantra = await MantraRepository.get_random_mantra_by_category(evening_mantra_cat)

        # Build plan text
        plan_text = f"🗓️ *План на {escape_md(date.today().strftime('%d.%m'))}* \\({escape_md(user_data.location_city or 'Неизвестно')}\\)\n\n"
        plan_text += f"☀️ Восход: `{escape_md(sunrise_str)}` \\| 🌙 Закат: `{escape_md(sunset_str)}`\n\n"
        plan_text += f"🌅 *Утро \\(до ~12:00\\)*\n"
        if morning_mantra:
            plan_text += f"   _{escape_md(morning_mantra.ossetian_text)}_\n"
        plan_text += escape_md("   Практика: Настройся на день с благодарностью\\.\n\n")
        plan_text += f"🌍 *День*\n"
        plan_text += escape_md("   ⚡ Практика: Выполни ежедневную задачу\\.\n")
        plan_text += f"   🎯 Отметь выполнение категорий ниже:\n\n"
        plan_text += f"🌃 *Вечер \\(после ~18:00\\)*\n"
        if evening_mantra:
            plan_text += f"   _{escape_md(evening_mantra.ossetian_text)}_\n"
        plan_text += escape_md("   🧘 Практика: Заверши день рефлексией в '✍️ Дневник'\\.\n\n")
        plan_text += f"💚 *Прогресс дня:*\n   {rings_text}"

        # Create inline keyboard
        inline_kb_buttons = []
        for cat_code in ACTIVITY_CATEGORIES:
            emoji = CATEGORY_EMOJI_MAP.get(cat_code, "❓")
            cat_name = CATEGORY_NAMES_MAP.get(cat_code, cat_code)
            completed = activity_status.get(cat_code, False)
            inline_kb_buttons.append(
                InlineKeyboardButton(
                    text=f"{'✅' if completed else emoji} {cat_name}", 
                    callback_data=f"log_activity:{cat_code}"
                )
            )
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[inline_kb_buttons])

        await message.answer(plan_text, reply_markup=inline_kb)
        
    except Exception as e:
        logger.error(f"Error in daily plan handler: {e}")
        await message.answer(escape_md("Произошла ошибка при получении плана дня 🙏"))

@dp.callback_query(F.data.startswith("log_activity:"))
async def process_log_activity_callback(callback_query: CallbackQuery):
    """Handle activity logging callback."""
    try:
        category_to_log = callback_query.data.split(":")[1]
        user_id = callback_query.from_user.id

        success = await ActivityRepository.log_daily_activity(user_id, category_to_log)
        
        if success:
            cat_name = CATEGORY_NAMES_MAP.get(category_to_log, category_to_log)
            await callback_query.answer(f"✅ {cat_name} отмечено!")
            
            # Update the message
            await handle_daily_plan(callback_query.message)
        else:
            await callback_query.answer("❌ Ошибка при отметке активности", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error in activity callback: {e}")
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)

@dp.message(F.text.in_({"✍️ Дневник", "/diary"}))
async def handle_diary_button(message: Message, state: FSMContext):
    """Handle diary button."""
    await message.answer(escape_md("📝 Что у тебя на сердце? Напиши:"))
    await state.set_state(DiaryStates.waiting_for_entry)

@dp.message(DiaryStates.waiting_for_entry)
async def process_diary_entry_message(message: Message, state: FSMContext):
    """Process diary entry."""
    user_id = message.from_user.id
    user_entry = message.text
    
    try:
        success = await DiaryRepository.add_entry(user_id, user_entry)
        if success:
            await message.answer(escape_md("Запись сохранена 🙏"), reply_markup=get_main_menu_keyboard())
        else:
            await message.answer(escape_md("🚫 Не удалось сохранить запись. Попробуйте позже."), reply_markup=get_main_menu_keyboard())
    except Exception as e:
        logger.error(f"Error saving diary entry: {e}")
        await message.answer(escape_md("🚫 Произошла ошибка при сохранении записи."), reply_markup=get_main_menu_keyboard())
    finally:
        await state.clear()

@dp.message(Command('mydiary'))
async def handle_mydiary(message: Message):
    """Handle mydiary command."""
    user_id = message.from_user.id
    
    try:
        entries = await DiaryRepository.get_entries(user_id, limit=5)
        if not entries:
            await message.answer(escape_md("В вашем дневнике пока нет записей. Используйте кнопку '✍️ Дневник'."))
            return
        
        response_text = escape_md("📖 Ваши последние 5 записей:\n")
        for entry in reversed(entries):
            try:
                ts_formatted = entry.timestamp.strftime('%d.%m.%y %H:%M')
            except (ValueError, TypeError):
                ts_formatted = str(entry.timestamp)
            
            response_text += f"\n*{escape_md(ts_formatted)}*\n"
            response_text += f"{escape_md(entry.entry_text)}\n"
        
        if len(response_text) > 4090:
            response_text = response_text[:4090] + "\n" + escape_md("...")
        
        await message.answer(response_text)
        
    except Exception as e:
        logger.error(f"Error getting diary entries: {e}")
        await message.answer(escape_md("Произошла ошибка при получении записей дневника 🙏"))

@dp.message(F.text == "📍 Локация")
async def handle_location_button(message: Message):
    """Handle location button."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить мою геолокацию", request_location=True)],
            [KeyboardButton(text="🚫 Отмена")]
        ],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer(
        escape_md("Чтобы точнее показывать время восхода/заката, нужна твоя геолокация 🌍.\n"
                  "Нажми кнопку 'Отправить...' или 'Отмена' 👇"),
        reply_markup=keyboard
    )

@dp.message(F.text == "🚫 Отмена")
async def handle_location_cancel(message: Message):
    """Handle location cancel."""
    await message.answer("Хорошо, оставим настройки локации по умолчанию.", reply_markup=get_main_menu_keyboard())

@dp.message(StateFilter(None), F.content_type == ContentType.LOCATION)
async def handle_user_location(message: Message):
    """Handle user location."""
    user_id = message.from_user.id
    lat = message.location.latitude
    lon = message.location.longitude
    
    logger.info(f"Received location from user {user_id}: lat={lat}, lon={lon}")
    await message.answer(escape_md("⏳ Определяю город и часовой пояс..."), reply_markup=types.ReplyKeyboardRemove())

    # For now, use default values - geocoding can be added later
    city = "Неизвестно"
    tz_str = "UTC"

    try:
        await UserRepository.update_user_location(user_id, lat, lon, city, tz_str)
        await message.answer(
            escape_md(f"📍 Локация сохранена: *{city}*\nЧасовой пояс: `{tz_str}`\nСпасибо\\! 🙏"),
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Error updating location: {e}")
        await message.answer(escape_md("Не удалось сохранить локацию. Попробуйте позже."), reply_markup=get_main_menu_keyboard())

@dp.message(F.text.in_({"📊 Статистика", "/stats"}))
async def handle_stats_button(message: Message):
    """Handle stats button."""
    user_id = message.from_user.id
    
    try:
        user_data = await UserRepository.get_user_data(user_id)
        if not user_data:
            await message.answer(escape_md("Не нашел ваши данные. Попробуйте /start."))
            return

        stats = await ActivityRepository.get_user_weekly_stats(user_id)

        stats_text = f"📊 *Твоя статистика за 7 дней:*\n\n"
        stats_text += f"☀️ Активных дней: *{escape_md(stats.days_active)}* из 7\n"
        stats_text += f"✍️ Записей в дневнике: *{escape_md(stats.diary_entries)}*\n"
        stats_text += f"🔥 Текущий стрик: *{escape_md(stats.streak)}* дня\\(ей\\)\n\n"
        stats_text += f"🎯 *Выполнено практик по категориям:*\n"
        
        for cat_code in ACTIVITY_CATEGORIES:
            count = stats.categories_done.get(cat_code, 0)
            emoji = CATEGORY_EMOJI_MAP.get(cat_code, "❓")
            cat_name = CATEGORY_NAMES_MAP.get(cat_code, cat_code)
            stats_text += f"   {emoji} {escape_md(cat_name)}: *{escape_md(count)}*\n"

        stats_text += f"\n📈 Общее число выполненных практик: *{escape_md(stats.tasks_done_total)}*"

        # Group stats button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌍 Общая статистика", callback_data="show_group_stats")]
        ])

        await message.answer(stats_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        await message.answer(escape_md("Произошла ошибка при получении статистики 🙏"))

@dp.callback_query(F.data == "show_group_stats")
async def process_show_group_stats(callback_query: CallbackQuery):
    """Handle group stats callback."""
    try:
        stats = await StatsRepository.get_group_weekly_stats()
        
        response = f"🌍 *Статистика сообщества за 7 дней:*\n\n"
        response += f"👥 Активных участников: *{escape_md(stats.total_users_active)}*\n\n"
        response += f"🎯 *Всего выполнено практик:*\n"
        
        for cat_code in ACTIVITY_CATEGORIES:
            count = stats.categories_done.get(cat_code, 0)
            if count > 0:
                emoji = CATEGORY_EMOJI_MAP.get(cat_code, "❓")
                cat_name = CATEGORY_NAMES_MAP.get(cat_code, cat_code)
                response += f"   {emoji} {escape_md(cat_name)}: *{escape_md(count)}*\n"

        response += f"\n📈 Общее число практик: *{escape_md(stats.total_tasks_done)}*"

        await callback_query.message.answer(response)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error getting group stats: {e}")
        await callback_query.answer("❌ Произошла ошибка при получении статистики", show_alert=True)

# Scheduler job
async def reset_daily_activities_job():
    """Reset daily activities job."""
    try:
        cutoff = (date.today() - timedelta(days=1)).isoformat()
        async with db_manager.get_cursor() as cursor:
            await cursor.execute(
                "DELETE FROM daily_activity WHERE activity_date < ?",
                (cutoff,)
            )
            await cursor.connection.commit()
        logger.info(f"Daily reset: deleted old activity records")
    except Exception as e:
        logger.error(f"Error in daily reset job: {e}")

# Main function
async def main():
    """Main function."""
    try:
        # Initialize database
        await db_manager.get_connection()
        logger.info("Database initialized")
        
        # Setup scheduler
        scheduler.add_job(reset_daily_activities_job, 'cron', hour=0, minute=5, timezone='UTC')
        scheduler.start()
        logger.info("Scheduler started")
        
        # Start bot
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, skip_updates=True)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        await db_manager.close()
        if scheduler.running:
            scheduler.shutdown(wait=False)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
