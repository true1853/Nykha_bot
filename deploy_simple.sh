#!/bin/bash

# Простой скрипт развертывания FarnPathBot
# Использование: ./deploy_simple.sh

echo "🚀 Простое развертывание FarnPathBot"
echo "=================================="

# Создаем архив проекта
echo "📦 Создаем архив проекта..."
tar -czf farnpathbot.tar.gz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' --exclude='deploy*.sh' .

echo "✅ Архив создан: farnpathbot.tar.gz"
echo ""
echo "📋 Инструкции для развертывания на сервере:"
echo "=========================================="
echo ""
echo "1. Скопируйте архив на сервер:"
echo "   scp farnpathbot.tar.gz root@62.181.44.86:/opt/"
echo ""
echo "2. Подключитесь к серверу:"
echo "   ssh root@62.181.44.86"
echo ""
echo "3. Выполните команды на сервере:"
echo "   cd /opt"
echo "   tar -xzf farnpathbot.tar.gz"
echo "   mv farnpathbot/* ."
echo "   rm -rf farnpathbot farnpathbot.tar.gz"
echo ""
echo "4. Установите зависимости:"
echo "   apt update && apt install -y python3 python3-pip python3-venv"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""
echo "5. Создайте .env файл:"
echo "   nano .env"
echo "   # Добавьте ваш API_TOKEN"
echo ""
echo "6. Запустите бота:"
echo "   python main.py"
echo ""
echo "🌐 Готово! Бот будет работать на сервере."
