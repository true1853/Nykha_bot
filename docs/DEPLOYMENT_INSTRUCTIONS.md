# 🚀 Инструкции по развертыванию FarnPathBot

## 📋 Подготовка

### 1. Архив создан
✅ Файл `farnpathbot.tar.gz` готов для развертывания

### 2. Размер архива
```bash
ls -lh farnpathbot.tar.gz
```

## 🌐 Развертывание на сервере

### Шаг 1: Копирование на сервер
```bash
scp farnpathbot.tar.gz root@62.181.44.86:/opt/
```

### Шаг 2: Подключение к серверу
```bash
ssh root@62.181.44.86
```

### Шаг 3: Распаковка проекта
```bash
cd /opt
tar -xzf farnpathbot.tar.gz
mv farnpathbot/* .
rm -rf farnpathbot farnpathbot.tar.gz
ls -la
```

### Шаг 4: Установка зависимостей
```bash
# Обновляем систему
apt update

# Устанавливаем Python и необходимые пакеты
apt install -y python3 python3-pip python3-venv build-essential

# Создаем виртуальное окружение
python3 -m venv venv

# Активируем окружение
source venv/bin/activate

# Устанавливаем зависимости
pip install --upgrade pip
pip install -r requirements.txt
```

### Шаг 5: Настройка конфигурации
```bash
# Создаем .env файл
nano .env
```

Содержимое `.env` файла:
```env
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
```

### Шаг 6: Тестирование
```bash
# Проверяем, что все работает
python main.py --help
```

### Шаг 7: Запуск в фоне
```bash
# Запускаем бота в фоне
nohup python main.py > bot.log 2>&1 &

# Проверяем, что процесс запущен
ps aux | grep python
```

## 🔧 Создание systemd сервиса

### Создание сервиса
```bash
nano /etc/systemd/system/farnpathbot.service
```

Содержимое файла:
```ini
[Unit]
Description=FarnPathBot - Spiritual Practice Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt
Environment=PATH=/opt/venv/bin
ExecStart=/opt/venv/bin/python main.py
Restart=always
RestartSec=10

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=farnpathbot

[Install]
WantedBy=multi-user.target
```

### Активация сервиса
```bash
# Перезагружаем systemd
systemctl daemon-reload

# Включаем автозапуск
systemctl enable farnpathbot

# Запускаем сервис
systemctl start farnpathbot

# Проверяем статус
systemctl status farnpathbot
```

## 📊 Мониторинг

### Просмотр логов
```bash
# Логи сервиса
journalctl -u farnpathbot -f

# Логи за последний час
journalctl -u farnpathbot --since "1 hour ago"

# Логи приложения
tail -f bot.log
```

### Управление сервисом
```bash
# Запуск
systemctl start farnpathbot

# Остановка
systemctl stop farnpathbot

# Перезапуск
systemctl restart farnpathbot

# Статус
systemctl status farnpathbot
```

### Мониторинг ресурсов
```bash
# Использование памяти
htop

# Использование диска
df -h

# Процессы Python
ps aux | grep python
```

## 🔄 Обновление

### Обновление кода
```bash
# Останавливаем сервис
systemctl stop farnpathbot

# Создаем backup
cp farnpathbot.db farnpathbot.db.backup.$(date +%Y%m%d_%H%M%S)

# Обновляем код (если используете git)
git pull origin main

# Или копируем новый архив
# scp farnpathbot.tar.gz root@62.181.44.86:/opt/
# tar -xzf farnpathbot.tar.gz

# Обновляем зависимости
source venv/bin/activate
pip install -r requirements.txt

# Запускаем сервис
systemctl start farnpathbot
```

## 🛠️ Скрипты управления

### Создание скриптов
```bash
cd /opt

# Скрипт запуска
cat > start.sh << 'EOF'
#!/bin/bash
systemctl start farnpathbot
echo "FarnPathBot запущен"
EOF

# Скрипт остановки
cat > stop.sh << 'EOF'
#!/bin/bash
systemctl stop farnpathbot
echo "FarnPathBot остановлен"
EOF

# Скрипт перезапуска
cat > restart.sh << 'EOF'
#!/bin/bash
systemctl restart farnpathbot
echo "FarnPathBot перезапущен"
EOF

# Скрипт логов
cat > logs.sh << 'EOF'
#!/bin/bash
journalctl -u farnpathbot -f
EOF

# Скрипт мониторинга
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== FarnPathBot Status ==="
systemctl is-active farnpathbot
echo ""
echo "=== Memory Usage ==="
ps aux | grep python | grep farnpathbot
echo ""
echo "=== Disk Usage ==="
du -sh /opt
echo ""
echo "=== Recent Logs ==="
journalctl -u farnpathbot --since '5 minutes ago' --no-pager
EOF

# Делаем скрипты исполняемыми
chmod +x *.sh
```

### Использование скриптов
```bash
# Запуск
./start.sh

# Остановка
./stop.sh

# Перезапуск
./restart.sh

# Логи
./logs.sh

# Мониторинг
./monitor.sh
```

## 🔍 Отладка

### Проверка конфигурации
```bash
# Проверяем .env файл
cat .env

# Проверяем зависимости
source venv/bin/activate
pip list
```

### Тестирование
```bash
# Тест импортов
python -c "import src.bot.main; print('Импорты OK')"

# Тест конфигурации
python -c "from src.config.config import API_TOKEN; print('Config OK')"
```

### Логи ошибок
```bash
# Детальные логи
journalctl -u farnpathbot -l

# Логи с временными метками
journalctl -u farnpathbot --since "today"
```

## 📈 Производительность

### Оптимизация
```bash
# Мониторинг памяти
free -h

# Мониторинг CPU
top

# Мониторинг диска
iostat -x 1
```

### Настройка логирования
```bash
# Ротация логов
nano /etc/logrotate.d/farnpathbot
```

Содержимое:
```
/opt/bot.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
}
```

## 🆘 Устранение неполадок

### Частые проблемы

1. **Сервис не запускается**
   ```bash
   systemctl status farnpathbot
   journalctl -u farnpathbot --since "1 hour ago"
   ```

2. **Ошибки импорта**
   ```bash
   source venv/bin/activate
   python -c "import sys; print(sys.path)"
   ```

3. **Проблемы с правами**
   ```bash
   chown -R root:root /opt
   chmod +x /opt/*.sh
   ```

4. **Проблемы с базой данных**
   ```bash
   ls -la farnpathbot.db
   sqlite3 farnpathbot.db ".tables"
   ```

## ✅ Проверка развертывания

### Финальная проверка
```bash
# Статус сервиса
systemctl status farnpathbot

# Логи
journalctl -u farnpathbot --since "1 minute ago"

# Процессы
ps aux | grep python

# Порт (если используется)
netstat -tlnp | grep python
```

### Тест функциональности
1. Отправьте `/start` боту в Telegram
2. Проверьте ответ
3. Протестируйте основные функции

## 🎉 Готово!

Бот успешно развернут и готов к работе!

### Полезные команды
```bash
# Быстрый статус
systemctl status farnpathbot

# Быстрые логи
journalctl -u farnpathbot -n 20

# Перезапуск
systemctl restart farnpathbot
```

---

*Удачного развертывания!* 🚀
