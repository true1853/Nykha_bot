# 🚀 Руководство по развертыванию FarnPathBot

## 📋 Требования

### Системные требования
- Python 3.8+
- SQLite 3
- 512MB RAM (минимум)
- 1GB свободного места на диске

### Зависимости
- aiogram 3.0+
- aiosqlite
- geopy
- astral
- APScheduler

## 🔧 Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd FarnPathBot
```

### 2. Создание виртуального окружения

```bash
# Linux/macOS
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка окружения

Создайте файл `.env`:

```env
# Обязательные настройки
API_TOKEN=your_telegram_bot_token

# Настройки базы данных
DATABASE_FILE=farnpathbot.db

# Настройки производительности
ENABLE_CACHING=true
ENABLE_MONITORING=true
CACHE_TTL=300

# Настройки логирования
LOG_LEVEL=INFO

# Настройки по умолчанию
DEFAULT_CITY_NAME=Moscow
DEFAULT_LATITUDE=55.7558
DEFAULT_LONGITUDE=37.6173
DEFAULT_TIMEZONE=Europe/Moscow
```

## 🐳 Docker развертывание

### 1. Создание Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY main.py .

CMD ["python", "main.py"]
```

### 2. Создание docker-compose.yml

```yaml
version: '3.8'

services:
  farnpathbot:
    build: .
    environment:
      - API_TOKEN=${API_TOKEN}
      - DATABASE_FILE=/app/data/farnpathbot.db
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

### 3. Запуск

```bash
docker-compose up -d
```

## ☁️ Облачное развертывание

### Heroku

1. Создайте `Procfile`:
```
worker: python main.py
```

2. Настройте переменные окружения в Heroku Dashboard

3. Деплой:
```bash
git push heroku main
```

### DigitalOcean App Platform

1. Создайте `app.yaml`:
```yaml
name: farnpathbot
services:
- name: bot
  source_dir: /
  github:
    repo: your-username/FarnPathBot
    branch: main
  run_command: python main.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: API_TOKEN
    value: ${API_TOKEN}
```

### AWS EC2

1. Создайте EC2 инстанс (Ubuntu 20.04+)

2. Установите зависимости:
```bash
sudo apt update
sudo apt install python3-pip python3-venv git
```

3. Клонируйте и настройте:
```bash
git clone <repository-url>
cd FarnPathBot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. Создайте systemd сервис:
```bash
sudo nano /etc/systemd/system/farnpathbot.service
```

```ini
[Unit]
Description=FarnPathBot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/FarnPathBot
Environment=PATH=/home/ubuntu/FarnPathBot/venv/bin
ExecStart=/home/ubuntu/FarnPathBot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

5. Запустите сервис:
```bash
sudo systemctl enable farnpathbot
sudo systemctl start farnpathbot
```

## 🔒 Безопасность

### 1. Переменные окружения

Никогда не коммитьте `.env` файл:
```bash
echo ".env" >> .gitignore
```

### 2. Firewall

Настройте firewall для ограничения доступа:
```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 3. SSL/TLS

Для Mini App используйте HTTPS:
```bash
# Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com
```

## 📊 Мониторинг

### 1. Логирование

Настройте ротацию логов:
```bash
# logrotate
sudo nano /etc/logrotate.d/farnpathbot
```

```
/home/ubuntu/FarnPathBot/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
}
```

### 2. Мониторинг системы

Установите htop для мониторинга:
```bash
sudo apt install htop
htop
```

### 3. Health checks

Создайте скрипт проверки:
```bash
#!/bin/bash
# health_check.sh

if pgrep -f "python main.py" > /dev/null; then
    echo "Bot is running"
    exit 0
else
    echo "Bot is not running"
    exit 1
fi
```

## 🔄 Обновления

### 1. Graceful restart

```bash
# Остановка
sudo systemctl stop farnpathbot

# Обновление кода
git pull origin main

# Запуск
sudo systemctl start farnpathbot
```

### 2. Zero-downtime deployment

```bash
# Создайте скрипт обновления
#!/bin/bash
# update.sh

# Создайте backup
cp farnpathbot.db farnpathbot.db.backup.$(date +%Y%m%d_%H%M%S)

# Обновите код
git pull origin main

# Перезапустите сервис
sudo systemctl restart farnpathbot

# Проверьте статус
sudo systemctl status farnpathbot
```

## 🐛 Отладка

### 1. Логи

```bash
# Просмотр логов
sudo journalctl -u farnpathbot -f

# Логи за последний час
sudo journalctl -u farnpathbot --since "1 hour ago"
```

### 2. Проверка базы данных

```bash
# SQLite
sqlite3 farnpathbot.db
.tables
.schema users
```

### 3. Тестирование

```bash
# Запуск в тестовом режиме
python main.py --test

# Запуск тестов
pytest tests/
```

## 📈 Масштабирование

### 1. Горизонтальное масштабирование

Для больших нагрузок рассмотрите:
- Redis для кэширования
- PostgreSQL вместо SQLite
- Load balancer для Mini App

### 2. Вертикальное масштабирование

Увеличьте ресурсы сервера:
- CPU: 2+ cores
- RAM: 2GB+
- Storage: SSD

## 🆘 Устранение неполадок

### Частые проблемы

1. **Bot не запускается**
   - Проверьте API_TOKEN
   - Проверьте права доступа к файлам
   - Проверьте логи

2. **Ошибки базы данных**
   - Проверьте права доступа к файлу БД
   - Проверьте свободное место на диске
   - Создайте backup и пересоздайте БД

3. **Высокое использование памяти**
   - Включите мониторинг
   - Проверьте утечки памяти
   - Перезапустите бота

### Контакты поддержки

- GitHub Issues: [ссылка на репозиторий]
- Email: support@farnpathbot.com
- Telegram: @farnpathbot_support

---

*Удачного развертывания!* 🚀
