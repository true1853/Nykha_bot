# 🔑 Настройка токена Telegram бота

## ❌ Проблема
FarnPathBot не работает, потому что не настроен API_TOKEN.

## ✅ Решение

### 1. Получите токен бота
1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot` или `/mybots`
3. Выберите вашего бота
4. Скопируйте токен (формат: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Настройте токен на сервере

#### Вариант A: Через SSH (рекомендуется)
```bash
# Подключитесь к серверу
ssh root@62.181.44.86

# Отредактируйте конфигурацию
cd /opt
nano .env

# Замените строку:
API_TOKEN=your_telegram_bot_token_here
# На:
API_TOKEN=ваш_реальный_токен_здесь

# Сохраните файл (Ctrl+X, Y, Enter)

# Перезапустите сервис
systemctl restart farnpathbot

# Проверьте статус
systemctl status farnpathbot
```

#### Вариант B: Через команды
```bash
# Замените YOUR_BOT_TOKEN на ваш реальный токен
ssh root@62.181.44.86 "cd /opt && sed -i 's/your_telegram_bot_token_here/YOUR_BOT_TOKEN/g' .env && systemctl restart farnpathbot"
```

### 3. Проверьте работу
```bash
# Проверьте статус
ssh root@62.181.44.86 "systemctl status farnpathbot"

# Проверьте логи
ssh root@62.181.44.86 "journalctl -u farnpathbot --since '1 minute ago'"

# Протестируйте бота
# Отправьте /start вашему боту в Telegram
```

## 🔍 Диагностика

### Если бот все еще не работает:

1. **Проверьте токен:**
```bash
ssh root@62.181.44.86 "cd /opt && cat .env | grep API_TOKEN"
```

2. **Проверьте формат токена:**
   - Должен быть в формате: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
   - Без пробелов и лишних символов

3. **Проверьте логи:**
```bash
ssh root@62.181.44.86 "journalctl -u farnpathbot -f"
```

4. **Ручной запуск для отладки:**
```bash
ssh root@62.181.44.86 "cd /opt && source venv/bin/activate && PYTHONPATH=/opt python main.py"
```

## 🚀 После настройки токена

Бот должен:
- ✅ Запуститься без ошибок
- ✅ Отвечать на команду `/start`
- ✅ Показывать главное меню
- ✅ Работать все функции

## 📞 Поддержка

Если проблемы остаются:
1. Проверьте правильность токена
2. Убедитесь, что бот не заблокирован
3. Проверьте интернет-соединение сервера
4. Посмотрите логи на ошибки

---

**🔑 Настройте токен, и бот заработает!**
