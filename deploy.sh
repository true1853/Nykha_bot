#!/bin/bash

# FarnPathBot Deployment Script
# Сервер: root@62.181.44.86

set -e

echo "🚀 Начинаем развертывание FarnPathBot..."

# Конфигурация
SERVER="root@62.181.44.86"
APP_DIR="/opt/farnpathbot"
SERVICE_NAME="farnpathbot"

echo "📋 Проверяем подключение к серверу..."
ssh $SERVER "echo '✅ Подключение к серверу успешно'"

echo "🔧 Устанавливаем необходимые пакеты..."
ssh $SERVER "
    apt update && apt install -y python3 python3-pip python3-venv git htop
    echo '✅ Пакеты установлены'
"

echo "📁 Создаем директорию приложения..."
ssh $SERVER "
    mkdir -p $APP_DIR
    cd $APP_DIR
    echo '✅ Директория создана'
"

echo "📦 Копируем файлы проекта..."
# Создаем архив проекта
tar -czf farnpathbot.tar.gz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' .

# Копируем на сервер
scp farnpathbot.tar.gz $SERVER:$APP_DIR/

# Распаковываем на сервере
ssh $SERVER "
    cd $APP_DIR
    tar -xzf farnpathbot.tar.gz
    rm farnpathbot.tar.gz
    echo '✅ Файлы скопированы и распакованы'
"

echo "🐍 Настраиваем Python окружение..."
ssh $SERVER "
    cd $APP_DIR
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo '✅ Python окружение настроено'
"

echo "⚙️ Создаем конфигурационный файл..."
ssh $SERVER "
    cd $APP_DIR
    cat > .env << 'EOF'
# FarnPathBot Configuration
API_TOKEN=your_telegram_bot_token_here
DATABASE_FILE=farnpathbot.db
LOG_LEVEL=INFO
ENABLE_CACHING=true
ENABLE_MONITORING=true
CACHE_TTL=300
DEFAULT_CITY_NAME=Moscow
DEFAULT_LATITUDE=55.7558
DEFAULT_LONGITUDE=37.6173
DEFAULT_TIMEZONE=Europe/Moscow
EOF
    echo '✅ Конфигурационный файл создан'
"

echo "🔧 Создаем systemd сервис..."
ssh $SERVER "
    cat > /etc/systemd/system/$SERVICE_NAME.service << 'EOF'
[Unit]
Description=FarnPathBot - Spiritual Practice Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python main.py
Restart=always
RestartSec=10

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=farnpathbot

[Install]
WantedBy=multi-user.target
EOF
    echo '✅ Systemd сервис создан'
"

echo "🔄 Перезагружаем systemd и запускаем сервис..."
ssh $SERVER "
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME
    systemctl start $SERVICE_NAME
    echo '✅ Сервис запущен'
"

echo "📊 Проверяем статус сервиса..."
ssh $SERVER "
    systemctl status $SERVICE_NAME --no-pager
    echo '✅ Статус проверен'
"

echo "📝 Создаем скрипты управления..."
ssh $SERVER "
    cd $APP_DIR
    
    # Скрипт запуска
    cat > start.sh << 'EOF'
#!/bin/bash
systemctl start $SERVICE_NAME
echo 'FarnPathBot запущен'
EOF
    
    # Скрипт остановки
    cat > stop.sh << 'EOF'
#!/bin/bash
systemctl stop $SERVICE_NAME
echo 'FarnPathBot остановлен'
EOF
    
    # Скрипт перезапуска
    cat > restart.sh << 'EOF'
#!/bin/bash
systemctl restart $SERVICE_NAME
echo 'FarnPathBot перезапущен'
EOF
    
    # Скрипт просмотра логов
    cat > logs.sh << 'EOF'
#!/bin/bash
journalctl -u $SERVICE_NAME -f
EOF
    
    # Скрипт обновления
    cat > update.sh << 'EOF'
#!/bin/bash
cd $APP_DIR
systemctl stop $SERVICE_NAME
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl start $SERVICE_NAME
echo 'FarnPathBot обновлен'
EOF
    
    chmod +x *.sh
    echo '✅ Скрипты управления созданы'
"

echo "🔍 Создаем скрипт мониторинга..."
ssh $SERVER "
    cd $APP_DIR
    cat > monitor.sh << 'EOF'
#!/bin/bash
echo '=== FarnPathBot Status ==='
systemctl is-active $SERVICE_NAME
echo ''
echo '=== Memory Usage ==='
ps aux | grep python | grep farnpathbot
echo ''
echo '=== Disk Usage ==='
du -sh $APP_DIR
echo ''
echo '=== Recent Logs ==='
journalctl -u $SERVICE_NAME --since '5 minutes ago' --no-pager
EOF
    chmod +x monitor.sh
    echo '✅ Скрипт мониторинга создан'
"

echo "🧪 Тестируем развертывание..."
ssh $SERVER "
    cd $APP_DIR
    source venv/bin/activate
    python -c 'import sys; print(f\"Python: {sys.version}\")'
    python -c 'import aiogram; print(f\"Aiogram: {aiogram.__version__}\")'
    echo '✅ Тестирование завершено'
"

echo "📋 Создаем README для сервера..."
ssh $SERVER "
    cd $APP_DIR
    cat > SERVER_README.md << 'EOF'
# FarnPathBot Server

## Управление сервисом

- Запуск: \`./start.sh\`
- Остановка: \`./stop.sh\`
- Перезапуск: \`./restart.sh\`
- Логи: \`./logs.sh\`
- Обновление: \`./update.sh\`
- Мониторинг: \`./monitor.sh\`

## Systemd команды

- Статус: \`systemctl status farnpathbot\`
- Логи: \`journalctl -u farnpathbot -f\`
- Перезапуск: \`systemctl restart farnpathbot\`

## Конфигурация

Файл конфигурации: \`.env\`
Основной файл: \`main.py\`

## Логи

Логи доступны через journalctl:
\`journalctl -u farnpathbot -f\`
EOF
    echo '✅ README для сервера создан'
"

echo "🎉 Развертывание завершено!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте .env файл на сервере:"
echo "   ssh $SERVER 'nano $APP_DIR/.env'"
echo ""
echo "2. Добавьте ваш Telegram Bot Token в .env"
echo ""
echo "3. Перезапустите сервис:"
echo "   ssh $SERVER 'cd $APP_DIR && ./restart.sh'"
echo ""
echo "4. Проверьте статус:"
echo "   ssh $SERVER 'cd $APP_DIR && ./monitor.sh'"
echo ""
echo "5. Просмотр логов:"
echo "   ssh $SERVER 'cd $APP_DIR && ./logs.sh'"
echo ""
echo "🌐 Сервер готов к работе!"
