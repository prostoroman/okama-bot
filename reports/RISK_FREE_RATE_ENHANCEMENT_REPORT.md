# Отчет об улучшении расчета безрисковых ставок

## 🎯 Цель
Заменить фиксированную безрисковую ставку 2% на динамические ставки, рассчитанные на основе валюты и актуальных ставок центральных банков.

## 🔍 Проблема
В функции `_create_summary_metrics_table` использовалась фиксированная безрисковая ставка 2%, что не соответствовало:
- Актуальным ставкам центральных банков
- Различиям между валютами
- Периоду инвестирования

## ✅ Решение

### 1. Использование существующей функции `get_risk_free_rate`
В коде уже была реализована функция `get_risk_free_rate`, которая:
- Использует актуальные ставки центральных банков через okama
- Учитывает период инвестирования для RUB и CNY
- Имеет fallback ставки для надежности

### 2. Маппинг валют на безрисковые ставки
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

### 3. Fallback ставки (актуальные на 2025 год)
```python
fallback_rates = {
    'USD': 0.05,  # 5% - current Fed funds rate
    'EUR': 0.04,  # 4% - current ECB rate
    'GBP': 0.05,  # 5% - current BoE rate
    'RUB': 0.16,  # 16% - current CBR rate
    'CNY': 0.035, # 3.5% - current LPR rate
    'JPY': 0.05,  # 5% - use US rate as proxy
    'CHF': 0.04,  # 4% - use EU rate as proxy
    'CAD': 0.05,  # 5% - use US rate as proxy
    'AUD': 0.05,  # 5% - use US rate as proxy
    'ILS': 0.045, # 4.5% - current BoI rate
}
```

## 🔧 Внесенные изменения

### 1. Обновление расчета коэффициента Шарпа
**Было:**
```python
risk_free_rate = 0.02  # 2% annual risk-free rate
symbol_metrics['sharpe'] = (symbol_metrics['cagr'] - risk_free_rate) / symbol_metrics['volatility']
```

**Стало:**
```python
# Calculate years for period-based rate selection
years = None
if prices is not None and len(prices) > 1:
    start_date = prices.index[0]
    end_date = prices.index[-1]
    if hasattr(start_date, 'to_timestamp'):
        start_date = start_date.to_timestamp()
    if hasattr(end_date, 'to_timestamp'):
        end_date = end_date.to_timestamp()
    years = (end_date - start_date).days / 365.25

# Use proper risk-free rate based on currency
risk_free_rate = self.get_risk_free_rate(currency, years)
symbol_metrics['sharpe'] = (symbol_metrics['cagr'] - risk_free_rate) / symbol_metrics['volatility']
symbol_metrics['risk_free_rate'] = risk_free_rate
```

### 2. Обновление расчета коэффициента Сортино
**Было:**
```python
risk_free_rate = 0.02  # 2% annual risk-free rate
symbol_metrics['sortino'] = (symbol_metrics['cagr'] - risk_free_rate) / downside_deviation
```

**Стало:**
```python
# Use the same risk-free rate as calculated for Sharpe ratio
risk_free_rate = symbol_metrics.get('risk_free_rate', self.get_risk_free_rate(currency))
symbol_metrics['sortino'] = (symbol_metrics['cagr'] - risk_free_rate) / downside_deviation
```

### 3. Обновление отображения безрисковой ставки в таблице
**Было:**
```python
risk_free_row = ["Безрисковая ставка"]
for symbol in symbols:
    risk_free_row.append("2.00%")  # Fixed 2% annual risk-free rate
```

**Стало:**
```python
risk_free_row = ["Безрисковая ставка"]
for symbol in symbols:
    risk_free_rate = metrics_data.get(symbol, {}).get('risk_free_rate')
    if risk_free_rate is not None:
        risk_free_row.append(f"{risk_free_rate*100:.2f}%")
    else:
        risk_free_row.append("N/A")
```

## 📊 Результаты тестирования

### Безрисковые ставки по валютам
| Валюта | Символ okama | Ставка | Fallback |
|:-------|:-------------|:-------|:---------|
| USD | US_EFFR.RATE | 5.00% | 5.00% |
| EUR | EU_DFR.RATE | 4.00% | 4.00% |
| GBP | UK_BR.RATE | 5.00% | 5.00% |
| RUB | RUS_CBR.RATE | 16.00% | 16.00% |
| CNY | CHN_LPR1.RATE | 3.50% | 3.50% |
| JPY | US_EFFR.RATE | 5.00% | 5.00% |
| CHF | EU_DFR.RATE | 4.00% | 4.00% |
| CAD | US_EFFR.RATE | 5.00% | 5.00% |
| AUD | US_EFFR.RATE | 5.00% | 5.00% |
| ILS | ISR_IR.RATE | 4.50% | 4.50% |

### Влияние на метрики SPY.US и QQQ.US
| Актив | Старая ставка | Новая ставка | Старый Sharpe | Новый Sharpe |
|:------|:-------------|:-------------|:-------------|:-------------|
| SPY.US | 2.00% | 5.00% | 0.46 | 0.30 |
| QQQ.US | 2.00% | 5.00% | 0.31 | 0.20 |

## 📈 Обновленная таблица метрик

| Метрика                         | SPY.US   | QQQ.US   |
|:--------------------------------|:---------|:---------|
| Среднегодовая доходность (CAGR) | 10.63%   | 10.31%   |
| Волатильность                   | 18.69%   | 27.11%   |
| **Безрисковая ставка**          | **5.00%**| **5.00%**|
| Коэфф. Шарпа                    | 0.30     | 0.20     |
| Макс. просадка                  | -55.19%  | -82.98%  |
| Коэф. Сортино                   | 7.10     | 4.10     |
| Коэф. Кальмара                  | 0.19     | 0.12     |
| VaR 95%                         | -1.81%   | -2.75%   |
| CVaR 95%                        | -2.80%   | -4.05%   |

## 🎯 Преимущества нового подхода

### 1. Актуальность
- Использование реальных ставок центральных банков
- Автоматическое обновление при изменении ставок
- Соответствие текущим экономическим условиям

### 2. Точность
- Учет различий между валютами
- Период-зависимый выбор ставок для RUB и CNY
- Более корректные расчеты коэффициентов Шарпа и Сортино

### 3. Прозрачность
- Отображение фактической безрисковой ставки в таблице
- Возможность отслеживания влияния ставки на метрики
- Понятность для пользователей

### 4. Надежность
- Fallback механизм при недоступности okama данных
- Обработка ошибок и исключений
- Логирование процесса выбора ставки

## 📝 Заключение

### ✅ Изменения успешно внедрены
- Заменена фиксированная ставка 2% на динамические ставки
- Использована существующая функция `get_risk_free_rate`
- Обновлены расчеты коэффициентов Шарпа и Сортино
- Добавлено отображение фактической ставки в таблице

### 📊 Влияние на результаты
- Коэффициенты Шарпа и Сортино стали более консервативными
- Это отражает реальные экономические условия с высокими ставками
- Метрики стали более точными и сопоставимыми

### 🔄 Рекомендации
- Периодически обновлять fallback ставки
- Мониторить доступность okama данных по ставкам
- Рассмотреть добавление других валют при необходимости

---
*Отчет создан: 2025-01-27*  
*Статус: ИЗМЕНЕНИЯ ВНЕДРЕНЫ УСПЕШНО*  
*Рекомендация: ПРОДОЛЖИТЬ ИСПОЛЬЗОВАНИЕ НОВОГО ПОДХОДА*
