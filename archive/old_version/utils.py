"""
utils.py

Общие утилиты:
 - Экранирование MarkdownV2
 - Получение времени восхода/заката для координат, произвольной даты
"""
import logging
from datetime import date, datetime
from typing import TypedDict, Optional, Union

import pytz
from astral import LocationInfo
from astral.sun import sun

logger = logging.getLogger(__name__)

# Markdown V2 escape characters
_ESCAPE_CHARS = r'_*[]()~`>#+-=|{}.!'


class SunTimes(TypedDict):
    sunrise: Optional[datetime]
    sunset: Optional[datetime]


def escape_md(text: object) -> str:
    """
    Экранирует специальные символы MarkdownV2 в строке.

    Args:
        text: Входные данные (будут приведены к строке).

    Returns:
        Текст с экранированными символами MarkdownV2.
    """
    text_str = str(text)
    escaped: list[str] = []
    prev_was_escape = False

    for ch in text_str:
        if ch in _ESCAPE_CHARS and not prev_was_escape:
            escaped.append(f"\\{ch}")
            prev_was_escape = True
        else:
            escaped.append(ch)
            prev_was_escape = (ch == "\\")

    return ''.join(escaped)


def get_sun_times(
    lat: float,
    lon: float,
    tz_str: str,
    city_name: str = "Default",
    target_date: Union[date, None] = None
) -> SunTimes:
    """
    Возвращает время восхода и заката для заданных координат, часового пояса и даты.

    Args:
        lat: Широта.
        lon: Долгота.
        tz_str: Строка часового пояса (например, 'Europe/Moscow').
        city_name: Имя локации для логирования.
        target_date: Дата, для которой считать времена. Если None, берётся сегодня.

    Returns:
        Словарь с ключами 'sunrise' и 'sunset'.
    """
    try:
        loc = LocationInfo(
            name=city_name,
            region="",
            timezone=tz_str,
            latitude=lat,
            longitude=lon
        )
        tz = pytz.timezone(tz_str)
        calc_date = target_date if target_date is not None else datetime.now(tz).date()
        s = sun(observer=loc.observer, date=calc_date, tzinfo=tz)

        return SunTimes(sunrise=s.get("sunrise"), sunset=s.get("sunset"))  # type: ignore

    except Exception as exc:
        logger.error(
            "Error calculating sun times for %s (lat=%s, lon=%s, tz=%s, date=%s): %s",
            city_name, lat, lon, tz_str, target_date, exc
        )
        return SunTimes(sunrise=None, sunset=None)  # type: ignore
