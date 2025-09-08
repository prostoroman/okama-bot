# 🧠 shans.ai

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Okama 1.5.0](https://img.shields.io/badge/okama-1.5.0-green.svg)](https://pypi.org/project/okama/)
[![Telegram Bot](https://img.shields.io/badge/telegram-bot-blue.svg)](https://core.telegram.org/bots)
[![AI Powered](https://img.shields.io/badge/AI-Powered-orange.svg)](https://yandex.ru/ai/)
[![Multi-Exchange](https://img.shields.io/badge/multi--exchange-green.svg)](https://tushare.pro/)


## 🌟 Обзор функциональности

### 🤖 Основные команды бота

| Команда | Описание | Пример использования |
|---------|----------|---------------------|
| `/start` | Запуск бота и получение справки | `/start` |
| `/info [символ]` | Детальная информация об активе с графиками и AI анализом | `/info SBER.MOEX` или просто `SBER.MOEX` |
| `/portfolio` | Создание и анализ портфеля с весами | `/portfolio SPY.US:0.6 QQQ.US:0.4` |
| `/compare` | Сравнение активов и портфелей | `/compare SPY.US QQQ.US` |
| `/my` | Просмотр всех сохраненных портфелей | `/my` |
| `/list [код]` | Просмотр пространств имен или символов | `/list` или `/list US` |
| `/gemini_status` | Проверка статуса AI сервисов | `/gemini_status` |

### 🧠 Возможности

### 📊 Поддерживаемые рынки и активы

#### 🇺🇸 Американские рынки (.US)
- **Акции**: AAPL.US, TSLA.US, MSFT.US, GOOGL.US
- **ETF**: SPY.US, QQQ.US, VOO.US, AGG.US, BND.US
- **Индексы**: SPX.INDX, IXIC.INDX, RUT.INDX

#### 🇷🇺 Российские рынки (.MOEX)
- **Акции**: SBER.MOEX, GAZP.MOEX, LKOH.MOEX, NVTK.MOEX
- **Индексы**: RGBITR.INDX, MCFTR.INDX
- **Облигации**: OBLG.MOEX, SU26208RMFS.MOEX

#### 🇨🇳 Китайские рынки (Tushare API)
- **Шанхайская биржа (.SH)**: 600000.SH, 000001.SH
- **Шэньчжэньская биржа (.SZ)**: 000001.SZ, 399005.SZ
- **Пекинская биржа (.BJ)**: 900001.BJ, 800001.BJ
- **Гонконгская биржа (.HK)**: 00001.HK, 00700.HK

#### 🌍 Международные рынки
- **Лондонская биржа (.LSE)**: VOD.LSE, BP.LSE
- **Немецкая биржа (.XETR)**: SAP.XETR, BMW.XETR
- **Французская биржа (.XFRA)**: ASML.XFRA, LVMH.XFRA
- **Голландская биржа (.XAMS)**: ASML.XAMS, ING.XAMS

#### 💱 Валютные пары (.FX)
- **Основные пары**: EURUSD.FX, GBPUSD.FX, USDJPY.FX
- **Кросс-пары**: EURGBP.FX, AUDCAD.FX
- **Экзотические**: USDTRY.FX, USDZAR.FX

#### 🛢️ Товарные активы (.COMM)
- **Драгоценные металлы**: XAU.COMM (золото), XAG.COMM (серебро)
- **Энергоносители**: BRENT.COMM (нефть), NG.COMM (газ)
- **Сельхозтовары**: CORN.COMM, WHEAT.COMM

#### ₿ Криптовалюты (.CC)
- **Основные**: BTC.CC, ETH.CC, ADA.CC
- **Альткоины**: DOT.CC, LINK.CC, UNI.CC

#### 🧠 YandexGPT (основной AI)
- **Финансовый анализ** - Выводы по графикам и данным
- **Оптимизация портфеля** - Рекомендации по улучшению

#### 🔍 Gemini API (дополнительный AI)
- **Анализ графиков** - Детальный анализ изображений графиков
- **Текстовый анализ** - Анализ финансовых данных
- **Мультимодальность** - Работа с текстом и изображениями

### 💼 Управление портфелями

#### 🏗️ Создание портфелей
```
/portfolio SPY.US:0.6 QQQ.US:0.3 BND.US:0.1
/portfolio SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3
/portfolio XAU.COMM:0.5 XAG.COMM:0.3 BRENT.COMM:0.2
```

#### 📋 Автоматические символы портфелей
- Автоматическое сохранение всех атрибутов
- Использование в команде `/compare`

#### 🔄 Сравнение портфелей
```
/compare PORTFOLIO_1 SPY.US          # Портфель vs индекс
/compare PORTFOLIO_1 PORTFOLIO_2     # Два портфеля
/compare PORTFOLIO_1 SPY.US QQQ.US   # Смешанное сравнение
```

### 📊 Финансовые метрики

#### 📈 Метрики производительности
- **Total Return** - Общая доходность
- **Annual Return** - Годовая доходность (CAGR)
- **Volatility** - Волатильность (стандартное отклонение)
- **Sharpe Ratio** - Коэффициент Шарпа
- **Sortino Ratio** - Коэффициент Сортино
- **Max Drawdown** - Максимальная просадка
- **VaR (95%)** - Value at Risk
- **CVaR (95%)** - Conditional Value at Risk

#### 🔗 Корреляционный анализ
- **Корреляционная матрица** - Тепловая карта корреляций
- **Диверсификация** - Анализ эффективности диверсификации
- **Риск-доходность** - Соотношение риска и доходности

#### 📊 Дополнительные метрики
- **Rolling CAGR** - Скользящая годовая доходность
- **Rolling Volatility** - Скользящая волатильность
- **Rolling Sharpe** - Скользящий коэффициент Шарпа
- **Dividend Yield** - Дивидендная доходность
- **Price-to-Earnings** - Соотношение цена/прибыль

### 🛠️ Технические возможности

#### 🔧 Модульная архитектура
- **services/** - Специализированные сервисы
- **domain/** - Доменные объекты (Asset, Portfolio)
- **context_store.py** - Управление контекстом пользователя
- **chart_styles.py** - Централизованные стили графиков

#### 🌐 API интеграции
- **Okama** - Основная библиотека финансового анализа
- **Tushare** - Китайские фондовые рынки
- **YandexGPT** - AI анализ
- **Gemini** - Дополнительный AI анализ

#### 💾 Управление данными
- **In-memory storage** - Быстрый доступ к контексту
- **Thread-safe operations** - Безопасная многопоточность
- **Automatic cleanup** - Управление памятью
- **Context persistence** - Сохранение состояния между сессиями

### 🎯 Продвинутые функции

#### 🔍 Поиск и фильтрация
- **Поиск по названию** - Автоматический поиск активов
- **Фильтрация по биржам** - Быстрый доступ к нужным рынкам
- **ISIN коды** - Поддержка международных идентификаторов


#### 🌍 Мультивалютность
- **Автоматическое определение валюты** - По символам активов
- **Конвертация валют** - Единая валюта для сравнения
- **Инфляционная корректировка** - Реальная доходность

### 🚀 Развертывание и конфигурация

#### ⚙️ Переменные окружения
```env
# Обязательные
TELEGRAM_BOT_TOKEN=your_bot_token
YANDEX_API_KEY=your_yandex_key
YANDEX_FOLDER_ID=your_folder_id

# Опциональные
TUSHARE_API_KEY=your_tushare_key
GEMINI_API_KEY=your_gemini_key
```

#### 📦 Зависимости
- **Python 3.8+** - Современная версия Python
- **Okama 1.5.0+** - Библиотека финансового анализа
- **matplotlib** - Построение графиков
- **pandas** - Обработка данных
- **scipy** - Научные вычисления
- **requests** - HTTP запросы
- **tushare** - Китайские рынки

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

#### Вариант 1: Использование виртуального окружения (рекомендуется)
```bash
# Активация виртуального окружения
.venv\Scripts\python.exe bot.py

# Или с помощью helper скрипта
python3 scripts/run_python.py bot.py
```

#### Вариант 2: Прямой запуск
```bash
python bot.py
```