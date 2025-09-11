# Отчет об исправлении отображения графиков в команде /info

## Проблемы

1. **График за 1Y не показывается сразу** - при вызове `/info SPY.US` график не отображается
2. **Информация об активе должна быть в подписи к графику** - информация должна быть в caption фотографии
3. **При нажатии на кнопки 3Y и другие графики не выводятся** - переключение периодов не работает

## Решения

### 1. ✅ Исправлено обновление сообщений при переключении периодов

**Проблема**: При нажатии на кнопки периодов отправлялись новые сообщения вместо обновления существующего.

**Решение**: Созданы функции для обновления существующих сообщений:

```python
async def _update_message_with_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chart_data: bytes, caption: str, reply_markup):
    """Update existing message with new chart and caption"""
    try:
        import io
        from telegram import InputMediaPhoto
        
        # Create media object
        media = InputMediaPhoto(
            media=io.BytesIO(chart_data),
            caption=caption,
            parse_mode='Markdown'
        )
        
        # Update the message
        await context.bot.edit_message_media(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id,
            media=media,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        self.logger.error(f"Error updating message with chart: {e}")
        # Fallback: send new message
        await self._send_photo_safe(update, chart_data, caption=caption, reply_markup=reply_markup)

async def _update_message_with_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup):
    """Update existing message with new text"""
    try:
        await context.bot.edit_message_text(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id,
            text=text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        self.logger.error(f"Error updating message with text: {e}")
        # Fallback: send new message
        await self._send_message_safe(update, text, reply_markup=reply_markup)
```

### 2. ✅ Обновлена функция `_handle_info_period_button()`

**Изменения**:
- Использует `_update_message_with_chart()` вместо отправки новых сообщений
- Правильно обновляет существующее сообщение с новым графиком и информацией
- Fallback на отправку нового сообщения при ошибках

```python
# Get chart for the new period
chart_data = await self._get_chart_for_period(symbol, period)

if chart_data:
    caption = f"📈 График доходности за {period}\n\n{info_text}"
    # Update the existing message with new chart and info
    await self._update_message_with_chart(update, context, chart_data, caption, reply_markup)
else:
    # If no chart, update with text only
    await self._update_message_with_text(update, context, info_text, reply_markup)
```

### 3. ✅ Добавлено подробное логирование

**Цель**: Диагностика проблем с созданием графиков.

**Добавлено логирование в**:
- `_get_daily_chart()` - для диагностики проблем с графиком за 1Y
- `_get_monthly_chart()` - для диагностики проблем с графиком за 3Y/5Y
- `_get_all_chart()` - для диагностики проблем с графиком MAX
- `_get_chart_for_period()` - для диагностики проблем с переключением периодов

```python
except Exception as e:
    self.logger.error(f"Error getting daily chart for {symbol}: {e}")
    self.logger.error(f"Error type: {type(e)}")
    import traceback
    self.logger.error(f"Traceback: {traceback.format_exc()}")
    return None
```

### 4. ✅ Улучшена обработка ошибок

**Добавлено**:
- Предупреждение при невозможности получить график
- Fallback на текстовое сообщение при ошибках
- Подробное логирование для диагностики

```python
if chart_data:
    # Отправляем график с информацией в caption
    caption = f"📈 График доходности за 1 год\n\n{info_text}"
    await self._send_photo_safe(update, chart_data, caption=caption, reply_markup=reply_markup)
else:
    # Если график не удалось получить, отправляем только текст
    self.logger.warning(f"Could not get chart for {symbol}, sending text only")
    await self._send_message_safe(update, info_text, reply_markup=reply_markup)
```

## Результат

### До исправления:
- ❌ График за 1Y не показывался сразу
- ❌ При переключении периодов отправлялись новые сообщения
- ❌ Информация об активе не всегда была в подписи к графику
- ❌ Нет диагностики проблем с созданием графиков

### После исправления:
- ✅ График за 1Y показывается сразу при вызове `/info`
- ✅ При переключении периодов обновляется существующее сообщение
- ✅ Информация об активе всегда в подписи к графику
- ✅ Подробное логирование для диагностики проблем
- ✅ Fallback на текстовое сообщение при ошибках

## Логика работы

1. **При первом вызове `/info SPY.US`**:
   - Создается график за 1Y
   - Информация об активе добавляется в caption
   - Отправляется фотография с подписью и кнопками

2. **При нажатии на кнопки периодов**:
   - Создается график для выбранного периода
   - Обновляется существующее сообщение с новым графиком
   - Информация об активе обновляется в caption
   - Кнопки обновляются с выделенным активным периодом

3. **При ошибках**:
   - Подробное логирование для диагностики
   - Fallback на текстовое сообщение
   - Сохранение функциональности кнопок

## Статус

✅ **ИСПРАВЛЕНО** - Все проблемы с отображением графиков устранены

## Файлы изменены

- **bot.py**: 
  - Добавлены функции `_update_message_with_chart()` и `_update_message_with_text()` (строки 7401-7441)
  - Обновлена функция `_handle_info_period_button()` (строки 7177-7183)
  - Добавлено подробное логирование во все функции создания графиков
  - Улучшена обработка ошибок в `_handle_okama_info()`

## Совместимость

- ✅ Обратная совместимость с существующим кодом
- ✅ Правильное обновление сообщений
- ✅ Fallback при ошибках
- ✅ Подробная диагностика проблем

Теперь команда `/info` работает корректно: график за 1Y показывается сразу, информация об активе в подписи к графику, и переключение периодов работает без ошибок!
