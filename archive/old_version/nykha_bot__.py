import logging
import random
import asyncio
import os
import aiosqlite
from datetime import datetime, date, time, timedelta
from dotenv import load_dotenv
from typing import Union, List, Dict, Optional
import pytz # Для работы с часовыми поясами
from astral.location import Location # Исправленный импорт astral
from astral.sun import sun
from geopy.geocoders import Nominatim # Для определения локации по координатам
from geopy.extra.rate_limiter import RateLimiter # Для ограничения запросов к Nominatim
from apscheduler.schedulers.asyncio import AsyncIOScheduler # Для сброса статуса

# Импортируем настройки
from config import (
    API_TOKEN, DATABASE_FILE as DB_NAME, DEFAULT_CITY_NAME,
    DEFAULT_LATITUDE, DEFAULT_LONGITUDE, DEFAULT_TIMEZONE, GEOPY_USER_AGENT
)

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command, StateFilter # Добавляем StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ContentType, WebAppInfo # Добавляем ContentType и WebAppInfo
)
from aiogram.exceptions import TelegramAPIError

# --- Конфигурация ---
load_dotenv()

if not API_TOKEN:
    raise ValueError("Не найден токен бота.")
if not GEOPY_USER_AGENT:
     logger.warning("GEOPY_USER_AGENT не задан в config.py, возможны проблемы с геокодингом.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="MarkdownV2"))

# Инициализация геокодеров и планировщика
try:
    logger.info("Astral Geocoder initialized.")
except Exception as e:
    logger.error(f"Failed to initialize Astral Geocoder: {e}. Timezone detection might fail.")
    astral_geo = None

geolocator = Nominatim(user_agent=GEOPY_USER_AGENT)
# Ограничение: 1 запрос в 1.1 секунды к Nominatim
geocode = RateLimiter(geolocator.reverse, min_delay_seconds=1.1, error_wait_seconds=5.0)

scheduler = AsyncIOScheduler(timezone="UTC") # Используем UTC для планировщика

# --- Утилиты ---
def escape_md(text):
    """Экранирует символы MarkdownV2."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    temp_text = str(text)
    # Экранируем только если символ не предшествует '\'
    escaped_text = ""
    prev_char_is_escape = False
    for char in temp_text:
        if char in escape_chars and not prev_char_is_escape:
            escaped_text += f'\\{char}'
        else:
            escaped_text += char
        prev_char_is_escape = char == '\\'
    return escaped_text

# --- Данные Учения ---
# (PRINCIPLES, TASKS, DEFAULT_PHASE - остаются)
# Убедитесь, что MANTRAS_DATA ЗАПОЛНЕНА всеми манатрами!
PRINCIPLES = [ escape_md(p) for p in [
    "1. «Зӕххы фарнӕй цӕр» (Живи благодатью Земли)",
    "2. «Ныхасӕй иугонд» (Един через коллективный разум)",
    "15. «Фӕстаг фыст - ног фыстӕн йӕ райдиан» (Последняя запись - начало новой)"
]]
TASKS = { k: {ik: escape_md(iv) for ik, iv in v.items()} for k, v in {
    "phase1_week1": { "title": "Фаза 1, Неделя 1: Наблюдение и Благодарность", "daily_habit": "1-2 мин осознанно наблюдайте природный элемент.", "meal_habit": "Перед 1 приемом пищи скажите мантру: «Зӕхх, дӕ фарнӕй цӕрын».", "reflection": "Вечером запишите 1 наблюдение." },
    "phase1_week2": { "title": "Фаза 1, Неделя 2: Вода и Слова", "daily_habit": "Будьте внимательны к использованию воды (Принцип 5).", "communication_habit": "Практикуйте паузу и правдивость в 1 разговоре (Принцип 13).", "reflection": "Запишите моменты осознанности." }
}.items()}
DEFAULT_PHASE = "phase1_week1"
ACTIVITY_CATEGORIES = ["mindfulness", "nature", "service"]
CATEGORY_EMOJI_MAP = {"mindfulness": "🧘", "nature": "🌳", "service": "🤝"}
CATEGORY_NAMES_MAP = {"mindfulness": "Осознанность", "nature": "Природа", "service": "Служение"}
MANTRAS_DATA = [ # СОКРАЩЕННЫЙ ПРИМЕР - ЗАПОЛНИТЕ ПОЛНОСТЬЮ!
        ("Единство с природой", "«Зӕхх - нӕ зӕрдӕ»", "Земля - наше сердце"),
        ("Единство с природой", "«Дон - фарн»", "Вода - благодать"),
        ("Коллективное сознание", "«Мах - иу зӕрдӕ»", "Мы - одно сердце"),
        # ... ДОБАВЬТЕ ВСЕ МАНТРЫ ЗДЕСЬ ...
]

# --- База Данных (SQLite) ---
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f'''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                current_phase TEXT NOT NULL DEFAULT '{DEFAULT_PHASE}',
                first_name TEXT,
                streak INTEGER DEFAULT 0,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                location_city TEXT DEFAULT '{DEFAULT_CITY_NAME}',
                location_lat REAL DEFAULT {DEFAULT_LATITUDE},
                location_lon REAL DEFAULT {DEFAULT_LONGITUDE},
                timezone TEXT DEFAULT '{DEFAULT_TIMEZONE}'
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS diary_entries (
                entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                entry_text TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS mantras (
                mantra_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                ossetian_text TEXT NOT NULL UNIQUE,
                russian_translation TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS daily_activity (
                activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_date DATE DEFAULT CURRENT_DATE, -- SQLite хранит DATE как TEXT
                category TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, activity_date, category)
            )
        ''')
        await db.commit()
    logger.info("Database initialized.")

async def populate_mantras_if_empty():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM mantras")
        count_result = await cursor.fetchone()
        if count_result and count_result[0] == 0:
            logger.info("Populating mantras table...")
            try:
                await db.executemany(
                    "INSERT OR IGNORE INTO mantras (category, ossetian_text, russian_translation) VALUES (?, ?, ?)",
                    MANTRAS_DATA
                )
                await db.commit()
                inserted_cursor = await db.execute("SELECT COUNT(*) FROM mantras") # Проверяем сколько вставилось
                inserted_count = await inserted_cursor.fetchone()
                logger.info(f"Populated mantras table with {inserted_count[0] if inserted_count else 0} entries (expected: {len(MANTRAS_DATA)}).")
            except aiosqlite.Error as e:
                logger.error(f"Failed to populate mantras table: {e}")
        else:
            # logger.info("Mantras table already populated or count check failed.")
            pass # Не логируем, если уже заполнено

# --- Функции работы с БД (add_user, get_user, update_location, log_activity, get_activity, stats) ---
# (Код этих функций остается таким же, как в предыдущем ответе)
async def add_user_if_not_exists(user_id: int, first_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        user_exists = await cursor.fetchone()
        current_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Формат для SQLite
        if not user_exists:
            await db.execute(
                "INSERT INTO users (user_id, current_phase, first_name, location_city, location_lat, location_lon, timezone, last_login) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, DEFAULT_PHASE, first_name, DEFAULT_CITY_NAME, DEFAULT_LATITUDE, DEFAULT_LONGITUDE, DEFAULT_TIMEZONE, current_ts)
            )
            await db.commit()
            logger.info(f"Added new user {user_id} ({first_name}) with default phase {DEFAULT_PHASE}")
            return True
        else:
             await db.execute("UPDATE users SET first_name = ?, last_login = ? WHERE user_id = ?", (first_name, current_ts, user_id))
             await db.commit()
        return False

async def get_user_data(user_id: int) -> Optional[Dict]:
     async with aiosqlite.connect(DB_NAME) as db:
         cursor = await db.execute("SELECT current_phase, streak, first_name, location_city, location_lat, location_lon, timezone FROM users WHERE user_id = ?", (user_id,))
         row = await cursor.fetchone()
         if row:
             return {"current_phase": row[0], "streak": row[1], "first_name": row[2], "city": row[3], "lat": row[4], "lon": row[5], "tz": row[6]}
         return None

async def update_user_location(user_id: int, lat: float, lon: float, city: str, tz: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET location_lat = ?, location_lon = ?, location_city = ?, timezone = ? WHERE user_id = ?", (lat, lon, city, tz, user_id))
        await db.commit()
        logger.info(f"Updated location for user {user_id} to {city} ({lat},{lon}), tz: {tz}")

async def log_daily_activity(user_id: int, category: str):
    if category not in ACTIVITY_CATEGORIES: return
    today_str = date.today().isoformat() # Формат 'YYYY-MM-DD'
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR REPLACE INTO daily_activity (user_id, activity_date, category, completed, timestamp)
            VALUES (?, ?, ?, TRUE, CURRENT_TIMESTAMP)
        """, (user_id, today_str, category))
        await db.commit()
        logger.info(f"Logged activity '{category}' for user {user_id} for {today_str}.")

async def get_daily_activity_status(user_id: int) -> Dict[str, bool]:
    status = {cat: False for cat in ACTIVITY_CATEGORIES}
    today_str = date.today().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT category FROM daily_activity WHERE user_id = ? AND activity_date = ? AND completed = TRUE", (user_id, today_str))
        rows = await cursor.fetchall()
        for row in rows:
            if row[0] in status: status[row[0]] = True
    return status

async def get_user_weekly_stats_detailed(user_id: int) -> Dict:
    stats = {"days_active": 0, "tasks_done_total": 0, "diary_entries": 0, "categories_done": {cat: 0 for cat in ACTIVITY_CATEGORIES}}
    week_ago_str = (date.today() - timedelta(days=6)).isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(DISTINCT activity_date) FROM daily_activity WHERE user_id = ? AND activity_date >= ?", (user_id, week_ago_str))
        result = await cursor.fetchone(); stats["days_active"] = result[0] if result else 0
        cursor = await db.execute("SELECT COUNT(*) FROM diary_entries WHERE user_id = ? AND DATE(timestamp) >= ?", (user_id, week_ago_str))
        result = await cursor.fetchone(); stats["diary_entries"] = result[0] if result else 0
        cursor = await db.execute("SELECT category, COUNT(*) FROM daily_activity WHERE user_id = ? AND activity_date >= ? AND completed = TRUE GROUP BY category", (user_id, week_ago_str))
        rows = await cursor.fetchall()
        for row in rows:
            cat, count = row
            if cat in stats["categories_done"]:
                stats["categories_done"][cat] = count
                stats["tasks_done_total"] += count
    return stats

async def get_group_weekly_stats_categorized() -> Dict:
    stats = {"total_users_active": 0, "total_tasks_done": 0, "categories_done": {cat: 0 for cat in ACTIVITY_CATEGORIES}}
    week_ago_str = (date.today() - timedelta(days=6)).isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(DISTINCT user_id) FROM daily_activity WHERE activity_date >= ? AND completed = TRUE", (week_ago_str,))
        result = await cursor.fetchone(); stats["total_users_active"] = result[0] if result else 0
        cursor = await db.execute("SELECT category, COUNT(*) FROM daily_activity WHERE activity_date >= ? AND completed = TRUE GROUP BY category", (week_ago_str,))
        rows = await cursor.fetchall()
        for row in rows:
            cat, count = row
            if cat in stats["categories_done"]:
                stats["categories_done"][cat] = count
                stats["total_tasks_done"] += count
    return stats

async def get_random_mantra() -> Optional[Dict]:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT category, ossetian_text, russian_translation FROM mantras ORDER BY RANDOM() LIMIT 1")
        row = await cursor.fetchone()
        if row: return {"category": row[0], "ossetian": row[1], "russian": row[2]}
        return None

async def get_random_mantra_by_category(category: str) -> Optional[Dict]:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT ossetian_text, russian_translation FROM mantras WHERE category = ? ORDER BY RANDOM() LIMIT 1", (category,))
        row = await cursor.fetchone()
        if row: return {"category": category, "ossetian": row[0], "russian": row[1]}
        return await get_random_mantra()

async def add_diary_entry(user_id: int, text: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO diary_entries (user_id, entry_text) VALUES (?, ?)", (user_id, text))
        await db.commit()
        logger.info(f"Added diary entry for user {user_id}")

async def get_last_diary_entries(user_id: int, limit: int = 5) -> List[Dict]:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT timestamp, entry_text FROM diary_entries WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
        rows = await cursor.fetchall()
        return [{"timestamp": row[0], "text": row[1]} for row in rows]

async def increment_user_streak(user_id: int) -> int:
     # TODO: Добавить логику проверки last_task_done_date для сброса стрика
     async with aiosqlite.connect(DB_NAME) as db:
         today_str = date.today().isoformat()
         await db.execute("UPDATE users SET streak = streak + 1, last_task_done_date = ? WHERE user_id = ?", (today_str, user_id))
         await db.commit()
         cursor = await db.execute("SELECT streak FROM users WHERE user_id = ?", (user_id,))
         result = await cursor.fetchone()
         new_streak = result[0] if result else 0
         logger.info(f"Incremented streak for user {user_id} to {new_streak}")
         return new_streak


# --- Функция для сброса статусов ---
async def reset_daily_activities_job():
    """Удаляет вчерашние и более старые записи об активности."""
    # Используем DATE('now', 'localtime', '-1 day') для надежности при переходе через полночь
    one_day_ago_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("DELETE FROM daily_activity WHERE activity_date < ?", (one_day_ago_str,))
        deleted_rows = cursor.rowcount # Количество удаленных строк
        await db.commit()
        logger.info(f"Daily reset job: Deleted {deleted_rows} old activity entries.")


# --- Расчет восхода/заката ---
def get_sun_times(lat: float, lon: float, tz_str: str, city_name: str = "Default") -> Dict[str, Optional[datetime]]:
    try:
        loc = Location((city_name, "region", lat, lon, tz_str, 0))
        today_dt = datetime.now(pytz.timezone(tz_str)).date() # Берем дату с учетом таймзоны
        s = sun(loc.observer, date=today_dt, tzinfo=loc.tzinfo)
        # Возвращаем объекты datetime
        sunrise_dt = s["sunrise"]
        sunset_dt = s["sunset"]
        return {"sunrise": sunrise_dt, "sunset": sunset_dt}
    except Exception as e:
        logger.error(f"Error calculating sun times for {city_name} ({lat}, {lon}), tz={tz_str}: {e}")
        return {"sunrise": None, "sunset": None}

# --- Состояния FSM ---
class DiaryStates(StatesGroup):
    waiting_for_entry = State()

# --- Клавиатуры ---
def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🗓️ План дня"), KeyboardButton(text="✨ Мантра")],
        [KeyboardButton(text="✍️ Дневник"), KeyboardButton(text="📍 Локация")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="🚀 Mini App", web_app=WebAppInfo(url="https://e0dfaa5fc43a.ngrok-free.app"))]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=False)
    return keyboard

# --- Обработчики ---

@dp.message(CommandStart())
async def handle_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Пользователь"
    await add_user_if_not_exists(user_id, user_name)
    await state.clear()
    keyboard = get_main_menu_keyboard()
    await message.answer(
        f"Приветствую, {escape_md(user_name)} 🙏\n"
        f"Снова на пути Ныхас\\-Фарн\\! ✨🌍\n"
        f"Чем займемся сегодня\\?",
        reply_markup=keyboard
    )

@dp.message(F.text.in_({"❓ Помощь", "/help"})) # Объединяем текст и команду
async def handle_help(message: Message):
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
    mantra_data = await get_random_mantra()
    if mantra_data:
        response = f"🌿 *{escape_md(mantra_data['category'])}*\n\n"
        response += f"*{escape_md(mantra_data['ossetian'])}*\n\n"
        if mantra_data['russian']:
            response += f"_{escape_md(mantra_data['russian'])}_"
        await message.answer(response)
    else:
        await message.answer(escape_md("Не удалось загрузить мантру. Попробуйте позже 🙏"))

@dp.message(F.text.in_({"🗓️ План дня", "/today"}))
async def handle_daily_plan(message: Message):
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)
    if not user_data:
        await message.answer(escape_md("Не нашел ваши данные. Попробуйте /start."))
        return

    sun_times = get_sun_times(user_data["lat"], user_data["lon"], user_data["tz"], user_data["city"])
    sunrise_dt = sun_times.get("sunrise")
    sunset_dt = sun_times.get("sunset")
    sunrise_str = sunrise_dt.strftime('%H:%M') if sunrise_dt else "н/д"
    sunset_str = sunset_dt.strftime('%H:%M') if sunset_dt else "н/д"

    activity_status = await get_daily_activity_status(user_id)
    rings = []
    for cat_code in ACTIVITY_CATEGORIES:
        emoji = CATEGORY_EMOJI_MAP.get(cat_code, "❓")
        cat_name = CATEGORY_NAMES_MAP.get(cat_code, cat_code)
        completed = activity_status.get(cat_code, False)
        rings.append(f"{emoji} {('🟢' if completed else '⚪️')} {escape_md(cat_name)}")
    rings_text = " \\| ".join(rings) if rings else escape_md("Активность не записана")

    current_phase = user_data.get("current_phase", DEFAULT_PHASE)
    task_info = TASKS.get(current_phase)
    main_task_text = task_info.get('daily_habit', escape_md("Практика дня")) if task_info else escape_md("Практика дня")

    # Выбираем мантры по времени суток (пример)
    now_time = datetime.now(pytz.timezone(user_data["tz"])).time()
    morning_mantra_cat = "Личный рост" if now_time < time(12,0) else "Единство с природой"
    evening_mantra_cat = "Благодарность" if now_time >= time(18,0) else "Служение"

    morning_mantra_data = await get_random_mantra_by_category(morning_mantra_cat)
    evening_mantra_data = await get_random_mantra_by_category(evening_mantra_cat)

    plan_text = f"🗓️ *План на {escape_md(date.today().strftime('%d.%m'))}* \\({escape_md(user_data['city'])}\\)\n\n"
    plan_text += f"☀️ Восход: `{escape_md(sunrise_str)}` \\| 🌙 Закат: `{escape_md(sunset_str)}`\n\n"
    plan_text += f"🌅 *Утро \\(до ~12:00\\)*\n"
    if morning_mantra_data:
        plan_text += f"   _{escape_md(morning_mantra_data['ossetian'])}_\n"
    plan_text += escape_md("   Практика: Настройся на день с благодарностью\\.\n\n")
    plan_text += f"🌍 *День*\n"
    plan_text += f"   ⚡ Практика: {main_task_text}\n"
    plan_text += f"   🎯 Отметь выполнение категорий ниже:\n\n"
    plan_text += f"🌃 *Вечер \\(после ~18:00\\)*\n"
    if evening_mantra_data:
        plan_text += f"   _{escape_md(evening_mantra_data['ossetian'])}_\n"
    plan_text += escape_md("   🧘 Практика: Заверши день рефлексией в '✍️ Дневник'\\.\n\n")
    plan_text += f"💚 *Прогресс дня:*\n   {rings_text}"

    inline_kb_buttons = []
    for cat_code in ACTIVITY_CATEGORIES:
         emoji = CATEGORY_EMOJI_MAP.get(cat_code, "❓")
         cat_name = CATEGORY_NAMES_MAP.get(cat_code, cat_code)
         completed = activity_status.get(cat_code, False)
         inline_kb_buttons.append(
             InlineKeyboardButton(text=f"{'✅' if completed else emoji} {cat_name}", callback_data=f"log_activity:{cat_code}")
         )
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[inline_kb_buttons])

    await message.answer(plan_text, reply_markup=inline_kb)

# Обработчик отметки активности (с обновлением сообщения)
@dp.callback_query(F.data.startswith("log_activity:"))
async def process_log_activity_callback(callback_query: CallbackQuery, state: FSMContext):
    category_to_log = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id

    await log_daily_activity(user_id, category_to_log)
    await callback_query.answer(f"✅ {CATEGORY_NAMES_MAP.get(category_to_log, category_to_log)} отмечено!")

    # --- Обновление исходного сообщения ---
    user_data = await get_user_data(user_id)
    if not user_data: return

    sun_times = get_sun_times(user_data["lat"], user_data["lon"], user_data["tz"], user_data["city"])
    sunrise_dt = sun_times.get("sunrise")
    sunset_dt = sun_times.get("sunset")
    sunrise_str = sunrise_dt.strftime('%H:%M') if sunrise_dt else "н/д"
    sunset_str = sunset_dt.strftime('%H:%M') if sunset_dt else "н/д"

    activity_status = await get_daily_activity_status(user_id) # Получаем СНОВА
    rings = []
    for cat_code in ACTIVITY_CATEGORIES:
         emoji = CATEGORY_EMOJI_MAP.get(cat_code, "❓")
         cat_name = CATEGORY_NAMES_MAP.get(cat_code, cat_code)
         completed = activity_status.get(cat_code, False)
         rings.append(f"{emoji} {('🟢' if completed else '⚪️')} {escape_md(cat_name)}")
    rings_text = " \\| ".join(rings)

    current_phase = user_data.get("current_phase", DEFAULT_PHASE)
    task_info = TASKS.get(current_phase)
    main_task_text = task_info.get('daily_habit', escape_md("Практика дня")) if task_info else escape_md("Практика дня")

    # Пытаемся сохранить мантры из исходного сообщения
    morning_mantra_line = ""
    evening_mantra_line = ""
    if callback_query.message and callback_query.message.text:
        original_text_lines = callback_query.message.text.split('\n')
        in_morning, in_evening = False, False
        for line in original_text_lines:
            clean_line = line.strip()
            if clean_line.startswith("🌅 *Утро"): in_morning = True; in_evening = False; continue
            if clean_line.startswith("🌍 *День"): in_morning = False; in_evening = False; continue
            if clean_line.startswith("🌃 *Вечер"): in_morning = False; in_evening = True; continue
            if in_morning and clean_line.startswith("_"): morning_mantra_line = line + "\n"; continue
            if in_evening and clean_line.startswith("_"): evening_mantra_line = line + "\n"; continue

    # Собираем обновленный текст
    plan_text = f"🗓️ *План на {escape_md(date.today().strftime('%d.%m'))}* \\({escape_md(user_data['city'])}\\)\n\n"
    plan_text += f"☀️ Восход: `{escape_md(sunrise_str)}` \\| 🌙 Закат: `{escape_md(sunset_str)}`\n\n"
    plan_text += f"🌅 *Утро \\(до ~12:00\\)*\n{morning_mantra_line}" # Используем сохраненную строку
    plan_text += escape_md("   Практика: Настройся на день с благодарностью\\.\n\n")
    plan_text += f"🌍 *День*\n   ⚡ Практика: {main_task_text}\n"
    plan_text += f"   🎯 Отметь выполнение категорий ниже:\n\n"
    plan_text += f"🌃 *Вечер \\(после ~18:00\\)*\n{evening_mantra_line}" # Используем сохраненную строку
    plan_text += escape_md("   🧘 Практика: Заверши день рефлексией в '✍️ Дневник'\\.\n\n")
    plan_text += f"💚 *Прогресс дня:*\n   {rings_text}"

    # Новая клавиатура
    inline_kb_buttons = []
    for cat_code in ACTIVITY_CATEGORIES:
         emoji = CATEGORY_EMOJI_MAP.get(cat_code, "❓")
         cat_name = CATEGORY_NAMES_MAP.get(cat_code, cat_code)
         completed = activity_status.get(cat_code, False)
         inline_kb_buttons.append(
             InlineKeyboardButton(text=f"{'✅' if completed else emoji} {cat_name}", callback_data=f"log_activity:{cat_code}")
         )
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[inline_kb_buttons])

    try:
        # Проверяем, изменился ли текст (хотя бы кольца должны были измениться)
        if callback_query.message.text != plan_text:
             await callback_query.message.edit_text(plan_text, reply_markup=inline_kb)
        else:
             # Если текст не изменился (например, двойное нажатие), просто подтверждаем
             await callback_query.answer("✅ Уже отмечено!")
    except TelegramAPIError as e:
        if "message is not modified" in str(e):
             await callback_query.answer("✅ Уже отмечено!")
        else:
             logger.warning(f"Could not edit daily plan message: {e}")
             # Если совсем не удалось, просто сообщаем
             await callback_query.answer("Не удалось обновить план.", show_alert=True)


@dp.message(F.text.in_({"✍️ Дневник", "/diary"}))
async def handle_diary_button(message: Message, state: FSMContext):
    await message.answer(escape_md("📝 Что у тебя на сердце? Напиши:"))
    await state.set_state(DiaryStates.waiting_for_entry)

@dp.message(DiaryStates.waiting_for_entry)
async def process_diary_entry_message(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_entry = message.text
    try:
        await add_diary_entry(user_id, user_entry)
        # Можно автоматически отмечать категорию 'mindfulness' при записи в дневник
        # await log_daily_activity(user_id, "mindfulness")
        await message.answer(escape_md("Запись сохранена 🙏"), reply_markup=get_main_menu_keyboard()) # Возвращаем меню
    except Exception as e:
        logger.error(f"Failed to add diary entry for user {user_id}: {e}")
        await message.answer(escape_md("🚫 Не удалось сохранить запись. Попробуйте позже."), reply_markup=get_main_menu_keyboard())
    finally:
        await state.clear()

@dp.message(Command('mydiary')) # Оставим команду для удобства
async def handle_mydiary(message: Message):
    user_id = message.from_user.id
    entries = await get_last_diary_entries(user_id, limit=5)
    if not entries:
        await message.answer(escape_md("В вашем дневнике пока нет записей. Используйте кнопку '✍️ Дневник'."))
        return
    response_text = escape_md("📖 Ваши последние 5 записей:\n") # Добавил эмоджи
    for entry in reversed(entries):
        try:
            # Убедимся, что timestamp это строка перед парсингом
            ts_str = str(entry['timestamp']).split('.')[0]
            ts_dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
            # Можно добавить локализацию времени, если таймзона пользователя известна
            ts_formatted = ts_dt.strftime('%d.%m.%y %H:%M')
        except (ValueError, TypeError):
             ts_formatted = str(entry['timestamp']) # Возврат к строке если ошибка
        response_text += f"\n*{escape_md(ts_formatted)}*\n"
        response_text += f"{escape_md(entry['text'])}\n"
    if len(response_text) > 4090:
         response_text = response_text[:4090] + "\n" + escape_md("...")
    await message.answer(response_text)


@dp.message(F.text == "📍 Локация")
async def handle_location_button(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить мою геолокацию", request_location=True)],
            [KeyboardButton(text="🚫 Отмена")] # Кнопка отмены
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
    """Обрабатывает отмену запроса локации."""
    await message.answer("Хорошо, оставим настройки локации по умолчанию.", reply_markup=get_main_menu_keyboard())


@dp.message(StateFilter(None), F.content_type == ContentType.LOCATION)
async def handle_user_location(message: Message):
    user_id = message.from_user.id
    lat = message.location.latitude
    lon = message.location.longitude
    logger.info(f"Received location from user {user_id}: lat={lat}, lon={lon}")
    await message.answer(escape_md("⏳ Определяю город и часовой пояс..."), reply_markup=types.ReplyKeyboardRemove()) # Убираем кнопку запроса локации

    city = "Неизвестно"
    tz_str = DEFAULT_TIMEZONE

    try:
        # Используем geopy (может быть медленным)
        location_info = await geocode(f"{lat}, {lon}", language='ru', exactly_one=True, addressdetails=True, timeout=10)
        if location_info and location_info.raw.get('address'):
            address = location_info.raw['address']
            # Пытаемся найти город/нас. пункт в разных полях
            city = address.get('city', address.get('town', address.get('village', address.get('county', city))))
            country_code = address.get('country_code', '').upper()
            logger.info(f"Geocoded location: City='{city}', Country Code={country_code}")

            # Пытаемся определить таймзону через Astral
            if astral_geo:
                try:
                    # Сначала ищем по городу
                    astral_loc_info = astral_geo.lookup(city)
                    if astral_loc_info:
                         tz_str = astral_loc_info.timezone
                         logger.info(f"Found timezone via astral for city '{city}': {tz_str}")
                    elif country_code: # Если город не нашелся, пробуем по стране
                         astral_loc_info_country = astral_geo.lookup(country_code, is_country=True)
                         if astral_loc_info_country:
                             tz_str = astral_loc_info_country.timezone
                             logger.info(f"Found timezone via astral for country '{country_code}': {tz_str}")
                         else:
                             logger.warning(f"Could not find timezone for city '{city}' or country '{country_code}' via astral.")
                    else:
                         logger.warning(f"Could not find timezone for city '{city}' via astral (no country code).")

                except Exception as e_astral:
                    logger.error(f"Error looking up timezone via astral: {e_astral}")
            else:
                 logger.warning("Astral Geocoder not initialized.")
        else:
             logger.warning(f"Geopy could not find address details for {lat},{lon}")
    except Exception as e_geo:
        logger.error(f"Geopy error getting location info: {e_geo}")
        # Можно уведомить пользователя об ошибке
        await message.answer(escape_md("Не удалось определить город по координатам. Попробуйте позже."), reply_markup=get_main_menu_keyboard())
        return

    # Сохраняем в БД
    await update_user_location(user_id, lat, lon, city, tz_str)

    await message.answer(
        escape_md(f"📍 Локация сохранена: *{city}*\nЧасовой пояс: `{tz_str}`\nСпасибо\\! 🙏"),
        reply_markup=get_main_menu_keyboard() # Возвращаем основное меню
    )


@dp.message(F.text.in_({"📊 Статистика", "/stats"}))
async def handle_stats_button(message: Message):
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)
    stats_detailed = await get_user_weekly_stats_detailed(user_id)

    if not user_data:
        await message.answer(escape_md("Не нашел ваши данные. Попробуйте /start."))
        return

    streak = user_data.get('streak', 0)

    stats_text = f"📊 *Твоя статистика за 7 дней:*\n\n"
    stats_text += f"☀️ Активных дней: *{escape_md(stats_detailed['days_active'])}* из 7\n"
    stats_text += f"✍️ Записей в дневнике: *{escape_md(stats_detailed['diary_entries'])}*\n"
    stats_text += f"🔥 Текущий стрик: *{escape_md(streak)}* дня\\(ей\\)\n\n"
    stats_text += f"🎯 *Выполнено практик по категориям:*\n"
    has_category_stats = False
    for cat_code in ACTIVITY_CATEGORIES:
        count = stats_detailed['categories_done'].get(cat_code, 0)
        # if count > 0: # Показывать все категории, даже если 0
        has_category_stats = True # Считаем, что статы есть, если есть категории
        emoji = CATEGORY_EMOJI_MAP.get(cat_code, "❓")
        cat_name = CATEGORY_NAMES_MAP.get(cat_code, cat_code)
        stats_text += f"   {emoji} {escape_md(cat_name)}: *{escape_md(count)}*\n"
    if not has_category_stats:
         stats_text += escape_md("   Пока нет данных по категориям.\n")

    stats_text += f"\n📈 Общее число выполненных практик: *{escape_md(stats_detailed['tasks_done_total'])}*"

    # Кнопка для общей статистики
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Общая статистика", callback_data="show_group_stats")]
    ])

    await message.answer(stats_text, reply_markup=keyboard)

# Обработчик кнопки общей статистики
@dp.callback_query(F.data == "show_group_stats")
async def process_show_group_stats(callback_query: CallbackQuery):
     stats = await get_group_weekly_stats_categorized()
     response = f"🌍 *Статистика сообщества за 7 дней:*\n\n"
     response += f"👥 Активных участников: *{escape_md(stats['total_users_active'])}*\n\n"
     response += f"🎯 *Всего выполнено практик:*\n"
     has_group_cat_stats = False
     for cat_code in ACTIVITY_CATEGORIES:
        count = stats['categories_done'].get(cat_code, 0)
        if count > 0:
             has_group_cat_stats = True
             emoji = CATEGORY_EMOJI_MAP.get(cat_code, "❓")
             cat_name = CATEGORY_NAMES_MAP.get(cat_code, cat_code)
             response += f"   {emoji} {escape_md(cat_name)}: *{escape_md(count)}*\n"
     if not has_group_cat_stats:
         response += escape_md("   Пока нет данных.\n")

     response += f"\n📈 Общее число практик: *{escape_md(stats['total_tasks_done'])}*"

     await callback_query.message.answer(response)
     await callback_query.answer() # Закрываем часики на кнопке


# --- Основная функция запуска ---
async def main():
    await init_db()
    await populate_mantras_if_empty()

    # Запуск планировщика для ежедневного сброса
    scheduler.add_job(reset_daily_activities_job, 'cron', hour=0, minute=5, timezone='UTC') # Сдвинул на 5 минут
    scheduler.start()
    logger.info("Scheduler started for daily reset.")

    logger.info("Starting bot polling...")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
    except Exception as e:
        logger.critical(f"Unhandled exception at top level: {e}", exc_info=True)
    finally:
        if scheduler.running:
             scheduler.shutdown(wait=False) # Не ждать завершения задач при остановке
             logger.info("Scheduler shut down.")