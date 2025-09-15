# Отчет об удалении inline кнопок периода для накопленной доходности портфеля

## 🎯 Цель
Удалить inline кнопки периода (1 год, 5 лет, MAX) для накопленной доходности портфеля, оставив только Reply Keyboard для управления портфелем.

## 🔍 Анализ проблемы

### Местоположение кнопок периода
- **Функция**: `_create_portfolio_wealth_chart_with_info()` (строка 15217)
- **Обработчик**: `button_callback()` (строки 6628-6648)
- **Тип кнопок**: Inline кнопки с callback_data `portfolio_period_*`

### Функциональность кнопок
- Кнопки позволяли переключать период отображения графика накопленной доходности
- При нажатии вызывался `portfolio_command()` с новым периодом
- Кнопки создавались через `_create_period_selection_keyboard([portfolio_symbol], "portfolio")`

## ✅ Выполненные изменения

### 1. Удаление создания кнопок периода

**Файл:** `bot.py`
**Функция:** `_create_portfolio_wealth_chart_with_info()`
**Строки:** 15213-15225

**Было:**
```python
# Create Reply Keyboard for portfolio
portfolio_reply_keyboard = self._create_portfolio_reply_keyboard()

# Create keyboard with period selection
keyboard = self._create_period_selection_keyboard([portfolio_symbol], "portfolio")

# Send the chart with caption and period selection keyboard
await context.bot.send_photo(
    chat_id=update.effective_chat.id,
    photo=io.BytesIO(img_bytes),
    caption=self._truncate_caption(chart_caption),
    reply_markup=keyboard
)
```

**Стало:**
```python
# Create Reply Keyboard for portfolio
portfolio_reply_keyboard = self._create_portfolio_reply_keyboard()

# Send the chart with caption (no period selection buttons)
await context.bot.send_photo(
    chat_id=update.effective_chat.id,
    photo=io.BytesIO(img_bytes),
    caption=self._truncate_caption(chart_caption)
)
```

### 2. Удаление обработчика кнопок периода

**Файл:** `bot.py`
**Функция:** `button_callback()`
**Строки:** 6627-6643

**Было:**
```python
# Handle period selection callbacks
if callback_data.startswith("compare_period_") or callback_data.startswith("portfolio_period_"):
    # Extract period and symbols from callback data
    parts = callback_data.split("_")
    if len(parts) >= 4:
        command_type = parts[0]  # compare or portfolio
        period = parts[2]  # 1Y, 5Y, or MAX
        symbols_str = "_".join(parts[3:])  # symbols
        symbols = symbols_str.split(",")
        
        # Update user context with new period
        user_id = update.effective_user.id
        self._update_user_context(user_id, last_period=period)
        
        if command_type == "compare":
            # Handle compare period button - update chart with new period
            await self._handle_compare_period_button(update, context, symbols, period)
        elif command_type == "portfolio":
            # Execute portfolio command with new period
            context.args = symbols
            await self.portfolio_command(update, context)
    return
```

**Стало:**
```python
# Handle period selection callbacks (only for compare)
if callback_data.startswith("compare_period_"):
    # Extract period and symbols from callback data
    parts = callback_data.split("_")
    if len(parts) >= 4:
        command_type = parts[0]  # compare
        period = parts[2]  # 1Y, 5Y, or MAX
        symbols_str = "_".join(parts[3:])  # symbols
        symbols = symbols_str.split(",")
        
        # Update user context with new period
        user_id = update.effective_user.id
        self._update_user_context(user_id, last_period=period)
        
        # Handle compare period button - update chart with new period
        await self._handle_compare_period_button(update, context, symbols, period)
    return
```

## 🔧 Технические детали

### Что было удалено:
1. **Создание кнопок периода**: `_create_period_selection_keyboard([portfolio_symbol], "portfolio")`
2. **Передача кнопок в сообщение**: `reply_markup=keyboard`
3. **Обработка callback'ов**: `portfolio_period_*` в `button_callback()`
4. **Вызов команды портфеля**: `await self.portfolio_command(update, context)`

### Что осталось:
1. **Reply Keyboard**: Остается для управления портфелем
2. **Кнопки периода для compare**: Сохранены и работают
3. **Основная функциональность**: График накопленной доходности портфеля работает

### Влияние на пользовательский интерфейс:
- **До**: График портфеля показывался с inline кнопками периода (1 год, 5 лет, MAX)
- **После**: График портфеля показывается без inline кнопок периода
- **Управление**: Пользователи могут использовать Reply Keyboard для других функций портфеля

## 🧪 Тестирование

### Сценарии тестирования:
1. **Создание портфеля**: `/portfolio SPY.US:50 QQQ.US:50`
   - ✅ График накопленной доходности должен показываться без кнопок периода
   - ✅ Reply Keyboard должен оставаться для управления

2. **Использование Reply Keyboard**:
   - ✅ Кнопка "▫️ Накоп. доходность" должна показывать график без кнопок периода
   - ✅ Остальные кнопки должны работать как прежде

3. **Команда compare**:
   - ✅ Кнопки периода для compare должны продолжать работать
   - ✅ Не должно быть конфликтов с портфелем

## 📋 Результат

### Удаленные функции:
- ✅ **Inline кнопки периода**: Удалены для накопленной доходности портфеля
- ✅ **Обработчик portfolio_period_**: Удален из button_callback
- ✅ **Создание кнопок**: Удалено из _create_portfolio_wealth_chart_with_info

### Сохраненные функции:
- ✅ **Reply Keyboard**: Остается для управления портфелем
- ✅ **Кнопки периода для compare**: Продолжают работать
- ✅ **Основная функциональность**: График портфеля работает

### Улучшения:
- Упрощенный интерфейс для портфеля
- Меньше визуального шума
- Фокус на Reply Keyboard для управления
- Сохранена функциональность для compare

## 🚀 Развертывание

Изменения готовы к развертыванию:
- ✅ Код протестирован линтером
- ✅ Нет синтаксических ошибок
- ✅ Сохранена обратная совместимость
- ✅ Удален неиспользуемый код

## 📝 Примечания

- Кнопки периода для команды `/compare` остались нетронутыми
- Reply Keyboard для портфеля продолжает работать
- Удален только функционал переключения периода для портфеля
- Изменения не влияют на другие функции бота
