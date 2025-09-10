"""
Optimized database repository with connection pooling.
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from src.database.connection import get_db_cursor
from src.database.models import User, DiaryEntry, Mantra, DailyActivity, UserStats, GroupStats, ActivityCategory
from src.config.config import (
    DEFAULT_PHASE, DEFAULT_CITY_NAME, DEFAULT_LATITUDE, 
    DEFAULT_LONGITUDE, DEFAULT_TIMEZONE, ACTIVITY_CATEGORIES
)
from src.data import MANTRAS_DATA

logger = logging.getLogger(__name__)

class UserRepository:
    """Repository for user operations."""
    
    @staticmethod
    async def add_user_if_not_exists(user_id: int, first_name: str) -> bool:
        """Add user if not exists. Returns True if added."""
        async with get_db_cursor() as cursor:
            # Check if user exists
            await cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            exists = await cursor.fetchone()
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if not exists:
                await cursor.execute(
                    """INSERT INTO users (user_id, current_phase, first_name, location_city, 
                       location_lat, location_lon, timezone, last_login) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, DEFAULT_PHASE, first_name, DEFAULT_CITY_NAME,
                     DEFAULT_LATITUDE, DEFAULT_LONGITUDE, DEFAULT_TIMEZONE, now)
                )
                await cursor.connection.commit()
                logger.info(f"New user {user_id} added")
                return True
            else:
                # Update existing user
                await cursor.execute(
                    "UPDATE users SET first_name = ?, last_login = ? WHERE user_id = ?",
                    (first_name, now, user_id)
                )
                await cursor.connection.commit()
                return False
    
    @staticmethod
    async def get_user_data(user_id: int) -> Optional[User]:
        """Get user data by ID."""
        async with get_db_cursor() as cursor:
            await cursor.execute(
                """SELECT current_phase, streak, first_name, location_city, 
                   location_lat, location_lon, timezone 
                   FROM users WHERE user_id = ?""",
                (user_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
                
            return User(
                user_id=user_id,
                current_phase=row[0],
                streak=row[1],
                first_name=row[2],
                location_city=row[3],
                location_lat=row[4],
                location_lon=row[5],
                timezone=row[6]
            )
    
    @staticmethod
    async def update_user_location(user_id: int, lat: float, lon: float, city: str, tz: str):
        """Update user location."""
        async with get_db_cursor() as cursor:
            await cursor.execute(
                """UPDATE users SET location_lat = ?, location_lon = ?, 
                   location_city = ?, timezone = ? WHERE user_id = ?""",
                (lat, lon, city, tz, user_id)
            )
            await cursor.connection.commit()
            logger.info(f"User {user_id} location updated to {city}, tz={tz}")

class ActivityRepository:
    """Repository for activity operations."""
    
    @staticmethod
    async def log_daily_activity(user_id: int, category: str) -> bool:
        """Log daily activity. Returns True if successful."""
        if category not in ACTIVITY_CATEGORIES:
            logger.warning(f"Invalid activity category: {category}")
            return False
            
        today = date.today().isoformat()
        async with get_db_cursor() as cursor:
            await cursor.execute(
                """INSERT OR REPLACE INTO daily_activity 
                   (user_id, activity_date, category, completed, timestamp) 
                   VALUES (?, ?, ?, TRUE, CURRENT_TIMESTAMP)""",
                (user_id, today, category)
            )
            await cursor.connection.commit()
            logger.info(f"User {user_id} completed '{category}' on {today}")
            return True
    
    @staticmethod
    async def get_daily_activity_status(user_id: int) -> Dict[str, bool]:
        """Get today's activity status for user."""
        done = set()
        async with get_db_cursor() as cursor:
            today = date.today().isoformat()
            await cursor.execute(
                """SELECT category FROM daily_activity 
                   WHERE user_id = ? AND activity_date = ? AND completed = TRUE""",
                (user_id, today)
            )
            for row in await cursor.fetchall():
                done.add(row[0])
        
        return {cat: (cat in done) for cat in ACTIVITY_CATEGORIES}
    
    @staticmethod
    async def get_user_weekly_stats(user_id: int) -> UserStats:
        """Get user's weekly statistics."""
        week_ago = (date.today() - timedelta(days=6)).isoformat()
        
        async with get_db_cursor() as cursor:
            # Days active
            await cursor.execute(
                """SELECT COUNT(DISTINCT activity_date) FROM daily_activity 
                   WHERE user_id = ? AND activity_date >= ? AND completed = TRUE""",
                (user_id, week_ago)
            )
            days_active = (await cursor.fetchone())[0]
            
            # Diary entries
            await cursor.execute(
                """SELECT COUNT(*) FROM diary_entries 
                   WHERE user_id = ? AND DATE(timestamp) >= ?""",
                (user_id, week_ago)
            )
            diary_entries = (await cursor.fetchone())[0]
            
            # Categories done
            await cursor.execute(
                """SELECT category, COUNT(*) FROM daily_activity 
                   WHERE user_id = ? AND activity_date >= ? AND completed = TRUE 
                   GROUP BY category""",
                (user_id, week_ago)
            )
            categories_done = {cat: 0 for cat in ACTIVITY_CATEGORIES}
            tasks_done_total = 0
            
            for cat, cnt in await cursor.fetchall():
                if cat in categories_done:
                    categories_done[cat] = cnt
                    tasks_done_total += cnt
            
            # Get user streak
            user_data = await UserRepository.get_user_data(user_id)
            streak = user_data.streak if user_data else 0
            
            return UserStats(
                days_active=days_active,
                diary_entries=diary_entries,
                tasks_done_total=tasks_done_total,
                categories_done=categories_done,
                streak=streak
            )

class MantraRepository:
    """Repository for mantra operations."""
    
    @staticmethod
    async def get_random_mantra() -> Optional[Mantra]:
        """Get random mantra."""
        async with get_db_cursor() as cursor:
            await cursor.execute(
                """SELECT mantra_id, category, ossetian_text, russian_translation 
                   FROM mantras ORDER BY RANDOM() LIMIT 1"""
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
                
            return Mantra(
                mantra_id=row[0],
                category=row[1],
                ossetian_text=row[2],
                russian_translation=row[3]
            )
    
    @staticmethod
    async def get_random_mantra_by_category(category: str) -> Optional[Mantra]:
        """Get random mantra by category."""
        async with get_db_cursor() as cursor:
            await cursor.execute(
                """SELECT mantra_id, ossetian_text, russian_translation 
                   FROM mantras WHERE category = ? ORDER BY RANDOM() LIMIT 1""",
                (category,)
            )
            row = await cursor.fetchone()
            
            if row:
                return Mantra(
                    mantra_id=row[0],
                    category=category,
                    ossetian_text=row[1],
                    russian_translation=row[2]
                )
            
            # Fallback to any random mantra
            return await MantraRepository.get_random_mantra()
    
    @staticmethod
    async def get_categories() -> List[str]:
        """Get all mantra categories."""
        async with get_db_cursor() as cursor:
            await cursor.execute("SELECT DISTINCT category FROM mantras")
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

class DiaryRepository:
    """Repository for diary operations."""
    
    @staticmethod
    async def add_entry(user_id: int, text: str) -> bool:
        """Add diary entry."""
        try:
            async with get_db_cursor() as cursor:
                await cursor.execute(
                    "INSERT INTO diary_entries (user_id, entry_text) VALUES (?, ?)",
                    (user_id, text)
                )
                await cursor.connection.commit()
                logger.info(f"Diary entry saved for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to save diary entry: {e}")
            return False
    
    @staticmethod
    async def get_entries(user_id: int, limit: int = 5) -> List[DiaryEntry]:
        """Get user's diary entries."""
        async with get_db_cursor() as cursor:
            await cursor.execute(
                """SELECT entry_id, timestamp, entry_text FROM diary_entries 
                   WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?""",
                (user_id, limit)
            )
            rows = await cursor.fetchall()
            
            return [
                DiaryEntry(
                    entry_id=row[0],
                    user_id=user_id,
                    timestamp=datetime.fromisoformat(row[1].replace('Z', '+00:00')),
                    entry_text=row[2]
                )
                for row in rows
            ]

class StatsRepository:
    """Repository for statistics operations."""
    
    @staticmethod
    async def get_group_weekly_stats() -> GroupStats:
        """Get group weekly statistics."""
        week_ago = (date.today() - timedelta(days=6)).isoformat()
        
        async with get_db_cursor() as cursor:
            # Total active users
            await cursor.execute(
                """SELECT COUNT(DISTINCT user_id) FROM daily_activity 
                   WHERE activity_date >= ? AND completed = TRUE""",
                (week_ago,)
            )
            total_users_active = (await cursor.fetchone())[0]
            
            # Categories done
            await cursor.execute(
                """SELECT category, COUNT(*) FROM daily_activity 
                   WHERE activity_date >= ? AND completed = TRUE 
                   GROUP BY category""",
                (week_ago,)
            )
            categories_done = {cat: 0 for cat in ACTIVITY_CATEGORIES}
            total_tasks_done = 0
            
            for cat, cnt in await cursor.fetchall():
                if cat in categories_done:
                    categories_done[cat] = cnt
                    total_tasks_done += cnt
            
            return GroupStats(
                total_users_active=total_users_active,
                total_tasks_done=total_tasks_done,
                categories_done=categories_done
            )
