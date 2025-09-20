# 🚀 Инструкции по запуску Okama Finance Bot v2.0

## ⚡ Быстрый старт (5 минут)

### 1. Активация окружения
```bash
cd okama-bot
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate для Windows
```

### 2. Проверка зависимостей
```bash
pip list | grep okama
# Должно показать: okama 1.5.0
```

### 3. Настройка конфигурации
```bash
cp config_files/config.env.example config_files/config.env
# Отредактируйте config_files/config.env, добавив ваши API ключи
```

### 4. Запуск бота
```bash
python bot.py
```

## 🔑 Необходимые API ключи

| Сервис | Переменная | Где получить |
|--------|------------|--------------|
| **Telegram Bot** | `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/botfather) |
| **YandexGPT** | `YANDEXGPT_API_KEY` | [Yandex Cloud](https://cloud.yandex.ru/) |
| **YandexGPT** | `YANDEXGPT_FOLDER_ID` | [Yandex Cloud](https://cloud.yandex.ru/) |

## 📱 Основные команды бота

- `/start` - Запуск бота
- `/portfolio RGBITR.INDX MCFTR.INDX` - Анализ портфеля
- `/risk AGG.US SPY.US` - Анализ рисков
- `/correlation RGBITR.INDX MCFTR.INDX GC.COMM` - Корреляция
- `/help` - Полная справка

## 🧪 Тестирование

### Быстрая проверка
```bash
python -c "from services.okama_service import OkamaServiceV2; print('✅ OK')"
python -c "from bot import ShansAi; print('✅ OK')"
```

### Полное тестирование
```bash
python -m tests.test_all_services
```

## 🆘 Устранение неполадок

### Проблема: "No module named 'services'"
**Решение**: Убедитесь, что вы находитесь в корневой папке проекта

### Проблема: "ImportError: cannot import name 'Config'"
**Решение**: Используйте `import config` вместо `from config import Config`

### Проблема: "Okama version not compatible"
**Решение**: Проверьте версию: `pip show okama` (должна быть 1.5.0)

## 📁 Структура проекта

```
okama-bot/
├── 📁 services/           # Специализированные сервисы
├── 📁 tests/              # Тестирование
├── 📁 docs/               # Документация
├── 📁 config/             # Конфигурация
├── 📁 scripts/            # Скрипты
├── bot.py                 # Основной файл бота
└── requirements.txt       # Зависимости
```

## 🎯 Команды для разработчиков

### Добавление нового сервиса
```bash
# Создайте файл
touch services/new_service.py

# Добавьте в __init__.py
echo "from .new_service import NewService" >> services/__init__.py
```

### Запуск тестов
```bash
# Все тесты
python -m tests.test_all_services

# Отдельный тест
python tests/test_yandexgpt.py
```

### Обновление зависимостей
```bash
pip install --upgrade -r requirements.txt
```

## 📊 Мониторинг

### Логи бота
```bash
python bot.py 2>&1 | tee bot.log
```

### Проверка состояния
```bash
# В боте используйте команду
/debug RGBITR.INDX MCFTR.INDX
```

## 🚀 Развертывание

### Render (рекомендуется)
```bash
# Файл config/render.yaml уже настроен
# Просто подключите репозиторий к Render
```

### Локальный сервер
```bash
# Используйте screen или tmux для фонового запуска
screen -S okama-bot
python bot.py
# Ctrl+A, D для отключения
```

## 📞 Поддержка

- **Команда `/testai`** - тест YandexGPT API
- **Команда `/debug`** - отладка данных портфеля

---

**Статус**: ✅ Готов к запуску  
**Время настройки**: ~5 минут  
**Совместимость**: Python 3.8+, Okama 1.5.0
