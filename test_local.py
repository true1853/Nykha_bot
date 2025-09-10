#!/usr/bin/env python3
"""
Тестовый скрипт для проверки бота локально
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Устанавливаем переменную окружения
os.environ['API_TOKEN'] = '7527334593:AAEOuwkxS1LzZVBRdnsPMymZuGSaNnPmnfM'

# Добавляем src в Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_bot():
    """Тестируем компоненты бота"""
    try:
        print("🔍 Тестируем импорты...")
        
        # Тест 1: Импорт конфигурации
        from config.config import API_TOKEN
        print(f"✅ API_TOKEN загружен: {API_TOKEN[:10]}...")
        
        # Тест 2: Импорт базы данных
        from database.connection import db_manager
        print("✅ Database manager импортирован")
        
        # Тест 3: Подключение к базе данных
        print("🔍 Тестируем подключение к базе данных...")
        conn = await db_manager.get_connection()
        print("✅ База данных подключена")
        
        # Тест 4: Импорт бота
        from bot.main import main
        print("✅ Bot main импортирован")
        
        print("\n🎉 Все тесты прошли успешно!")
        print("🚀 Бот готов к запуску!")
        
        # Запускаем бота на 10 секунд
        print("\n🤖 Запускаем бота на 10 секунд...")
        await asyncio.wait_for(main(), timeout=10.0)
        
    except asyncio.TimeoutError:
        print("⏰ Тест завершен по таймауту (10 секунд)")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bot())
