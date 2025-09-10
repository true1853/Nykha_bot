import logging
import aiosqlite
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict

from config import (
    DATABASE_FILE as DB_NAME,
    DEFAULT_PHASE,
    DEFAULT_CITY_NAME,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_TIMEZONE,
)
from data import MANTRAS_DATA  # Ваш список мантр из data.py

logger = logging.getLogger(__name__)


async def init_db():
    """Создаёт таблицы и делает миграции столбцов в users."""
    async with aiosqlite.connect(DB_NAME) as db:
        # 1) Базовая схема users (без мигрированных полей)
        await db.execute(f'''
            CREATE TABLE IF NOT EXISTS users (
                user_id       INTEGER PRIMARY KEY,
                current_phase TEXT    NOT NULL DEFAULT '{DEFAULT_PHASE}',
                first_name    TEXT,
                streak        INTEGER DEFAULT 0
            )
        ''')

        # 2) Проверяем, какие столбцы уже есть
        pragma = await db.execute("PRAGMA table_info(users)")
        existing = {row[1] for row in await pragma.fetchall()}

        # 3) Для каждого нового столбца — выполняем ALTER, если его нет
        migration_statements = []
        if 'last_login' not in existing:
            migration_statements.append(
                "ALTER TABLE users ADD COLUMN last_login TIMESTAMP"
            )
        if 'location_city' not in existing:
            migration_statements.append(
                f"ALTER TABLE users ADD COLUMN location_city TEXT DEFAULT '{DEFAULT_CITY_NAME}'"
            )
        if 'location_lat' not in existing:
            migration_statements.append(
                f"ALTER TABLE users ADD COLUMN location_lat REAL DEFAULT {DEFAULT_LATITUDE}"
            )
        if 'location_lon' not in existing:
            migration_statements.append(
                f"ALTER TABLE users ADD COLUMN location_lon REAL DEFAULT {DEFAULT_LONGITUDE}"
            )
        if 'timezone' not in existing:
            migration_statements.append(
                f"ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT '{DEFAULT_TIMEZONE}'"
            )

        for stmt in migration_statements:
            logger.info(f"Миграция users: {stmt}")
            await db.execute(stmt)
        if migration_statements:
            await db.commit()

        # 4) Создаём остальные таблицы
        await db.execute('''
            CREATE TABLE IF NOT EXISTS diary_entries (
                entry_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                timestamp  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                entry_text TEXT    NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS mantras (
                mantra_id           INTEGER PRIMARY KEY AUTOINCREMENT,
                category            TEXT    NOT NULL,
                ossetian_text       TEXT    NOT NULL UNIQUE,
                russian_translation TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS daily_activity (
                activity_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                activity_date DATE    DEFAULT CURRENT_DATE,
                category      TEXT    NOT NULL,
                completed     BOOLEAN DEFAULT FALSE,
                timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, activity_date, category)
            )
        ''')
        await db.commit()

    logger.info("Инициализация БД и миграции завершены.")


async def populate_mantras_if_empty():
    """Заполняет таблицу мантр из MANTRAS_DATA, если она пуста."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM mantras")
        count = (await cursor.fetchone())[0]
        if count == 0:
            logger.info("Заполняем таблицу mantras...")
            await db.executemany(
                "INSERT OR IGNORE INTO mantras (category, ossetian_text, russian_translation) VALUES (?, ?, ?)",
                MANTRAS_DATA
            )
            await db.commit()
            cursor2 = await db.execute("SELECT COUNT(*) FROM mantras")
            total = (await cursor2.fetchone())[0]
            logger.info(f"Вставлено мантр: {total}")


async def add_user_if_not_exists(user_id: int, first_name: str) -> bool:
    """Добавляет пользователя, если его нет. Возвращает True, если добавлен."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
        )
        exists = await cursor.fetchone()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not exists:
            await db.execute(
                "INSERT INTO users (user_id, current_phase, first_name, location_city, location_lat, location_lon, timezone, last_login) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, DEFAULT_PHASE, first_name, DEFAULT_CITY_NAME,
                 DEFAULT_LATITUDE, DEFAULT_LONGITUDE, DEFAULT_TIMEZONE, now)
            )
            await db.commit()
            logger.info(f"Новый пользователь {user_id} добавлен.")
            return True

        # Обновляем имя и last_login
        await db.execute(
            "UPDATE users SET first_name = ?, last_login = ? WHERE user_id = ?",
            (first_name, now, user_id)
        )
        await db.commit()
        return False


async def get_user_data(user_id: int) -> Optional[Dict]:
    """Возвращает данные пользователя или None."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT current_phase, streak, first_name, location_city, location_lat, location_lon, timezone "
            "FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "current_phase": row[0],
            "streak":        row[1],
            "first_name":    row[2],
            "city":          row[3],
            "lat":           row[4],
            "lon":           row[5],
            "tz":            row[6],
        }


async def update_user_location(user_id: int, lat: float, lon: float, city: str, tz: str):
    """Обновляет в БД город и таймзону пользователя."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET location_lat = ?, location_lon = ?, location_city = ?, timezone = ? WHERE user_id = ?",
            (lat, lon, city, tz, user_id)
        )
        await db.commit()
    logger.info(f"Локация пользователя {user_id} обновлена на {city}, tz={tz}.")


async def log_daily_activity(user_id: int, category: str):
    """Помечает категорию выполненной на сегодня."""
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO daily_activity (user_id, activity_date, category, completed, timestamp) "
            "VALUES (?, ?, ?, TRUE, CURRENT_TIMESTAMP)",
            (user_id, today, category)
        )
        await db.commit()
    logger.info(f"Пользователь {user_id} выполнил '{category}' на {today}.")


async def get_daily_activity_status(user_id: int) -> Dict[str, bool]:
    """Возвращает для каждой категории, выполнена ли она сегодня."""
    from config import ACTIVITY_CATEGORIES

    done = set()
    async with aiosqlite.connect(DB_NAME) as db:
        today = date.today().isoformat()
        cursor = await db.execute(
            "SELECT category FROM daily_activity WHERE user_id = ? AND activity_date = ? AND completed = TRUE",
            (user_id, today)
        )
        for row in await cursor.fetchall():
            done.add(row[0])

    return {cat: (cat in done) for cat in ACTIVITY_CATEGORIES}


async def get_user_weekly_stats_detailed(user_id: int) -> Dict:
    """Статистика пользователя за последние 7 дней."""
    from config import ACTIVITY_CATEGORIES

    week_ago = (date.today() - timedelta(days=6)).isoformat()
    stats = {
        "days_active":      0,
        "diary_entries":    0,
        "tasks_done_total": 0,
        "categories_done":  {cat: 0 for cat in ACTIVITY_CATEGORIES}
    }

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT COUNT(DISTINCT activity_date) FROM daily_activity "
            "WHERE user_id = ? AND activity_date >= ? AND completed = TRUE",
            (user_id, week_ago)
        )
        stats["days_active"] = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM diary_entries WHERE user_id = ? AND DATE(timestamp) >= ?",
            (user_id, week_ago)
        )
        stats["diary_entries"] = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT category, COUNT(*) FROM daily_activity "
            "WHERE user_id = ? AND activity_date >= ? AND completed = TRUE GROUP BY category",
            (user_id, week_ago)
        )
        for cat, cnt in await cursor.fetchall():
            stats["categories_done"][cat] = cnt
            stats["tasks_done_total"] += cnt

    return stats


async def get_group_weekly_stats_categorized() -> Dict:
    """Статистика всех пользователей за последние 7 дней."""
    from config import ACTIVITY_CATEGORIES

    week_ago = (date.today() - timedelta(days=6)).isoformat()
    stats = {
        "total_users_active": 0,
        "total_tasks_done":   0,
        "categories_done":    {cat: 0 for cat in ACTIVITY_CATEGORIES}
    }

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT COUNT(DISTINCT user_id) FROM daily_activity "
            "WHERE activity_date >= ? AND completed = TRUE",
            (week_ago,)
        )
        stats["total_users_active"] = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT category, COUNT(*) FROM daily_activity "
            "WHERE activity_date >= ? AND completed = TRUE GROUP BY category",
            (week_ago,)
        )
        for cat, cnt in await cursor.fetchall():
            stats["categories_done"][cat] = cnt
            stats["total_tasks_done"] += cnt

    return stats


async def get_random_mantra() -> Optional[Dict[str, str]]:
    """Любая случайная мантра."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT category, ossetian_text, russian_translation "
            "FROM mantras ORDER BY RANDOM() LIMIT 1"
        )
        row = await cursor.fetchone()
    if not row:
        return None
    return {"category": row[0], "ossetian": row[1], "russian": row[2]}


async def get_random_mantra_by_category(category: str) -> Optional[Dict[str, str]]:
    """Случайная мантра из заданной категории или любая, если не нашлось."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT ossetian_text, russian_translation FROM mantras "
            "WHERE category = ? ORDER BY RANDOM() LIMIT 1",
            (category,)
        )
        row = await cursor.fetchone()
    if row:
        return {"category": category, "ossetian": row[0], "russian": row[1]}
    return await get_random_mantra()


async def get_mantra_categories() -> List[str]:
    """Возвращает список всех категорий мантр."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT DISTINCT category FROM mantras")
        rows = await cursor.fetchall()
    # rows — список кортежей вида [(cat1,), (cat2,), …]
    return [row[0] for row in rows]


async def add_diary_entry(user_id: int, text: str):
    """Добавляет запись в дневник."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO diary_entries (user_id, entry_text) VALUES (?, ?)",
            (user_id, text)
        )
        await db.commit()
    logger.info(f"Diary entry saved for user {user_id}.")


async def get_last_diary_entries(user_id: int, limit: int = 5) -> List[Dict]:
    """Возвращает последние `limit` записей."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT timestamp, entry_text FROM diary_entries "
            "WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
    return [{"timestamp": row[0], "text": row[1]} for row in rows]


async def increment_user_streak(user_id: int) -> int:
    """Увеличивает стрик на 1 и возвращает новое значение."""
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET streak = streak + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.execute(
            "UPDATE users SET last_login = ? WHERE user_id = ?",
            (today, user_id)
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT streak FROM users WHERE user_id = ?", (user_id,)
        )
        new_streak = (await cursor.fetchone())[0]
    logger.info(f"User {user_id} streak incremented to {new_streak}.")
    return new_streak

async def get_mantra_categories() -> List[str]:
    """Вернуть список всех уникальных категорий мантр."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT DISTINCT category FROM mantras")
        rows = await cursor.fetchall()
    return [row[0] for row in rows]

async def get_mantras_by_category(category: str) -> List[Dict]:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT ossetian_text, russian_translation FROM mantras WHERE category = ?",
            (category,)
        )
        rows = await cursor.fetchall()
    return [{"ossetian_text": row[0], "russian_translation": row[1]} for row in rows]

async def reset_daily_activities_job():
    """Удаляет старые записи активности (до вчерашнего включительно)."""
    cutoff = (date.today() - timedelta(days=1)).isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "DELETE FROM daily_activity WHERE activity_date < ?",
            (cutoff,)
        )
        await db.commit()
    logger.info(f"Daily reset: deleted {cursor.rowcount} old records.")
