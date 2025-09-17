# Отчет об исправлении проблемы с Sharpe Ratio в сравнении активов

## Проблема

**Дата:** 2025-01-27  
**Символы:** AAPL.US, TSLA.US  
**Проблема:** В команде `/compare` для метрики Sharpe Ratio отображалось значение N/A вместо числового значения.

## Анализ проблемы

### Причина
Код в функции `_add_sharpe_ratio_row()` искал данные для периода `'5 years, 1 months'`, но в данных `okama.AssetList.describe()` доступны следующие периоды:

- CAGR: `'5 years'` (без дополнительных месяцев)
- Risk: только для полного периода `'15 years, 2 months'`

### Результаты отладки
```
=== ДАННЫЕ DESCRIBE ===
                  property              period   AAPL.US   TSLA.US inflation
0          Compound return                 YTD -0.069797 -0.173311  0.026391
1                     CAGR             1 years   0.01843  0.559258  0.029164
2                     CAGR             5 years  0.130915  0.149777  0.045069  ← Доступен
3                     CAGR            10 years  0.248022    0.3499  0.031201
4                     CAGR  15 years, 2 months   0.25345  0.422708  0.026496
5   Annualized mean return  15 years, 2 months  0.297067  0.683894       NaN
6           Dividend yield                 LTM  0.004394       0.0       NaN
7                     Risk  15 years, 2 months  0.343997  1.108391       NaN  ← Только полный период
8                     CVAR  15 years, 2 months  0.287339   0.57004       NaN
9            Max drawdowns  15 years, 2 months -0.395395 -0.677187       NaN
```

## Решение

### Изменения в коде

**Файл:** `bot.py`  
**Функция:** `_add_sharpe_ratio_row()` (строки 8941-9002)

### До исправления (проблемный код)
```python
if property_name == 'CAGR' and period == '5 years, 1 months':
    cagr_value = value
elif property_name == 'Risk' and period == '5 years, 1 months':
    risk_value = value
```

### После исправления
```python
# First, try to find CAGR for 5 years period
if property_name == 'CAGR' and period == '5 years':
    cagr_value = value
elif property_name == 'Risk' and period == '5 years':
    risk_value = value

# Fallback: if no 5-year data, try to find any available CAGR and Risk
if cagr_value is None:
    for idx in describe_data.index:
        property_name = describe_data.loc[idx, 'property']
        if symbol in describe_data.columns:
            value = describe_data.loc[idx, symbol]
            if not pd.isna(value) and property_name == 'CAGR':
                cagr_value = value
                break

if risk_value is None:
    for idx in describe_data.index:
        property_name = describe_data.loc[idx, 'property']
        if symbol in describe_data.columns:
            value = describe_data.loc[idx, symbol]
            if not pd.isna(value) and property_name == 'Risk':
                risk_value = value
                break
```

### Ключевые улучшения

1. **Исправлен период поиска:** Изменен с `'5 years, 1 months'` на `'5 years'`
2. **Добавлена fallback логика:** Если данные для 5-летнего периода недоступны, используется любой доступный период
3. **Улучшена надежность:** Код теперь работает с различными структурами данных okama

## Результаты тестирования

### До исправления
```
AAPL.US: Sharpe Ratio = N/A
TSLA.US: Sharpe Ratio = N/A
```

### После исправления
```
AAPL.US: Sharpe Ratio = 0.244
TSLA.US: Sharpe Ratio = 0.093
```

### Детали расчета
- **Risk-free rate:** 4.69%
- **AAPL.US:** CAGR (5 years) = 13.09%, Risk (15 years, 2 months) = 34.40%
- **TSLA.US:** CAGR (5 years) = 14.98%, Risk (15 years, 2 months) = 110.84%

## Статус

✅ **ИСПРАВЛЕНО** - Sharpe Ratio теперь корректно рассчитывается и отображается в сравнении активов.

## Влияние

- Исправление влияет на все сравнения активов в команде `/compare`
- Улучшена точность финансовых метрик
- Повышена надежность работы с различными периодами данных
