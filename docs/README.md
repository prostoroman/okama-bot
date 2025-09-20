# Okama Finance Bot v2.0

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Okama 1.5.0](https://img.shields.io/badge/okama-1.5.0-green.svg)](https://pypi.org/project/okama/)
[![Telegram Bot](https://img.shields.io/badge/telegram-bot-blue.svg)](https://core.telegram.org/bots)

Интеллектуальный Telegram бот для финансового анализа портфелей на базе библиотеки Okama v1.5.0 и YandexGPT.

## 🚀 Ключевые возможности

- **Анализ портфелей** - комплексная оценка производительности и рисков
- **Корреляционный анализ** - матрицы корреляции для оптимизации диверсификации
- **Эффективная граница** - поиск оптимальных соотношений риск-доходность
- **Сравнение активов** - детальное сопоставление различных инструментов
- **Пенсионное планирование** - анализ портфелей с учетом инфляции
- **Прогнозирование Монте-Карло** - моделирование будущих сценариев
- **AI-консультации** - финансовые советы от YandexGPT
- **Модульная архитектура** - легко расширяемая система

## 🏗️ Архитектура

Проект использует модульную архитектуру для лучшей производительности и поддержки:

```
okama-bot/
├── okama_service.py         # Главный координатор сервисов
├── correlation_service.py    # Анализ корреляций
├── frontier_service.py       # Эффективная граница
├── comparison_service.py     # Сравнение активов
├── pension_service.py        # Пенсионные портфели
├── monte_carlo_service.py   # Прогнозирование Монте-Карло
├── allocation_service.py     # Анализ распределения активов
├── bot.py                   # Обновленная версия бота
└── requirements.txt          # Зависимости
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
cp config.env.example config.env
# Отредактируйте config.env, добавив ваши API ключи
```

## ⚙️ Конфигурация

Создайте файл `config.env` со следующими параметрами:

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
python test_all_services.py
```

### Тестирование отдельных компонентов
```python
from okama_service import OkamaServiceV2

# Создание сервиса
service = OkamaServiceV2()

# Тест создания портфеля
portfolio = service.create_portfolio(['RGBITR.INDX', 'MCFTR.INDX'])

# Получение метрик
metrics = service.get_portfolio_performance(portfolio)
print(metrics)
```

## 🔍 Поддерживаемые активы

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
python -u bot_v2.py 2>&1 | tee bot.log

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
1. Создайте файл `new_service.py`
2. Реализуйте класс с необходимыми методами
3. Добавьте импорт в `okama_service_v2.py`
4. Инициализируйте сервис в конструкторе
5. Добавьте делегирующие методы

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
