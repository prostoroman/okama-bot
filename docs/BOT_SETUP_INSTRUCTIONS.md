# Инструкция по настройке Okama Finance Bot

## Быстрая настройка

### 1. Создайте файл конфигурации
Скопируйте `config_files/config.env.example` в `config.env` и заполните:

```bash
# Telegram Bot Token (получите у @BotFather)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# YandexGPT API (получите на https://cloud.yandex.com/)
YANDEX_API_KEY=your_yandex_api_key_here
YANDEX_FOLDER_ID=your_yandex_folder_id_here

# Настройки бота
BOT_USERNAME=your_bot_username
BOT_FULL_NAME=@your_bot_username
ADMIN_USER_ID=your_telegram_user_id
```

### 2. Важные моменты настройки ссылок

**BOT_FULL_NAME** - это имя вашего бота для ссылок:
- ✅ Правильно: `@okama_finance_bot`
- ❌ Неправильно: `okama_finance_bot` (без @)

**BOT_USERNAME** - имя бота без символа @:
- ✅ Правильно: `okama_finance_bot`
- ❌ Неправильно: `@okama_finance_bot` (с @)

### 3. Примеры настроек

#### Для бота @okama_finance_bot:
```bash
BOT_USERNAME=okama_finance_bot
BOT_FULL_NAME=@okama_finance_bot
```

#### Для бота @my_finance_bot:
```bash
BOT_USERNAME=my_finance_bot
BOT_FULL_NAME=@my_finance_bot
```

### 4. Проверка настроек

После настройки все ссылки будут автоматически формироваться в формате:
- `https://t.me/okama_finance_bot?start=info`
- `https://t.me/okama_finance_bot?start=namespace`
- `https://t.me/okama_finance_bot?start=info_AAPL`

### 5. Запуск бота

```bash
python bot.py
```

## Устранение проблем

### Проблема: Ссылки не работают
**Решение**: Проверьте, что `BOT_FULL_NAME` начинается с `@`

### Проблема: Бот не запускается
**Решение**: Убедитесь, что заполнены все обязательные переменные:
- `TELEGRAM_BOT_TOKEN`
- `YANDEX_API_KEY`
- `YANDEX_FOLDER_ID`

### Проблема: Кнопки не отображаются
**Решение**: Проверьте, что `BOT_FULL_NAME` указан правильно

## Поддержка

Если у вас возникли проблемы:
1. Проверьте логи бота
2. Убедитесь, что все переменные окружения заполнены
3. Проверьте формат `BOT_FULL_NAME` (должен начинаться с `@`)
