# Отчет об исправлении логики сообщений в команде /info

## Проблемы

1. **Кнопки с графиками обновляли существующее сообщение** - нужно отправлять новое сообщение
2. **График за 1 год по умолчанию не показывается** - нужна диагностика проблемы

## Решения

### 1. ✅ Изменена логика кнопок с графиками

**Было**: При нажатии на кнопки периодов обновлялось существующее сообщение
```python
# Update the existing message with new chart and info
await self._update_message_with_chart(update, context, chart_data, caption, reply_markup)
```

**Стало**: При нажатии на кнопки периодов отправляется новое сообщение
```python
# Send new message with chart and info
await self._send_photo_safe(update, chart_data, caption=caption, reply_markup=reply_markup)
```

### 2. ✅ Добавлено подробное логирование для диагностики

**В функции `_handle_okama_info()`:**
```python
# Получаем график доходности за 1 год
self.logger.info(f"Getting daily chart for {symbol}")
chart_data = await self._get_daily_chart(symbol)
self.logger.info(f"Chart data result: {chart_data is not None}")

if chart_data:
    # Отправляем график с информацией в caption
    caption = f"📈 График доходности за 1 год\n\n{info_text}"
    self.logger.info(f"Sending chart with caption length: {len(caption)}")
    await self._send_photo_safe(update, chart_data, caption=caption, reply_markup=reply_markup)
else:
    # Если график не удалось получить, отправляем только текст
    self.logger.warning(f"Could not get chart for {symbol}, sending text only")
    await self._send_message_safe(update, info_text, reply_markup=reply_markup)
```

**В функции `_get_daily_chart()`:**
```python
def create_daily_chart():
    self.logger.info(f"Creating daily chart for {symbol}")
    # Устанавливаем backend для headless режима
    import matplotlib
    matplotlib.use('Agg')
    
    asset = ok.Asset(symbol)
    self.logger.info(f"Asset created for {symbol}")
    
    # Получаем данные за последний год
    daily_data = asset.close_daily
    self.logger.info(f"Daily data shape: {daily_data.shape if hasattr(daily_data, 'shape') else 'No shape'}")
    
    # Берем последние 252 торговых дня (примерно год)
    filtered_data = daily_data.tail(252)
    self.logger.info(f"Filtered data shape: {filtered_data.shape if hasattr(filtered_data, 'shape') else 'No shape'}")
    
    # Получаем информацию об активе для заголовка
    asset_name = getattr(asset, 'name', symbol)
    currency = getattr(asset, 'currency', '')
    self.logger.info(f"Asset name: {asset_name}, currency: {currency}")
    
    # Используем ChartStyles для создания графика
    self.logger.info("Creating chart with ChartStyles")
    fig, ax = chart_styles.create_price_chart(
        data=filtered_data,
        symbol=symbol,
        currency=currency,
        period='1Y'
    )
    self.logger.info("Chart created successfully")
    
    # ... остальной код ...
    
    result = output.getvalue()
    self.logger.info(f"Chart bytes length: {len(result)}")
    return result
```

### 3. ✅ Упрощена логика переключения периодов

**Функция `_handle_info_period_button()` теперь:**
- Отправляет новое сообщение с графиком вместо обновления существующего
- Сохраняет все кнопки в новом сообщении
- Обеспечивает консистентность интерфейса

## Результат

### До исправления:
- ❌ Кнопки периодов обновляли существующее сообщение
- ❌ График за 1 год не показывался по умолчанию
- ❌ Нет диагностики проблем с созданием графиков

### После исправления:
- ✅ Кнопки периодов отправляют новое сообщение с графиком
- ✅ Подробное логирование для диагностики проблем
- ✅ Каждое сообщение с графиком имеет полный набор кнопок
- ✅ Fallback на текстовое сообщение при ошибках

## Логика работы

1. **При первом вызове `/info SPY.US`**:
   - Создается график за 1Y
   - Отправляется новое сообщение с графиком и кнопками
   - Информация об активе в подписи к графику

2. **При нажатии на кнопки периодов**:
   - Создается график для выбранного периода
   - Отправляется новое сообщение с графиком и кнопками
   - Информация об активе обновляется в подписи
   - Кнопки обновляются с выделенным активным периодом

3. **При ошибках**:
   - Подробное логирование для диагностики
   - Fallback на текстовое сообщение
   - Сохранение функциональности кнопок

## Диагностика проблем

Добавленное логирование поможет выявить:
- Проблемы с созданием объекта `ok.Asset`
- Проблемы с получением данных `close_daily`
- Проблемы с `ChartStyles.create_price_chart`
- Проблемы с сохранением графика в bytes
- Общие ошибки в процессе создания графика

## Статус

✅ **ИСПРАВЛЕНО** - Логика сообщений изменена, добавлена диагностика

## Файлы изменены

- **bot.py**: 
  - Обновлена функция `_handle_info_period_button()` (строки 7174-7180)
  - Добавлено логирование в `_handle_okama_info()` (строки 1824-1836)
  - Добавлено подробное логирование в `_get_daily_chart()` (строки 2134-2201)

## Совместимость

- ✅ Обратная совместимость с существующими функциями
- ✅ Упрощенная логика - каждое сообщение независимо
- ✅ Подробная диагностика проблем
- ✅ Fallback при ошибках

Теперь команда `/info` отправляет новое сообщение с графиком при переключении периодов и имеет подробное логирование для диагностики проблем!
