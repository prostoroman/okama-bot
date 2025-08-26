# 🧠 Okama Financial Brain v3.x

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Okama 1.5.0](https://img.shields.io/badge/okama-1.5.0-green.svg)](https://pypi.org/project/okama/)
[![Telegram Bot](https://img.shields.io/badge/telegram-bot-blue.svg)](https://core.telegram.org/bots)
[![AI Powered](https://img.shields.io/badge/AI-Powered-orange.svg)](https://yandex.ru/ai/)

**Ядро интеллектуальной системы для финансового анализа** - революционная система, которая управляет полным циклом обработки запроса пользователя: от анализа текста до генерации аналитических выводов.

## 🚀 Ключевые возможности

### 🧠 Интеллектуальный анализ
- **Автоматическое распознавание намерений** - понимаю, что вы хотите
- **Естественный язык** - пишите запросы как общаетесь с человеком
- **AI-аналитика** - интеллектуальные выводы и рекомендации

### 📊 Финансовый анализ
- **Анализ активов** - полная информация по одному активу
- **Сравнение активов** - сопоставление нескольких инструментов
- **Анализ портфеля** - оптимизация и оценка рисков
- **Макроэкономический анализ** - валюты, сырье, индексы
- **Анализ инфляции** - данные по инфляции в разных странах

### 🔧 Автоматизация
- **Нормализация активов** - перевожу названия в тикеры Okama
- **Построение отчетов** - создаю аналитические таблицы
- **Генерация графиков** - визуализирую данные
- **Оптимизация весов** - автоматически распределяю веса портфеля

### 🎯 Специализированные функции
- **Корреляционный анализ** - матрицы корреляции для диверсификации
- **Эффективная граница** - поиск оптимальных соотношений риск-доходность
- **Пенсионное планирование** - анализ с учетом инфляции
- **Прогнозирование Монте-Карло** - моделирование будущих сценариев

## 🏗️ Архитектура проекта

Проект использует модульную архитектуру для лучшей производительности и поддержки:

```
okama-bot/
├── 📁 services/                    # Специализированные сервисы
│   ├── __init__.py                # Пакет сервисов
│   ├── 🧠 financial_brain.py      # **Ядро интеллектуальной системы**
│   ├── okama_handler_enhanced.py  # Обработка данных Okama
│   ├── asset_service.py           # Работа с данными активов
│   ├── intent_parser_enhanced.py  # Парсинг намерений
│   ├── asset_resolver_enhanced.py # Нормализация активов
│   ├── report_builder_enhanced.py # Формирование отчетов
│   ├── analysis_engine_enhanced.py# AI-выводы по результатам
│   └── financial_brain_enhanced.py# Высокоуровневый пайплайн
├── 📁 docs/                        # Документация
├── 📁 config_files/                # Конфигурационные файлы
├── 📁 scripts/                     # Скрипты
├── bot.py                          # Основной файл бота
├── config.py                       # Управление конфигурацией
├── yandexgpt_service.py            # Сервис YandexGPT
├── requirements.txt                # Зависимости Python
└── .gitignore                      # Исключения Git
```

## 💡 Примеры использования

### 🧠 Естественный язык (рекомендуется!)

**Анализ активов:**
```
"Проанализируй Apple"
"Информация о Tesla"
"Покажи данные по SBER.MOEX"
```

**Сравнение активов:**
```
"Сравни Apple и Microsoft"
"Что лучше: VOO.US или SPY.US?"
"Сопоставь золото и серебро"
```

**Анализ портфеля:**
```
"Портфель из VOO.US и AGG.US"
"Оптимизируй портфель с весами 60% акции, 40% облигации"
"Анализ рисков портфеля"
```

**Макроэкономический анализ:**
```
"Сравни S&P 500 и NASDAQ"
"Анализ валютных пар"
"Динамика цен на нефть и золото"
```

**Анализ инфляции:**
```
"Инфляция в США за последние 5 лет"
"CPI данные по России"
"Тренды инфляции в Европе"
```

### 🔧 Традиционные команды

```
/asset VOO.US          # Информация об активе
/price SPY.US          # Текущая цена
/dividends AGG.US      # История дивидендов
/chat [вопрос]         # AI-советник
/test VOO.US           # Тест Okama
/testai                # Тест YandexGPT
```

## 📦 Установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-username/okama-bot.git
cd okama-bot
```

### 2. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка конфигурации
```bash
cp config_files/config.env.example config_files/config.env
# Отредактируйте config_files/config.env, добавив ваши API ключи
```

## ⚙️ Конфигурация

Создайте файл `config_files/config.env` со следующими параметрами:

```env
# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# YandexGPT API
YANDEX_API_KEY=your_yandexgpt_api_key
YANDEX_FOLDER_ID=your_folder_id

# Дополнительно
OKAMA_API_KEY=optional_okama_api_key
```

> Примечание: `config.py` использует переменные `YANDEX_API_KEY` и `YANDEX_FOLDER_ID`. Ранее используемые `YANDEXGPT_*` больше не применяются.

## 🚀 Запуск

### Запуск бота
```bash
python bot.py
```

### Проверка интеграций
```bash
# Проверка Okama
/chat Что такое диверсификация?
/test VOO.US

# Проверка YandexGPT
/testai
```

## 📱 Использование

### Основные команды

| Команда | Описание | Пример |
|---------|----------|---------|
| `/start` | Запуск бота | `/start` |
| `/help` | Справка по командам | `/help` |
| `/asset` | Информация об активе | `/asset VOO.US` |
| `/price` | Текущая цена актива | `/price SPY.US` |
| `/dividends` | История дивидендов | `/dividends AGG.US` |
| `/chat` | AI-советник | `/chat What is Sharpe ratio?` |
| `/test` | Тест Okama интеграции | `/test VOO.US` |
| `/testai` | Тест YandexGPT интеграции | `/testai` |

### Естественный язык

Бот понимает запросы на естественном языке:

- "Проанализируй мой портфель AGG.US SPY.US"
- "Какой риск у XAU.COMM?"
- "Сравни SPX.INDX с IXIC.INDX"
- "Как оптимизировать мой портфель?"

## 📊 Поддерживаемые активы

### Российские индексы
- `RGBITR.INDX` - Индекс МосБиржи
- `MCFTR.INDX` - Индекс Московской биржи

### Американские ETF
- `AGG.US` - Aggregate Bond ETF
- `SPY.US` - S&P 500 ETF
- `QQQ.US` - NASDAQ-100 ETF

### Товары
- `XAU.COMM` - Золото
- `XAG.COMM` - Серебро
- `BRENT.COMM` - Нефть

### Валюты
- `USD.RUB` - Доллар США к рублю
- `EURUSD.FX` - Евро к доллару США

## 📈 Метрики производительности

- **Total Return** - Общая доходность
- **Annual Return** - Годовая доходность
- **Volatility** - Волатильность
- **Sharpe Ratio** - Коэффициент Шарпа
- **Sortino Ratio** - Коэффициент Сортино
- **Max Drawdown** - Максимальная просадка
- **VaR (95%)** - Value at Risk
- **CVaR (95%)** - Conditional Value at Risk

## 🎯 Особенности v3.x

### 1. Совместимость с Okama v1.5.0
- Использование актуальных методов API
- Корректная работа с новыми атрибутами
- Поддержка `inflation=True`

### 2. Модульная архитектура
- Разделение функциональности по сервисам
- Легкое добавление новых возможностей
- Улучшенная производительность

### 3. Обработка ошибок
- Fallback механизмы
- Информативные сообщения
- Graceful degradation

### 4. Оптимизация для лимитов
- Разбиение больших запросов
- Эффективное использование памяти
- Кэширование результатов

## 🐛 Устранение неполадок

### Частые ошибки

1. **"Real Return is not defined"**
   - Решение: Добавьте `inflation=True` при создании портфеля

2. **"No price data found"**
   - Решение: Проверьте правильность символов
   - Используйте поддерживаемые форматы: `.INDX`, `.US`, `.COMM`, `.FX`

3. **"Insufficient data for analysis"**
   - Решение: Убедитесь в достаточности исторических данных
   - Попробуйте другие символы

### Логи и отладка
```bash
# Включение подробного логирования
export PYTHONPATH=.
python -u bot.py 2>&1 | tee bot.log

# Использование команд отладки в боте
/test VOO.US
/testai
```

## 🔄 Обновления

### Обновление Okama
```bash
pip install --upgrade okama
```

### Обновление зависимостей
```bash
pip install --upgrade -r requirements.txt
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

### Добавление нового сервиса
1. Создайте файл `services/new_service.py`
2. Реализуйте класс с необходимыми методами
3. Добавьте импорт в `services/__init__.py`
4. Обновите `services/okama_handler_enhanced.py` или интеграцию в `financial_brain_enhanced.py`

### Структура сервиса
```python
class NewService:
    def __init__(self):
        pass
    def main_method(self, *args):
        pass
    def _helper_method(self, *args):
        pass
    def _create_error_chart(self, error_message: str) -> bytes:
        pass
```

## 📚 Документация

Подробная документация находится в папке [docs/readme/](docs/readme/):
- [Индекс документации](docs/readme/README_INDEX.md) - Обзор всей документации
- [Быстрый старт](docs/readme/OPTIMIZED_QUICK_START.md) - Быстрый запуск бота
- [Руководство по развертыванию](docs/readme/DEPLOYMENT_GUIDE.md) - Развертывание на любой платформе
- [Структура проекта](docs/readme/PROJECT_STRUCTURE.md) - Архитектура кода
- [Отчет об оптимизации](docs/readme/OPTIMIZATION_REPORT.md) - Улучшения производительности

## 📄 Лицензия

Проект использует те же лицензии, что и оригинальные библиотеки:
- Okama: [MIT License](https://github.com/mbk-dev/okama/blob/master/LICENSE)
- python-telegram-bot: [GPL-3.0](https://github.com/python-telegram-bot/python-telegram-bot/blob/master/LICENSE)

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи бота
2. Используйте команды отладки (`/test`, `/testai`)
3. Убедитесь в совместимости версий
4. Проверьте доступность API сервисов

## 🎉 Благодарности

- [Okama](https://github.com/mbk-dev/okama) - Библиотека для финансового анализа
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API
- [YandexGPT](https://cloud.yandex.ru/services/yandexgpt) - AI-консультации

---

**Okama Finance Bot v3.x** - Ваш интеллектуальный помощник в мире финансов! 🚀📊
