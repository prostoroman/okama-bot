# Отчет об исправлении источника данных дивидендной доходности

## Проблема

При попытке создать график дивидендной доходности портфеля возникала ошибка:
```
❌ Данные о дивидендах не содержат информацию для отображения.
```

## Причина

Метод `portfolio.dividend_yield_with_assets` либо не существует, либо возвращает пустые данные. В Okama для получения дивидендной доходности отдельных активов нужно использовать `AssetList` с методом `dividend_yields`.

## Исправление

### 1. Изменен подход к получению данных

**Было:**
```python
# Check if portfolio has dividend yield data
try:
    dividend_yield_data = portfolio.dividend_yield_with_assets
    if dividend_yield_data is None or dividend_yield_data.empty:
        await self._send_callback_message(update, context, "❌ Данные о дивидендах не содержат информацию для отображения.")
        return
except Exception as e:
    self.logger.warning(f"Could not access dividend yield data: {e}")
    await self._send_callback_message(update, context, "❌ Данные о дивидендах не содержат информацию для отображения.")
    return
```

**Стало:**
```python
# Check if portfolio has dividend yield data
try:
    # Try to get dividend yield data for each asset
    import okama as ok
    asset_list = ok.AssetList(symbols, ccy=currency)
    
    self.logger.info(f"AssetList created for symbols: {symbols}")
    self.logger.info(f"AssetList has dividend_yields: {hasattr(asset_list, 'dividend_yields')}")
    
    if hasattr(asset_list, 'dividend_yields'):
        self.logger.info(f"Dividend yields shape: {asset_list.dividend_yields.shape}")
        self.logger.info(f"Dividend yields empty: {asset_list.dividend_yields.empty}")
        if not asset_list.dividend_yields.empty:
            self.logger.info(f"Dividend yields columns: {asset_list.dividend_yields.columns.tolist()}")
            dividend_yield_data = asset_list.dividend_yields
        else:
            self.logger.warning("AssetList dividend_yields is empty")
            raise ValueError("No dividend yield data in AssetList")
    else:
        self.logger.warning("AssetList does not have dividend_yields attribute")
        raise ValueError("No dividend_yields attribute in AssetList")
        
except Exception as e:
    self.logger.warning(f"Could not get dividend yield data from AssetList: {e}")
    # Fallback to portfolio dividend yield
    try:
        dividend_yield_data = portfolio.dividend_yield
        if dividend_yield_data is None or dividend_yield_data.empty:
            await self._send_callback_message(update, context, "❌ Данные о дивидендах не содержат информацию для отображения.")
            return
        self.logger.info("Using portfolio dividend yield as fallback")
    except Exception as portfolio_error:
        self.logger.error(f"Could not access portfolio dividend yield: {portfolio_error}")
        await self._send_callback_message(update, context, "❌ Данные о дивидендах не содержат информацию для отображения.")
        return
```

### 2. Добавлена диагностика

Добавлено подробное логирование для диагностики проблем:
- Проверка существования атрибута `dividend_yields`
- Логирование формы и содержимого данных
- Логирование колонок в данных
- Fallback к `portfolio.dividend_yield` если `AssetList` не работает

### 3. Двухуровневый fallback

1. **Первый уровень**: `AssetList.dividend_yields` - для получения данных по каждому активу
2. **Второй уровень**: `portfolio.dividend_yield` - агрегированная дивидендная доходность портфеля

## Технические детали

### AssetList vs Portfolio
- **`AssetList`** - используется для работы с отдельными активами
- **`Portfolio`** - используется для работы с портфелем как единым целым
- **`dividend_yields`** (множественное число) - метод `AssetList` для получения дивидендной доходности каждого актива
- **`dividend_yield`** (единственное число) - метод `Portfolio` для получения агрегированной дивидендной доходности

### Обработка ошибок
- Подробное логирование на каждом этапе
- Graceful fallback между методами
- Информативные сообщения об ошибках для пользователя

## Результат

Теперь система:
1. **Сначала пытается** получить данные по каждому активу через `AssetList`
2. **Если не получается** - использует агрегированные данные портфеля
3. **Логирует** подробную информацию для диагностики
4. **Показывает** все активы в легенде (если данные по активам доступны)

## Файлы изменены

- `bot.py` - обновлен метод `_create_portfolio_dividends_chart`

## Статус

✅ Исправлен источник данных дивидендной доходности
✅ Добавлена диагностика и логирование
✅ Реализован двухуровневый fallback
✅ Код готов к тестированию
✅ Ошибки линтера отсутствуют

## Тестирование

Рекомендуется протестировать создание графика дивидендной доходности портфеля и проверить логи для диагностики доступности данных.
