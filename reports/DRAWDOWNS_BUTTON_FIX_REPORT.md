# Отчет об исправлении кнопки Drawdowns

## Дата исправления
2025-08-31

## Описание проблемы

Пользователь сообщил, что при нажатии на кнопку "Drawdowns" в портфеле появляется ошибка:
```
❌ Данные о сравнении не найдены. Выполните команду /compare заново.
```

## 🔍 Результаты диагностики

### Причина проблемы

В обработчике callback была дублирующаяся логика для кнопки "Drawdowns":

1. **Строка 1909**: `callback_data.startswith('drawdowns_')` → `_handle_drawdowns_button` (для /compare)
2. **Строка 1949**: `callback_data.startswith('drawdowns_')` → `_handle_portfolio_drawdowns_button` (для /portfolio)

**Проблема**: Первый обработчик всегда выполнялся первым и искал данные о сравнении вместо данных о портфеле, что приводило к ошибке.

### Неправильная логика
```python
if callback_data.startswith('drawdowns_'):
    # Всегда вызывался для любых drawdowns
    await self._handle_drawdowns_button(update, context, symbols)
elif callback_data.startswith('drawdowns_'):
    # Никогда не выполнялся из-за первого условия
    await self._handle_portfolio_drawdowns_button(update, context, symbols)
```

## ✅ Исправления

### 1. Умная логика определения типа анализа

**Решение**: Добавлена проверка `last_analysis_type` из контекста пользователя для определения правильного обработчика.

**Новая логика**:
```python
if callback_data.startswith('drawdowns_'):
    symbols = callback_data.replace('drawdowns_', '').split(',')
    
    # Check user context to determine which type of analysis this is
    user_id = update.effective_user.id
    user_context = self._get_user_context(user_id)
    last_analysis_type = user_context.get('last_analysis_type')
    
    if last_analysis_type == 'portfolio':
        await self._handle_portfolio_drawdowns_button(update, context, symbols)
    else:
        await self._handle_drawdowns_button(update, context, symbols)
```

### 2. Удаление дублирующегося кода

**Удалено**: Второе условие `elif callback_data.startswith('drawdowns_')` которое никогда не выполнялось.

### 3. Улучшенное логирование

**Добавлено**: Дополнительное логирование в `_handle_portfolio_drawdowns_button` для диагностики:
- Логирование символов из кнопки
- Логирование финальных символов
- Логирование данных из контекста

## 📊 Как это работает

### Сценарий 1: После команды /portfolio
```
1. Пользователь: /portfolio LQDT.MOEX:0.78 OBLG.MOEX:0.16 GOLD.MOEX:0.06
2. Бот сохраняет: last_analysis_type = 'portfolio'
3. Пользователь нажимает: кнопку "Drawdowns"
4. Бот проверяет: last_analysis_type == 'portfolio' ✅
5. Бот вызывает: _handle_portfolio_drawdowns_button ✅
6. Результат: График просадок портфеля ✅
```

### Сценарий 2: После команды /compare
```
1. Пользователь: /compare SBER.MOEX GAZP.MOEX
2. Бот сохраняет: last_analysis_type = 'comparison'
3. Пользователь нажимает: кнопку "Drawdowns"
4. Бот проверяет: last_analysis_type != 'portfolio' ✅
5. Бот вызывает: _handle_drawdowns_button ✅
6. Результат: График просадок сравнения ✅
```

## 🎯 Результат

**ПРОБЛЕМА РЕШЕНА** ✅

- ✅ Кнопка "Drawdowns" теперь работает корректно для портфелей
- ✅ Сохранена совместимость с командой /compare
- ✅ Добавлено умное определение типа анализа
- ✅ Улучшено логирование для диагностики

## 📝 Технические детали

### Файлы изменены:
- `bot.py` - метод `button_callback`
- `bot.py` - метод `_handle_portfolio_drawdowns_button`

### Ключевые изменения:
1. **Умная диспетчеризация**: Определение правильного обработчика по типу анализа
2. **Удаление дублирования**: Устранение конфликтующих условий
3. **Улучшенное логирование**: Больше информации для диагностики

### Обратная совместимость:
- ✅ Все существующие функции работают без изменений
- ✅ Команда /compare по-прежнему использует свой обработчик
- ✅ Команда /portfolio использует правильный обработчик
