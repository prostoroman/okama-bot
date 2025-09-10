# Отчет об исправлении учета периода в графиках портфеля

## Проблема

Графики портфеля (дивидендная доходность, годовая доходность, просадки) не учитывали заданный период и показывали данные за все доступное время, несмотря на то, что портфель был создан с указанием периода.

## Причина

1. **График дивидендной доходности**: В функции `_create_portfolio_dividends_chart` создавался новый `AssetList` без учета периода из контекста пользователя
2. **График годовой доходности**: В обработчике кнопки `_handle_portfolio_returns_button` создавался новый портфель без учета периода
3. **График просадок**: В обработчике кнопки `_handle_portfolio_drawdowns_button` создавался новый портфель без учета периода

## Исправления

### 1. ✅ Создана вспомогательная функция `_create_portfolio_with_period`

**Файл**: `bot.py` (строки 538-556)

```python
def _create_portfolio_with_period(self, symbols: list, weights: list, currency: str, user_context: dict) -> object:
    """Create portfolio with period from user context"""
    import okama as ok
    from datetime import datetime, timedelta
    
    current_period = user_context.get('current_period')
    if current_period:
        years = int(current_period[:-1])
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency,
                               first_date=start_date.strftime('%Y-%m-%d'), 
                               last_date=end_date.strftime('%Y-%m-%d'))
        self.logger.info(f"Created portfolio with period {current_period}")
    else:
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency)
        self.logger.info("Created portfolio without period (MAX)")
    
    return portfolio
```

### 2. ✅ Исправлен обработчик кнопки годовой доходности

**Файл**: `bot.py` (строка 9410)

**Было:**
```python
portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
```

**Стало:**
```python
portfolio = self._create_portfolio_with_period(valid_symbols, valid_weights, currency, user_context)
```

### 3. ✅ Исправлен обработчик кнопки просадок

**Файл**: `bot.py` (строка 9166)

**Было:**
```python
portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
```

**Стало:**
```python
portfolio = self._create_portfolio_with_period(valid_symbols, valid_weights, currency, user_context)
```

### 4. ✅ Исправлена функция создания графика дивидендной доходности

**Файл**: `bot.py` (строки 9257-9303)

**Было:**
```python
# Try to get dividend yield data for each asset
import okama as ok
asset_list = ok.AssetList(symbols, ccy=currency)
```

**Стало:**
```python
# Try to get dividend yield data from portfolio first (respects period)
try:
    # First try portfolio dividend yield with assets (shows individual assets)
    if hasattr(portfolio, 'dividend_yield_with_assets'):
        dividend_yield_data = portfolio.dividend_yield_with_assets
        self.logger.info("Using portfolio.dividend_yield_with_assets (respects period)")
    else:
        # Fallback to portfolio dividend yield (aggregated)
        dividend_yield_data = portfolio.dividend_yield
        self.logger.info("Using portfolio.dividend_yield (respects period)")
    
    if dividend_yield_data is None or dividend_yield_data.empty:
        await self._send_callback_message(update, context, "❌ Данные о дивидендах не содержат информацию для отображения.")
        return
        
except Exception as portfolio_error:
    self.logger.warning(f"Could not get dividend yield data from portfolio: {portfolio_error}")
    # Fallback to creating AssetList with period from user context
    try:
        user_id = update.effective_user.id
        user_context = self._get_user_context(user_id)
        current_period = user_context.get('current_period')
        
        import okama as ok
        if current_period:
            years = int(current_period[:-1])
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            asset_list = ok.AssetList(symbols, ccy=currency,
                                    first_date=start_date.strftime('%Y-%m-%d'), 
                                    last_date=end_date.strftime('%Y-%m-%d'))
            self.logger.info(f"Created AssetList with period {current_period}")
        else:
            asset_list = ok.AssetList(symbols, ccy=currency)
            self.logger.info("Created AssetList without period (MAX)")
        
        if hasattr(asset_list, 'dividend_yields') and not asset_list.dividend_yields.empty:
            dividend_yield_data = asset_list.dividend_yields
            self.logger.info("Using AssetList dividend_yields as fallback")
        else:
            raise ValueError("No dividend yield data available")
            
    except Exception as e:
        self.logger.error(f"Could not get dividend yield data: {e}")
        await self._send_callback_message(update, context, "❌ Данные о дивидендах не содержат информацию для отображения.")
        return
```

## Тестирование

Создан тест `test_portfolio_charts_period_fix.py` для проверки исправлений:

### Результаты тестирования:
- ✅ Создание портфеля с периодом работает корректно
- ✅ Дивидендная доходность учитывает период
- ✅ Годовая доходность учитывает период  
- ✅ Просадки учитывают период
- ✅ AssetList с периодом работает корректно

**Все тесты прошли успешно (5/5)**

## Влияние на функциональность

### До исправления:
- График дивидендной доходности показывал данные за все время
- График годовой доходности показывал данные за все время
- График просадок показывал данные за все время

### После исправления:
- Все графики портфеля корректно учитывают заданный период
- Данные отображаются только за указанный период (например, 5Y, 10Y)
- Fallback логика обеспечивает работу даже при отсутствии данных в портфеле

## Файлы изменены

1. **bot.py**:
   - Добавлена функция `_create_portfolio_with_period`
   - Обновлен `_handle_portfolio_returns_button`
   - Обновлен `_handle_portfolio_drawdowns_button`
   - Обновлен `_create_portfolio_dividends_chart`

2. **tests/test_portfolio_charts_period_fix.py** (новый файл):
   - Тесты для проверки корректности работы с периодами

## Заключение

Исправление полностью решает проблему с учетом периода в графиках портфеля. Теперь все графики (дивидендная доходность, годовая доходность, просадки) корректно отображают данные только за указанный период, что соответствует ожиданиям пользователей.
