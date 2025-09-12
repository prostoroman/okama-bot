# Отчет об унификации расчета коэффициента Шарпа

## Обзор

Данный отчет описывает работу по объединению всех расчетов коэффициента Шарпа в единую функцию с использованием оптимальных безрисковых ставок для различных валют через методы okama.

## Проблема

В коде бота было обнаружено множество мест с дублирующимися расчетами коэффициента Шарпа:
- Использовались фиксированные безрисковые ставки (0.02 = 2%)
- Отсутствовала унификация расчетов
- Не учитывались особенности различных валют
- Код был разбросан по разным функциям

## Решение

### 1. Создана единая функция `calculate_sharpe_ratio`

```python
def calculate_sharpe_ratio(self, returns: Union[float, pd.Series], volatility: float, 
                          currency: str = 'USD', period_years: float = None, 
                          asset_data: Any = None) -> float:
```

**Особенности:**
- Поддержка различных типов входных данных (float, pd.Series)
- Автоматический выбор безрисковой ставки по валюте
- Учет периода инвестирования для выбора оптимальной ставки
- Интеграция с okama объектами для прямого расчета
- Обработка ошибок и fallback значения

### 2. Создана функция `get_risk_free_rate`

```python
def get_risk_free_rate(self, currency: str, period_years: float = None) -> float:
```

**Особенности:**
- Маппинг валют на соответствующие ставки okama
- Период-зависимый выбор ставок для RUB и CNY
- Fallback ставки для надежности
- Логирование процесса выбора ставки

### 3. Маппинг валют на безрисковые ставки

```python
self.risk_free_rate_mapping = {
    'USD': 'US_EFFR.RATE',  # US Federal Reserve Effective Federal Funds Rate
    'EUR': 'EU_DFR.RATE',   # European Central Bank key rate
    'GBP': 'UK_BR.RATE',    # Bank of England Bank Rate
    'RUB': 'RUS_CBR.RATE',  # Bank of Russia key rate
    'CNY': 'CHN_LPR1.RATE', # China one-year loan prime rate
    'JPY': 'US_EFFR.RATE',  # Use US rate as proxy for JPY
    'CHF': 'EU_DFR.RATE',   # Use EU rate as proxy for CHF
    'CAD': 'US_EFFR.RATE',  # Use US rate as proxy for CAD
    'AUD': 'US_EFFR.RATE',  # Use US rate as proxy for AUD
    'ILS': 'ISR_IR.RATE',   # Bank of Israel interest rate
}
```

### 4. Период-зависимый выбор ставок

**Для RUB:**
- ≤ 3 месяцев: `RUONIA.RATE` (overnight rate)
- ≤ 6 месяцев: `RUONIA_AVG_1M.RATE` (1 month average)
- ≤ 1 года: `RUONIA_AVG_3M.RATE` (3 month average)
- > 1 года: `RUONIA_AVG_6M.RATE` (6 month average)

**Для CNY:**
- ≤ 5 лет: `CHN_LPR1.RATE` (1-year rate)
- > 5 лет: `CHN_LPR5.RATE` (5-year rate)

## Замененные участки кода

### 1. Основные метрики портфеля (строка ~5957)
```python
# Было:
risk_free_rate = 0.02  # 2% annual risk-free rate
sharpe_value = (cagr_value - risk_free_rate) / volatility_value

# Стало:
sharpe_value = self.calculate_sharpe_ratio(cagr_value, volatility_value, currency)
```

### 2. Анализ активов (строка ~6261)
```python
# Было:
if hasattr(asset_data, 'get_sharpe_ratio'):
    sharpe_ratio = asset_data.get_sharpe_ratio(rf_return=0.02)
else:
    sharpe_ratio = (annual_return - 0.02) / volatility

# Стало:
sharpe_ratio = self.calculate_sharpe_ratio(annual_return, volatility, currency, asset_data=asset_data)
```

### 3. Детальные метрики (строка ~6623)
```python
# Было:
if hasattr(asset_data, 'get_sharpe_ratio'):
    sharpe_ratio = asset_data.get_sharpe_ratio(rf_return=0.02)
else:
    sharpe_ratio = (annual_return - 0.02) / volatility

# Стало:
sharpe_ratio = self.calculate_sharpe_ratio(annual_return, volatility, currency, asset_data=asset_data)
```

### 4. Сравнение активов (строка ~6927)
```python
# Было:
risk_free_rate = 0.02  # 2% annual risk-free rate
symbol_metrics['sharpe'] = (symbol_metrics['cagr'] - risk_free_rate) / symbol_metrics['volatility']

# Стало:
symbol_metrics['sharpe'] = self.calculate_sharpe_ratio(symbol_metrics['cagr'], symbol_metrics['volatility'], currency)
```

### 5. Метрики портфеля (строки ~9961, ~9970)
```python
# Было:
sharpe_ratio = (annual_return - 0.02) / volatility

# Стало:
sharpe_ratio = self.calculate_sharpe_ratio(annual_return, volatility, currency, asset_data=portfolio)
```

### 6. Метрики активов (строки ~10144, ~10153)
```python
# Было:
sharpe_ratio = (annual_return - 0.02) / volatility

# Стало:
sharpe_ratio = self.calculate_sharpe_ratio(annual_return, volatility, currency, asset_data=asset)
```

## Тестирование

Создан тестовый файл `tests/test_sharpe_ratio_unified.py` который проверяет:

1. **Базовые расчеты** для разных валют
2. **Различные сценарии** (высокая доходность/низкая волатильность, низкая доходность/высокая волатильность, отрицательная доходность)
3. **Разные валюты** (USD, EUR, RUB, CNY)
4. **Период-зависимый выбор ставок** для RUB и CNY
5. **Fallback механизм** при недоступности okama данных

### Результаты тестирования

```
✅ All tests completed successfully!

Key improvements:
- Unified Sharpe ratio calculation function
- Currency-specific risk-free rates using okama
- Period-based rate selection for RUB and CNY
- Fallback rates for reliability
- Consistent calculation across all portfolio and asset metrics
```

## Преимущества нового подхода

### 1. Унификация
- Все расчеты коэффициента Шарпа теперь используют единую функцию
- Устранено дублирование кода
- Единообразная обработка ошибок

### 2. Точность
- Использование актуальных безрисковых ставок для каждой валюты
- Учет периода инвестирования для выбора оптимальной ставки
- Интеграция с okama для получения реальных данных

### 3. Надежность
- Fallback ставки при недоступности okama данных
- Обработка различных типов входных данных
- Логирование процесса расчета

### 4. Гибкость
- Поддержка различных валют
- Возможность расширения маппинга валют
- Настраиваемые fallback ставки

## Поддерживаемые валюты и ставки

| Валюта | Okama Symbol | Описание | Fallback Rate |
|--------|--------------|----------|---------------|
| USD | US_EFFR.RATE | US Federal Reserve Effective Federal Funds Rate | 5.0% |
| EUR | EU_DFR.RATE | European Central Bank key rate | 4.0% |
| GBP | UK_BR.RATE | Bank of England Bank Rate | 5.0% |
| RUB | RUS_CBR.RATE | Bank of Russia key rate | 16.0% |
| CNY | CHN_LPR1.RATE | China one-year loan prime rate | 3.5% |
| JPY | US_EFFR.RATE | Use US rate as proxy | 5.0% |
| CHF | EU_DFR.RATE | Use EU rate as proxy | 4.0% |
| CAD | US_EFFR.RATE | Use US rate as proxy | 5.0% |
| AUD | US_EFFR.RATE | Use US rate as proxy | 5.0% |
| ILS | ISR_IR.RATE | Bank of Israel interest rate | 4.5% |

## Заключение

Работа по унификации расчета коэффициента Шарпа успешно завершена. Все расчеты теперь используют единую функцию с оптимальными безрисковыми ставками для различных валют. Это обеспечивает:

- **Точность расчетов** - использование актуальных ставок
- **Консистентность** - единый подход во всем коде
- **Надежность** - fallback механизмы и обработка ошибок
- **Гибкость** - поддержка различных валют и периодов

Система готова к использованию и может быть легко расширена для поддержки дополнительных валют и ставок.
