"""
Database models and schemas.
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum

class ActivityCategory(str, Enum):
    """Activity categories enum."""
    MINDFULNESS = "mindfulness"
    NATURE = "nature"
    SERVICE = "service"

@dataclass
class User:
    """User model."""
    user_id: int
    current_phase: str
    first_name: Optional[str] = None
    streak: int = 0
    last_login: Optional[datetime] = None
    location_city: Optional[str] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    timezone: Optional[str] = None

@dataclass
class DiaryEntry:
    """Diary entry model."""
    entry_id: int
    user_id: int
    timestamp: datetime
    entry_text: str

@dataclass
class Mantra:
    """Mantra model."""
    mantra_id: int
    category: str
    ossetian_text: str
    russian_translation: Optional[str] = None

@dataclass
class DailyActivity:
    """Daily activity model."""
    activity_id: int
    user_id: int
    activity_date: date
    category: str
    completed: bool
    timestamp: datetime

@dataclass
class UserStats:
    """User statistics model."""
    days_active: int
    diary_entries: int
    tasks_done_total: int
    categories_done: Dict[str, int]
    streak: int

@dataclass
class GroupStats:
    """Group statistics model."""
    total_users_active: int
    total_tasks_done: int
    categories_done: Dict[str, int]
