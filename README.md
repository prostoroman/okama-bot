# 🧠 Okama Financial Brain v3.0

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
│   ├── okama_service.py           # Главный координатор сервисов
│   ├── correlation_service.py     # Анализ корреляций
│   ├── frontier_service.py        # Эффективная граница
│   ├── comparison_service.py      # Сравнение активов
│   ├── pension_service.py         # Пенсионные портфели
│   ├── monte_carlo_service.py     # Прогнозирование Монте-Карло
│   └── allocation_service.py      # Анализ распределения активов
├── 📁 tests/                       # Тестирование
│   ├── __init__.py                # Пакет тестов
│   ├── test_all_services.py       # Комплексное тестирование
│   ├── test_okama_formatting.py   # Тесты форматирования
│   └── test_yandexgpt.py          # Тесты YandexGPT
├── 📁 docs/                        # Документация
│   ├── README.md                  # Основная документация
│   ├── 🧠 README_FINANCIAL_BRAIN.md # **Документация Financial Brain**
│   ├── QUICK_START.md             # Быстрый старт
│   ├── README_MODULAR.md          # Модульная структура
│   ├── CHANGELOG.md               # Журнал изменений
│   ├── FINAL_REPORT.md            # Финальный отчет
│   └── RENAMING_INFO.md           # Информация о переименовании
├── 📁 config_files/                # Конфигурационные файлы
│   ├── __init__.py                # Пакет конфигурации
│   ├── config.env.example         # Шаблон переменных окружения
│   ├── render.yaml                # Конфигурация Render
│   └── runtime.txt                # Версия Python
├── 📁 scripts/                     # Скрипты
│   ├── __init__.py                # Пакет скриптов
│   └── deploy.sh                  # Скрипт развертывания
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

### 5. Тестирование Financial Brain
```bash
python test_financial_brain.py
```

## ⚙️ Конфигурация

Создайте файл `config_files/config.env` со следующими параметрами:

```env
# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# YandexGPT API
YANDEXGPT_API_KEY=your_yandexgpt_api_key
YANDEXGPT_FOLDER_ID=your_folder_id
YANDEXGPT_BASE_URL=https://llm.api.cloud.yandex.net/foundationModels/v1
```

## 🚀 Запуск

### Запуск бота
```bash
python bot.py
```

### Тестирование
```bash
python -m tests.test_all_services
```

## 📱 Использование

### Основные команды

| Команда | Описание | Пример |
|---------|----------|---------|
| `/start` | Запуск бота | `/start` |
| `/help` | Справка по командам | `/help` |
| `/portfolio` | Анализ портфеля | `/portfolio RGBITR.INDX MCFTR.INDX` |
| `/risk` | Анализ рисков | `/risk AGG.US SPY.US` |
| `/correlation` | Корреляция активов | `/correlation RGBITR.INDX MCFTR.INDX GC.COMM` |
| `/efficient_frontier` | Эффективная граница | `/efficient_frontier RGBITR.INDX MCFTR.INDX` |
| `/compare` | Сравнение активов | `/compare AGG.US SPY.US GC.COMM` |
| `/pension` | Пенсионный портфель | `/pension RGBITR.INDX MCFTR.INDX 0.6 0.4 1000000 -50000 year` |
| `/monte_carlo` | Прогнозирование | `/monte_carlo AGG.US SPY.US 20 100 norm` |
| `/allocation` | Распределение активов | `/allocation RGBITR.INDX MCFTR.INDX GC.COMM` |

### Естественный язык

Бот понимает запросы на естественном языке:

- "Проанализируй мой портфель AGG.US SPY.US"
- "Какой риск у GC.COMM?"
- "Сравни RGBITR.INDX с MCFTR.INDX"
- "Как оптимизировать мой портфель?"

## 🔧 Тестирование

### Запуск всех тестов
```bash
python -m tests.test_all_services
```

### Тестирование отдельных компонентов
```python
from services.okama_service import OkamaServiceV2

# Создание сервиса
service = OkamaServiceV2()

# Тест создания портфеля
portfolio = service.create_portfolio(['RGBITR.INDX', 'MCFTR.INDX'])

# Получение метрик
metrics = service.get_portfolio_performance(portfolio)
print(metrics)
```

## 📊 Поддерживаемые активы

### Российские индексы
- `RGBITR.INDX` - Индекс МосБиржи
- `MCFTR.INDX` - Индекс Московской биржи

### Американские ETF
- `AGG.US` - Aggregate Bond ETF
- `SPY.US` - S&P 500 ETF
- `QQQ.US` - NASDAQ-100 ETF

### Товары
- `GC.COMM` - Золото
- `SI.COMM` - Серебро
- `CL.COMM` - Нефть

### Валюты
- `USD.RUB` - Доллар США к рублю
- `EUR.USD` - Евро к доллару США

## 📈 Метрики производительности

- **Total Return** - Общая доходность
- **Annual Return** - Годовая доходность
- **Volatility** - Волатильность
- **Sharpe Ratio** - Коэффициент Шарпа
- **Sortino Ratio** - Коэффициент Сортино
- **Max Drawdown** - Максимальная просадка
- **VaR (95%)** - Value at Risk
- **CVaR (95%)** - Conditional Value at Risk

## 🎯 Особенности v2.0

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
   - Используйте поддерживаемые форматы: `.INDX`, `.US`, `.COMM`

3. **"Insufficient data for analysis"**
   - Решение: Убедитесь в достаточности исторических данных
   - Попробуйте другие символы

### Логи и отладка
```bash
# Включение подробного логирования
export PYTHONPATH=.
python -u bot.py 2>&1 | tee bot.log

# Использование команды отладки в боте
/debug RGBITR.INDX MCFTR.INDX
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
4. Обновите `services/okama_service.py`

### Структура сервиса
```python
class NewService:
    def __init__(self):
        # Инициализация
        
    def main_method(self, *args):
        # Основная логика
        
    def _helper_method(self, *args):
        # Вспомогательные методы
        
    def _create_error_chart(self, error_message: str) -> bytes:
        # Обработка ошибок
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
2. Используйте команды отладки (`/debug`, `/test`)
3. Убедитесь в совместимости версий
4. Проверьте доступность API сервисов

### Полезные команды отладки
- `/test [symbols]` - Тест интеграции с Okama
- `/testai` - Тест подключения к YandexGPT
- `/debug [symbols]` - Отладка данных портфеля

## 🎉 Благодарности

- [Okama](https://github.com/mbk-dev/okama) - Библиотека для финансового анализа
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API
- [YandexGPT](https://cloud.yandex.ru/services/yandexgpt) - AI-консультации

---

**Okama Finance Bot v2.0** - Ваш интеллектуальный помощник в мире финансов! 🚀📊
