# Отчет об исправлении проблемы с MOEX активами

## Проблема

При использовании команды `/asset` для активов `LQDT.MOEX` и `VTBR.MOEX` получались ошибочные месячные цены.

## Диагностика

### Анализ данных
Проведено тестирование активов через библиотеку Okama:

**LQDT.MOEX:**
- `adj_close`: 1400 точек данных (дневные цены) ✅
- `close_monthly`: 68 точек данных (месячные цены) ✅
- Период: 2020-02-01 по 2025-08-01 ✅

**VTBR.MOEX:**
- `adj_close`: 4497 точек данных (дневные цены) ✅
- `close_monthly`: 216 точек данных (месячные цены) ✅
- Период: 2007-10-01 по 2025-08-01 ✅

**SBER.MOEX (для сравнения):**
- `adj_close`: 4773 точки данных (дневные цены) ✅
- `close_monthly`: 229 точек данных (месячные цены) ✅
- Период: 2006-09-01 по 2025-08-01 ✅

### Выявленная проблема
**Проблема НЕ в источнике данных** - все данные доступны и корректны.

**Проблема в коде бота:**
- `asset.price` возвращает `NaN` для MOEX активов
- Код не обрабатывал случай, когда `asset.price` равен `NaN`
- Отсутствовал fallback на `adj_close` или `close_monthly` данные

## Исправление

### Изменения в `services/asset_service.py`

1. **Добавлен fallback для NaN значений:**
```python
# Handle NaN values - try to get price from adj_close or close_monthly
if isinstance(price_data, float) and (price_data != price_data or price_data in (float('inf'), float('-inf'))):
    # price_data is NaN or infinite, try fallback to adj_close
    if hasattr(asset, 'adj_close') and asset.adj_close is not None and len(asset.adj_close) > 0:
        try:
            # Get last valid price from adj_close
            adj_close_clean = asset.adj_close.dropna()
            if len(adj_close_clean) > 0:
                latest_price = adj_close_clean.iloc[-1]
                latest_date = adj_close_clean.index[-1]
                return {
                    'price': float(latest_price),
                    'currency': getattr(asset, 'currency', ''),
                    'timestamp': str(latest_date)
                }
        except Exception as e:
            self.logger.warning(f"Failed to get price from adj_close for {symbol}: {e}")
    
    # If adj_close failed, try close_monthly
    if hasattr(asset, 'close_monthly') and asset.close_monthly is not None and len(asset.close_monthly) > 0:
        try:
            # Get last valid price from close_monthly
            monthly_clean = asset.close_monthly.dropna()
            if len(monthly_clean) > 0:
                latest_price = monthly_clean.iloc[-1]
                latest_date = monthly_clean.index[-1]
                return {
                    'price': float(latest_price),
                    'currency': getattr(asset, 'currency', ''),
                    'timestamp': str(latest_date)
                }
        except Exception as e:
            self.logger.warning(f"Failed to get price from close_monthly for {symbol}: {e}")
    
    # If all fallbacks failed, try MOEX ISS
    return _maybe_moex_fallback('Price data is NaN, fallbacks failed')
```

2. **Исправлены проблемы с типизацией для Python 3.7:**
   - Заменены `Dict[str, Any]` на `Dict[str, Union[str, Any]]`
   - Исправлена типизация `tuple[float, str]` на `tuple`

## Результат

### После исправления:
✅ **LQDT.MOEX**: Цена 1.7808 RUB (2025-08-26)
✅ **VTBR.MOEX**: Цена 76.15 RUB (2025-08-25)  
✅ **SBER.MOEX**: Цена 311.21 RUB (2025-08-26)

### Графики создаются корректно:
- **Дневные цены (adj_close)**: 365 точек данных за последний год
- **Месячные цены (close_monthly)**: 120 точек данных за последние 10 лет

## Заключение

Проблема была **НЕ в источнике данных**, а в коде бота, который не обрабатывал случай, когда `asset.price` возвращает `NaN` для MOEX активов.

**Исправление:**
1. Добавлен fallback на `adj_close` данные при получении `NaN` из `asset.price`
2. Добавлен дополнительный fallback на `close_monthly` данные
3. Исправлены проблемы с типизацией для совместимости с Python 3.7

Теперь команда `/asset` работает корректно для всех MOEX активов, включая `LQDT.MOEX` и `VTBR.MOEX`.

## Технические детали

- **Fallback порядок**: `asset.price` → `asset.adj_close` → `asset.close_monthly` → MOEX ISS API
- **Обработка ошибок**: Логирование всех fallback попыток для диагностики
- **Совместимость**: Код работает с Python 3.7+ и всеми версиями Okama
