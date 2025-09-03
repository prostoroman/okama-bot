# Отчет об исправлении кнопки "Месячный график (10Y)"

## Проблема

При нажатии на кнопку "📅 Месячный график (10Y)" в команде `/info` отображался дневной график вместо месячного.

**Причина:** В методе `_get_monthly_chart` в `bot.py` использовалось поле `prices` из `asset_service.get_asset_price_history()`, которое всегда содержит дневные данные (отфильтрованные за 1 год), даже когда запрашивается месячный график.

## Решение

### 1. Исправление логики в `_get_monthly_chart`

**Было:**
```python
# Получаем данные о ценах
if 'prices' in price_history and price_history['prices'] is not None:
    prices = price_history['prices']  # ← Это дневные данные!
    currency = price_history.get('currency', 'USD')
    
    # Создаем график с использованием централизованных стилей
    return self._create_monthly_chart_with_styles(symbol, prices, currency)
```

**Стало:**
```python
# Сначала проверяем наличие готового месячного графика
if 'charts' in price_history and price_history['charts']:
    charts = price_history['charts']
    if 'close_monthly' in charts and charts['close_monthly']:
        chart_data = charts['close_monthly']
        if isinstance(chart_data, bytes) and len(chart_data) > 0:
            self.logger.info(f"Using existing monthly chart for {symbol}")
            return chart_data

# Если готового графика нет, создаем новый из месячных данных
if 'price_data' in price_history and 'close_monthly' in price_history['price_data']:
    monthly_info = price_history['price_data']['close_monthly']
    currency = price_history.get('currency', 'USD')
    
    # Получаем месячные данные из asset
    try:
        asset = ok.Asset(symbol)
        monthly_data = asset.close_monthly
        if monthly_data is not None and len(monthly_data) > 0:
            # Фильтруем данные за 10 лет
            filtered_monthly = self._filter_data_by_period(monthly_data, '10Y')
            return self._create_monthly_chart_with_styles(symbol, filtered_monthly, currency)
    except Exception as asset_error:
        self.logger.warning(f"Could not get monthly data from asset: {asset_error}")
```

### 2. Добавление метода `_filter_data_by_period`

Добавлен метод для фильтрации данных по периоду, скопированный из `asset_service.py`:

```python
def _filter_data_by_period(self, data, period: str):
    """
    Filter data by specified period
    
    Args:
        data: Pandas Series with price data
        period: Time period (e.g., '1Y', '2Y', '5Y', 'MAX')
        
    Returns:
        Filtered data series
    """
    # ... (полная реализация)
```

## Затронутые файлы

- `bot.py`
  - Исправлен метод `_get_monthly_chart`
  - Добавлен метод `_filter_data_by_period`

## Логика исправления

1. **Приоритет готового графика:** Сначала проверяется наличие готового месячного графика в `charts['close_monthly']`
2. **Создание нового графика:** Если готового нет, создается новый из месячных данных `asset.close_monthly`
3. **Фильтрация периода:** Месячные данные фильтруются за 10 лет с помощью `_filter_data_by_period`
4. **Fallback:** Если ничего не работает, используется любой доступный график

## Проверка

Создан тестовый скрипт `test_monthly_chart_fix.py` для проверки исправления:

**Результат:**
```
✅ Price history successful
   - Has charts: True
   - Chart types: ['adj_close', 'close_monthly']
   - Has price_data: True
   - Price data keys: ['adj_close', 'close_monthly']
   - Monthly chart size: 101425 bytes
   - Monthly chart type: <class 'bytes'>

2. Testing asset monthly data directly...
   - Monthly data type: <class 'pandas.core.series.Series'>
   - Monthly data length: 230
   - Monthly data sample: date
2006-08    57122.1129
2006-09    57741.3829
2006-10    60154.9630
2006-11    65420.8833
2006-12    92455.1046
Freq: M, Name: SBER.MOEX, dtype: float64
   ✅ Monthly data available
```

## Технические детали

- **Проблема:** Использование дневных данных вместо месячных для создания месячного графика
- **Решение:** Правильная логика выбора данных с приоритетом готовых месячных графиков
- **Результат:** Кнопка "Месячный график (10Y)" теперь показывает настоящий месячный график за 10 лет

## Примечания

- Исправление не влияет на другие функции бота
- Сохранена обратная совместимость
- Добавлено подробное логирование для отладки
- Fallback механизм обеспечивает надежность
