# 🚀 Быстрый запуск Okama Finance Bot v2.0

## ⚡ Экспресс-установка

### 1. Клонирование и настройка
```bash
git clone https://github.com/your-username/okama-bot.git
cd okama-bot
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate для Windows
pip install -r requirements.txt
```

### 2. Конфигурация
```bash
cp config_files/config.env.example config_files/config.env
# Отредактируйте config_files/config.env, добавив ваши API ключи
```

### 3. Запуск
```bash
python bot.py
```

## 🔑 Необходимые API ключи

| Сервис | Переменная | Где получить |
|--------|------------|--------------|
| **Telegram Bot** | `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/botfather) |
| **YandexGPT** | `YANDEXGPT_API_KEY` | [Yandex Cloud](https://cloud.yandex.ru/) |
| **YandexGPT** | `YANDEXGPT_FOLDER_ID` | [Yandex Cloud](https://cloud.yandex.ru/) |

## 📱 Основные команды

- `/start` - Запуск бота
- `/portfolio RGBITR.INDX MCFTR.INDX` - Анализ портфеля
- `/risk AGG.US SPY.US` - Анализ рисков
- `/correlation RGBITR.INDX MCFTR.INDX GC.COMM` - Корреляция
- `/help` - Полная справка

## 🧪 Тестирование

```bash
python -m tests.test_all_services
```

## 🆘 Если что-то не работает

1. **Проверьте версию Python**: требуется 3.8+
2. **Активируйте виртуальное окружение**
3. **Проверьте API ключи** в config_files/config.env
4. **Запустите тесты** для диагностики
5. **Используйте команду** `/debug` в боте

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

## 📞 Поддержка

- Команда `/test` - тест интеграции с Okama
- Команда `/testai` - тест YandexGPT API
- Команда `/debug` - отладка данных портфеля

---

**Готово!** 🎉 Ваш бот должен работать и отвечать на команды.
