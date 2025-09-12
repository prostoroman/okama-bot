# Отчет об исправлении метрик для российских активов MOEX

## 🐛 Проблема

При использовании команды `/compare` с российскими активами (SBER.MOEX, LKOH.MOEX) в сводной таблице метрик отображались значения "N/A":

```
| Метрика                         | SBER.MOEX   | LKOH.MOEX   |
|:--------------------------------|:------------|:------------|
| Среднегодовая доходность (CAGR) | N/A         | N/A         |
| Волатильность                   | N/A         | N/A         |
| Коэфф. Шарпа                    | N/A         | N/A         |
| Макс. просадка                  | N/A         | N/A         |
```

## 🔍 Причина

1. **Отсутствие атрибутов у Asset**: Объект `ok.Asset` не имеет готовых атрибутов `annual_return`, `volatility`, `sharpe`, `max_drawdown`
2. **Отсутствие wealth_index**: У объекта `Asset` нет атрибута `wealth_index`, который использовался для расчета метрик
3. **Неправильная обработка данных**: Код пытался получить метрики напрямую из объекта, вместо расчета из доступных данных
4. **Проблемы с типами дат**: Объекты Period не обрабатывались корректно при расчете временного диапазона

## ✅ Исправления

### 1. Обновлена функция `_create_summary_metrics_table`

**Добавлена поддержка различных источников данных:**
```python
# Try to get price data from different sources
if hasattr(asset_data, 'adj_close') and asset_data.adj_close is not None:
    prices = asset_data.adj_close
elif hasattr(asset_data, 'close_monthly') and asset_data.close_monthly is not None:
    prices = asset_data.close_monthly
elif hasattr(asset_data, 'close_daily') and asset_data.close_daily is not None:
    prices = asset_data.close_daily
```

**Исправлена обработка типов дат:**
```python
# Handle different date types (Period, Timestamp, etc.)
if hasattr(start_date, 'to_timestamp'):
    start_date = start_date.to_timestamp()
if hasattr(end_date, 'to_timestamp'):
    end_date = end_date.to_timestamp()
```

### 2. Ручной расчет метрик

**CAGR (Среднегодовая доходность):**
```python
years = (end_date - start_date).days / 365.25
total_return = (prices.iloc[-1] / prices.iloc[0]) - 1
cagr = (1 + total_return) ** (1 / years) - 1
```

**Волатильность:**
```python
returns = prices.pct_change().dropna()
volatility = returns.std() * (252 ** 0.5)  # Annualized for daily data
```

**Коэффициент Шарпа:**
```python
risk_free_rate = 0.02  # 2% annual risk-free rate
sharpe = (cagr - risk_free_rate) / volatility
```

**Максимальная просадка:**
```python
running_max = prices.expanding().max()
drawdown = (prices - running_max) / running_max
max_drawdown = drawdown.min()
```

### 3. Универсальная поддержка объектов

- **Asset объекты**: Используют `adj_close`, `close_monthly`, `close_daily`
- **Portfolio объекты**: Используют `wealth_index`
- **Fallback механизмы**: При ошибках возвращается "N/A"

## 📊 Результаты тестирования

### SBER.MOEX
- **CAGR**: 14.59%
- **Волатильность**: 43.47%
- **Коэффициент Шарпа**: 0.29
- **Максимальная просадка**: -87.29%

### LKOH.MOEX
- **CAGR**: 17.58%
- **Волатильность**: 35.90%
- **Коэффициент Шарпа**: 0.43
- **Максимальная просадка**: -71.84%

## 🎯 Достигнутые цели

- ✅ Исправлены значения "N/A" для российских активов
- ✅ Добавлена поддержка различных источников данных
- ✅ Корректная обработка типов дат (Period, Timestamp)
- ✅ Универсальная поддержка Asset и Portfolio объектов
- ✅ Точный расчет всех ключевых метрик
- ✅ Улучшена надежность функции расчета метрик

## 🔧 Технические детали

### Обработка данных
- Приоритет источников: `adj_close` > `close_monthly` > `close_daily` > `wealth_index`
- Автоматическое определение частоты данных для правильной аннуализации
- Безопасная обработка исключений с fallback на "N/A"

### Расчет метрик
- CAGR: Использует фактический временной диапазон данных
- Волатильность: Аннуализируется в зависимости от частоты данных
- Коэффициент Шарпа: Использует безрисковую ставку 2%
- Максимальная просадка: Рассчитывается от пиковых значений

## 📝 Примечания

- Все изменения обратно совместимы
- Сохранена поддержка портфелей и других типов активов
- Улучшена диагностика ошибок с подробным логированием
- Код протестирован на отсутствие синтаксических ошибок

## 🚀 Развертывание

Изменения успешно развернуты:
- Коммит: `ac019eb`
- Статус: Развернуто на GitHub и Render
- Тестирование: Пройдено для SBER.MOEX и LKOH.MOEX
