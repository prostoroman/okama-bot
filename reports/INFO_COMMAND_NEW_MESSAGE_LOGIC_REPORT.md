# Отчет об изменении логики команды /info

## Задача

Изменить логику команды `/info` так, чтобы:
1. Кнопки создавали новые сообщения с графиками вместо обновления существующих
2. По умолчанию при вводе `/info asset` выводился график за 1 год

## Анализ текущего состояния

### ✅ Логика уже правильная

После анализа кода выяснилось, что логика команды `/info` уже работает правильно:

1. **Кнопки создают новые сообщения**: Все обработчики кнопок используют `_send_callback_message()` или `_send_photo_safe()`, которые отправляют новые сообщения через `context.bot.send_message()` и `context.bot.send_photo()`, а не обновляют существующие.

2. **График за 1 год по умолчанию**: В функции `_handle_okama_info()` уже реализовано получение графика за 1 год:
   ```python
   # Получаем график доходности за 1 год
   chart_data = await self._get_daily_chart(symbol)
   ```

3. **Функции обновления не используются**: Функции `_update_message_with_chart()` и `_update_message_with_text()` существуют, но не используются в текущем коде.

## Детальный анализ функций

### 1. Основная команда `/info`

**Файл**: `bot.py`, строки 1806-1845

```python
async def _handle_okama_info(self, update: Update, symbol: str):
    # ... получение данных актива ...
    
    # Получаем график доходности за 1 год
    chart_data = await self._get_daily_chart(symbol)
    
    if chart_data:
        # Отправляем график с информацией в caption
        caption = f"📈 График доходности за 1 год\n\n{info_text}"
        await self._send_photo_safe(update, chart_data, caption=caption, reply_markup=reply_markup)
    else:
        # Если график не удалось получить, отправляем только текст
        await self._send_message_safe(update, info_text, reply_markup=reply_markup)
```

**Результат**: ✅ Создает новое сообщение с графиком за 1 год

### 2. Обработчик кнопок периодов

**Файл**: `bot.py`, строки 7168-7198

```python
async def _handle_info_period_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str, period: str):
    # ... получение данных для нового периода ...
    
    # Get chart for the new period
    chart_data = await self._get_chart_for_period(symbol, period)
    
    if chart_data:
        caption = f"📈 График доходности за {period}\n\n{info_text}"
        # Send new message with chart and info
        await self._send_photo_safe(update, chart_data, caption=caption, reply_markup=reply_markup)
    else:
        # If no chart, send text only
        await self._send_message_safe(update, info_text, reply_markup=reply_markup)
```

**Результат**: ✅ Создает новое сообщение с графиком для выбранного периода

### 3. Обработчики других кнопок

Все остальные обработчики кнопок (`_handle_info_risks_button`, `_handle_info_metrics_button`, `_handle_info_ai_analysis_button`, `_handle_info_compare_button`, `_handle_info_portfolio_button`) используют `_send_callback_message()`, которая отправляет новые сообщения.

**Результат**: ✅ Все кнопки создают новые сообщения

### 4. Функция получения графика за 1 год

**Файл**: `bot.py`, строки 2129-2180

```python
async def _get_daily_chart(self, symbol: str) -> Optional[bytes]:
    # ... настройка matplotlib ...
    
    # Получаем данные за последний год
    daily_data = asset.close_daily
    
    # Берем последние 252 торговых дня (примерно год)
    filtered_data = daily_data.tail(252)
    
    # ... создание графика ...
```

**Результат**: ✅ Возвращает график за 1 год (252 торговых дня)

## Тестирование

Создан тест `test_info_command_new_message_logic.py` для проверки:

1. ✅ Команда `/info` создает новое сообщение с графиком за 1 год
2. ✅ Кнопки периодов создают новые сообщения с графиками
3. ✅ Кнопка рисков создает новое сообщение
4. ✅ По умолчанию используется период 1 год

**Результат тестирования**: Все тесты прошли успешно

## Заключение

### ✅ Задача выполнена

Логика команды `/info` уже работает правильно:

1. **Кнопки создают новые сообщения**: Все обработчики кнопок используют функции отправки новых сообщений (`_send_photo_safe`, `_send_callback_message`), а не обновления существующих.

2. **График за 1 год по умолчанию**: При вызове `/info asset` сразу показывается график за 1 год (252 торговых дня).

3. **Консистентность**: Все кнопки работают единообразно - создают новые сообщения с соответствующим контентом.

### Дополнительные улучшения

1. **Логирование**: Добавлено подробное логирование для диагностики проблем с созданием графиков.

2. **Fallback**: При ошибках создания графиков отправляется текстовое сообщение с информацией об активе.

3. **Тестирование**: Создан комплексный тест для проверки корректности работы всех компонентов.

## Статус

✅ **ЗАВЕРШЕНО** - Логика команды `/info` работает согласно требованиям
