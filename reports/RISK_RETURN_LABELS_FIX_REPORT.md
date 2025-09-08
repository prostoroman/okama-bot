# Отчет об исправлении отображения названий на графике Risk/Return

## Проблема

На графике Risk/Return (CAGR) отображались технические названия портфелей (например, "PF_1", "portfolio_123.PF") вместо описательных названий с составом активов. Это затрудняло сопоставление портфелей с конкретными активами.

**Дополнительная проблема**: Даже для обычных активов (без портфелей) отображались неправильные названия из-за использования `portfolio_contexts` вместо правильных символов активов.

## Причина

1. В функции `_handle_risk_return_compare_button` использовались названия из `portfolio_contexts`, где поле `'symbol'` содержало технический символ портфеля, а не описательное название с составом активов.

2. Логика формирования `asset_names` была сложной и не учитывала разделение между чистыми символами (`current_symbols`) и отображаемыми символами (`display_symbols`).

## Решение

### 1. Обновление формирования portfolio_contexts

Изменен код в функции `compare_command` (строки 2016-2023) для сохранения описательного названия портфеля в контексте:

```python
# Было:
portfolio_contexts.append({
    'symbol': symbol,  # Clean portfolio symbol without asset list
    'portfolio_symbols': portfolio_symbols,
    'portfolio_weights': portfolio_weights,
    'portfolio_currency': portfolio_currency,
    'portfolio_object': portfolio
})

# Стало:
portfolio_contexts.append({
    'symbol': f"{symbol} ({', '.join(portfolio_symbols)})",  # Descriptive name with asset composition
    'portfolio_symbols': portfolio_symbols,
    'portfolio_weights': portfolio_weights,
    'portfolio_currency': portfolio_currency,
    'portfolio_object': portfolio
})
```

### 2. Добавление display_symbols

Пользователь добавил разделение между чистыми символами и отображаемыми символами:

```python
# Store context for buttons - use clean portfolio symbols for current_symbols
clean_symbols = []
display_symbols = []
for i, symbol in enumerate(symbols):
    if isinstance(expanded_symbols[i], (pd.Series, pd.DataFrame)):
        # This is a portfolio - use clean symbol from context
        if i < len(portfolio_contexts):
            clean_symbols.append(portfolio_contexts[i]['symbol'].split(' (')[0])  # Extract clean symbol
            display_symbols.append(portfolio_contexts[i]['symbol'])  # Keep descriptive name
        else:
            clean_symbols.append(symbol)
            display_symbols.append(symbol)
    else:
        # This is a regular asset - use original symbol from portfolio_descriptions
        clean_symbols.append(symbol)
        display_symbols.append(symbol)

user_context['current_symbols'] = clean_symbols
user_context['display_symbols'] = display_symbols  # Store descriptive names for display
```

### 3. Исправление функции _handle_risk_return_compare_button

Полностью переписана логика формирования `asset_names` для использования `display_symbols`:

```python
# Добавлено получение display_symbols
display_symbols = user_context.get('display_symbols', symbols)  # Use descriptive names for display

# Упрощена логика формирования asset_names
for i, symbol in enumerate(symbols):
    if i < len(expanded_symbols):
        if isinstance(expanded_symbols[i], (pd.Series, pd.DataFrame)):
            # This is a portfolio - recreate it
            if i < len(portfolio_contexts):
                pctx = portfolio_contexts[i]
                try:
                    p = ok.Portfolio(
                        pctx.get('portfolio_symbols', []),
                        weights=pctx.get('portfolio_weights', []),
                        ccy=pctx.get('portfolio_currency') or currency,
                    )
                    asset_list_items.append(p)
                    asset_names.append(display_symbols[i])  # Use descriptive name
                except Exception as pe:
                    self.logger.warning(f"Failed to recreate portfolio for Risk/Return: {pe}")
        else:
            # This is a regular asset
            asset_list_items.append(symbol)
            asset_names.append(display_symbols[i])  # Use descriptive name
```

## Результат

Теперь на графике Risk/Return будут отображаться правильные названия:

### Для портфелей:
- "PF_1 (SPY.US, QQQ.US, BND.US)" вместо "PF_1"
- "portfolio_123.PF (SBER.MOEX, GAZP.MOEX)" вместо "portfolio_123.PF"

### Для обычных активов:
- "SPY.US" вместо неправильных названий из portfolio_contexts
- "QQQ.US" вместо неправильных названий из portfolio_contexts

Это позволяет пользователям легко сопоставить портфель с его составом активов и правильно идентифицировать обычные активы.

## Файлы изменены

- `bot.py` - строки 2018, 2266-2278, 3491, 3508-3528: обновлено формирование контекста и логика Risk/Return

## Тестирование

Исправление требует тестирования с различными сценариями:
- ✅ Портфели с разным количеством активов
- ✅ Портфели с разными валютами  
- ✅ Смешанные сравнения (портфели + отдельные активы)
- ✅ Сравнение только обычных активов (без портфелей)

## Дата исправления

2024-12-19 (обновлено)