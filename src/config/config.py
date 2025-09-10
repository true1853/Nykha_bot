"""
Optimized configuration for FarnPathBot.
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("API_TOKEN is required")

# Database Configuration
DATABASE_FILE = os.getenv("DATABASE_FILE", "farnpathbot.db")
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
DATABASE_TIMEOUT = int(os.getenv("DATABASE_TIMEOUT", "30"))

# Performance Configuration
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes
RATE_LIMIT_CALLS = int(os.getenv("RATE_LIMIT_CALLS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(levelname)s - %(name)s - %(message)s")

# Default User Settings
DEFAULT_PHASE = os.getenv("DEFAULT_PHASE", "phase1_week1")
DEFAULT_CITY_NAME = os.getenv("DEFAULT_CITY_NAME", "Moscow")
DEFAULT_LATITUDE = float(os.getenv("DEFAULT_LATITUDE", "55.7558"))
DEFAULT_LONGITUDE = float(os.getenv("DEFAULT_LONGITUDE", "37.6173"))
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Europe/Moscow")

# External Services
GEOPY_USER_AGENT = os.getenv("GEOPY_USER_AGENT", "FarnPathBot (true1853@yandex.ru)")
GEOCODING_TIMEOUT = int(os.getenv("GEOCODING_TIMEOUT", "10"))

# Activity Categories
ACTIVITY_CATEGORIES = ["mindfulness", "nature", "service"]
CATEGORY_EMOJI_MAP = {
    "mindfulness": "🧘",
    "nature": "🌳",
    "service": "🤝",
}
CATEGORY_NAMES_MAP = {
    "mindfulness": "Осознанность",
    "nature": "Природа",
    "service": "Служение",
}

# 12-Week Plan Configuration
TASKS = {
    "phase1_week1": {
        "title": "Неделя 1: Живи благодатью Земли",
        "daily_habit": "1–2 минуты в день созерцайте элемент природы и ощущайте благодарность.",
        "meal_habit": "Перед едой произносите «Зæххы фарнæй цæр» (Живи благодатью Земли).",
        "reflection": "Вечером запишите одно наблюдение о вашей взаимосвязи с природой.",
    },
    "phase1_week2": {
        "title": "Неделя 2: Един через коллективный разум",
        "daily_habit": "В течение дня замечайте моменты, когда вы действуете в интересах группы.",
        "meal_habit": "Перед едой подумайте о том, как ваше питание влияет на сообщество.",
        "reflection": "Запишите один пример коллективного действия, в котором вы участвовали.",
    },
    "phase1_week3": {
        "title": "Неделя 3: Трудись ради обновления",
        "daily_habit": "Выделяйте 5 минут на созидательную активность: посадка растения или уборка.",
        "meal_habit": "Перед едой мысленно посвятите труд, который помогает природе восстановиться.",
        "reflection": "Запишите, какое маленькое дело вы сделали во благо планеты.",
    },
    "phase1_week4": {
        "title": "Неделя 4: Иди путём чести",
        "daily_habit": "Проверяйте свои поступки на соответствие кодексу чести и справедливости.",
        "meal_habit": "Перед едой произнесите мысленно честную и благодарственную фразу.",
        "reflection": "Запишите ситуацию, где вы выбрали честность вместо лёгкого пути.",
    },
    "phase1_week5": {
        "title": "Неделя 5: Храни воду чистой, как слезинку",
        "daily_habit": "Сократите расход воды и обратите внимание, сколько воды вы используете.",
        "meal_habit": "Пейте только чистую воду и мысленно поблагодарите источник.",
        "reflection": "Запишите, где и как вы сэкономили воду сегодня.",
    },
    "phase1_week6": {
        "title": "Неделя 6: Лес — дыхание наших предков",
        "daily_habit": "Проведите 5–10 минут в лесу или среди растений, глубоко дыша.",
        "meal_habit": "Перед едой вспомните лес и его роль в вашем дыхании.",
        "reflection": "Опишите, как запах и звук леса повлияли на ваше состояние.",
    },
    "phase1_week7": {
        "title": "Неделя 7: Цифра — не замена душе",
        "daily_habit": "Ограничьте экранное время и замените его моментом тишины.",
        "meal_habit": "Во время еды отключайте все гаджеты и ешьте осознанно.",
        "reflection": "Запишите, как ощущалось питание без цифровых отвлечений.",
    },
    "phase1_week8": {
        "title": "Неделя 8: Рука не для разрушения",
        "daily_habit": "Каждый день совершайте хотя бы один акт созидания или помощи.",
        "meal_habit": "Перед едой подумайте, какие добрые дела вы совершите сегодня.",
        "reflection": "Опишите ваш акт созидания или помощи другим людям.",
    },
    "phase1_week9": {
        "title": "Неделя 9: Как нарты, ищи равновесие",
        "daily_habit": "Найдите баланс между работой и отдыхом, уделите время себе и окружающим.",
        "meal_habit": "Перед едой настройтесь на гармонию тела и души.",
        "reflection": "Запишите, как вы сегодня сохранили внутреннее равновесие.",
    },
    "phase1_week10": {
        "title": "Неделя 10: Великое через малое",
        "daily_habit": "Совершайте маленькие добрые дела: улыбнитесь, помогите с чем-то простым.",
        "meal_habit": "Перед едой вспомните малое дело, совершённое вами сегодня.",
        "reflection": "Запишите, как маленький шаг привёл к большому изменению.",
    },
    "phase1_week11": {
        "title": "Неделя 11: Ты не первое поколение",
        "daily_habit": "Думайте о корнях и своих предках, посвятите минуту благодарности.",
        "meal_habit": "Во время еды вспомните традиции своей семьи и предков.",
        "reflection": "Запишите, какие семейные ценности вы сегодня почитали.",
    },
    "phase1_week12": {
        "title": "Неделя 12: Твоя благодать — благодать Земли",
        "daily_habit": "Сознательно ощущайте взаимосвязь своей жизненной силы и природы.",
        "meal_habit": "Перед едой произнесите «Хи фарн — зæххы фарн» (Твоя благодать — благодать Земли).",
        "reflection": "Запишите, как сегодня природа подпитывала вашу благодать.",
    }
}

# Performance Settings
PERFORMANCE_SETTINGS = {
    "enable_caching": os.getenv("ENABLE_CACHING", "true").lower() == "true",
    "enable_monitoring": os.getenv("ENABLE_MONITORING", "true").lower() == "true",
    "enable_rate_limiting": os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true",
    "log_performance": os.getenv("LOG_PERFORMANCE", "false").lower() == "true",
}

# Database Optimization Settings
DATABASE_SETTINGS = {
    "journal_mode": "WAL",
    "synchronous": "NORMAL",
    "cache_size": 10000,
    "temp_store": "MEMORY",
    "foreign_keys": True,
    "optimize_on_close": True,
}

# Error Handling Settings
ERROR_SETTINGS = {
    "max_retries": int(os.getenv("MAX_RETRIES", "3")),
    "retry_delay": float(os.getenv("RETRY_DELAY", "1.0")),
    "log_errors": os.getenv("LOG_ERRORS", "true").lower() == "true",
    "notify_errors": os.getenv("NOTIFY_ERRORS", "false").lower() == "true",
}

def get_config() -> Dict[str, Any]:
    """Get complete configuration dictionary."""
    return {
        "api_token": API_TOKEN,
        "database": {
            "file": DATABASE_FILE,
            "pool_size": DATABASE_POOL_SIZE,
            "timeout": DATABASE_TIMEOUT,
            "settings": DATABASE_SETTINGS,
        },
        "performance": {
            "cache_ttl": CACHE_TTL,
            "rate_limit_calls": RATE_LIMIT_CALLS,
            "rate_limit_window": RATE_LIMIT_WINDOW,
            "settings": PERFORMANCE_SETTINGS,
        },
        "logging": {
            "level": LOG_LEVEL,
            "format": LOG_FORMAT,
        },
        "defaults": {
            "phase": DEFAULT_PHASE,
            "city": DEFAULT_CITY_NAME,
            "latitude": DEFAULT_LATITUDE,
            "longitude": DEFAULT_LONGITUDE,
            "timezone": DEFAULT_TIMEZONE,
        },
        "external": {
            "geopy_user_agent": GEOPY_USER_AGENT,
            "geocoding_timeout": GEOCODING_TIMEOUT,
        },
        "activities": {
            "categories": ACTIVITY_CATEGORIES,
            "emoji_map": CATEGORY_EMOJI_MAP,
            "names_map": CATEGORY_NAMES_MAP,
        },
        "tasks": TASKS,
        "error_handling": ERROR_SETTINGS,
    }
