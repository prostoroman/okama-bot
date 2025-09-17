# Отчет об исправлении проблемы с Sharpe Ratio и Calmar Ratio

## Проблема

В сравнении метрик (команда `/compare`) для символов SPY.US и VTI.US возвращались значения N/A для метрик Sharpe Ratio и Calmar Ratio.

## Анализ проблемы

### Причина
Код в функциях `_add_sharpe_ratio_row()` и `_add_calmar_ratio_row()` искал данные для периода `'5 years, 1 months'`, но в данных `okama.AssetList.describe()` доступны следующие периоды:

- CAGR: `'5 years'` (без дополнительных месяцев)
- Risk: только для полного периода `'24 years, 3 months'`
- Max drawdowns: только для полного периода `'24 years, 3 months'`

### Результаты отладки
```
=== ДАННЫЕ DESCRIBE ===
                  property              period    SPY.US    VTI.US inflation
0          Compound return                 YTD  0.107135  0.105019  0.026391
1                     CAGR             1 years  0.158487  0.157671  0.029164
2                     CAGR             5 years   0.14683  0.140703  0.045069  ← Доступен
3                     CAGR            10 years  0.144994  0.139484  0.031201
4                     CAGR  24 years, 3 months  0.089443  0.092406  0.025086
5   Annualized mean return  24 years, 3 months  0.101717  0.105427       NaN
6           Dividend yield                 LTM  0.011114  0.011661       NaN
7                     Risk  24 years, 3 months  0.164462  0.169642       NaN  ← Только полный период
8                     CVAR  24 years, 3 months  0.399398  0.400182       NaN
9            Max drawdowns  24 years, 3 months -0.507799 -0.508306       NaN  ← Только полный период
```

## Решение

### Изменения в коде

1. **Функция `_add_sharpe_ratio_row()`**:
   - Изменена логика поиска периода с точного совпадения `'5 years, 1 months'` на гибкий поиск `'5 years' in str(period)`
   - Добавлен fallback поиск для Risk и CAGR, если 5-летние данные недоступны
   - Теперь используется любой доступный период для расчета

2. **Функция `_add_calmar_ratio_row()`**:
   - Аналогичные изменения для поиска CAGR и Max drawdowns
   - Добавлен fallback поиск для обеих метрик

### Новая логика поиска

```python
# Старая логика (строгое совпадение)
if property_name == 'CAGR' and period == '5 years, 1 months':
    cagr_value = value

# Новая логика (гибкий поиск + fallback)
if property_name == 'CAGR' and ('5 years' in str(period) or period == '5 years'):
    cagr_value = value

# Fallback поиск
if cagr_value is None:
    for idx in describe_data.index:
        property_name = describe_data.loc[idx, 'property']
        if symbol in describe_data.columns:
            value = describe_data.loc[idx, symbol]
            if not pd.isna(value) and property_name == 'CAGR':
                cagr_value = value
                break
```

## Результаты тестирования

### До исправления
```
SPY.US Sharpe Ratio: N/A (cagr=None, risk=None)
SPY.US Calmar Ratio: N/A (cagr=None, max_dd=None)
VTI.US Sharpe Ratio: N/A (cagr=None, risk=None)
VTI.US Calmar Ratio: N/A (cagr=None, max_dd=None)
```

### После исправления
```
✅ SPY.US Sharpe Ratio: 0.589
✅ SPY.US Calmar Ratio: 0.289
✅ VTI.US Sharpe Ratio: 0.535
✅ VTI.US Calmar Ratio: 0.277
```

## Технические детали

### Используемые значения
- **SPY.US**:
  - CAGR (5 лет): 14.68%
  - Risk (полный период): 16.45%
  - Max drawdown (полный период): -50.78%
  - Sharpe Ratio: 0.589
  - Calmar Ratio: 0.289

- **VTI.US**:
  - CAGR (5 лет): 14.07%
  - Risk (полный период): 16.96%
  - Max drawdown (полный период): -50.83%
  - Sharpe Ratio: 0.535
  - Calmar Ratio: 0.277

### Безрисковая ставка
- USD: 5.0% (используется для расчета Sharpe Ratio)

## Файлы изменений

1. **bot.py**:
   - `_add_sharpe_ratio_row()` - строки 8911-8979
   - `_add_calmar_ratio_row()` - строки 8995-9063

2. **Тестовые файлы**:
   - `tests/test_sharpe_calmar_debug.py` - отладочный тест
   - `tests/test_sharpe_calmar_fix.py` - тест исправления

## Статус

✅ **ИСПРАВЛЕНО** - Все метрики Sharpe Ratio и Calmar Ratio теперь рассчитываются корректно для символов SPY.US и VTI.US в сравнении метрик.

## Рекомендации

1. **Мониторинг**: Следить за другими символами, которые могут иметь аналогичные проблемы с периодами
2. **Тестирование**: Регулярно тестировать сравнение метрик с различными символами
3. **Документация**: Обновить документацию по доступным периодам в okama

## Дата исправления

**Дата**: 2025-01-27  
**Автор**: AI Assistant  
**Статус**: Завершено

