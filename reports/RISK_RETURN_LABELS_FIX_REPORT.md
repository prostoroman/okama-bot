# Отчет об исправлении отображения названий на графике Risk/Return

## Проблема

На графике Risk/Return (CAGR) отображались технические названия портфелей (например, "PF_1", "portfolio_123.PF") вместо описательных названий с составом активов. Это затрудняло сопоставление портфелей с конкретными активами.

## Причина

В функции `_handle_risk_return_compare_button` использовались названия из `portfolio_contexts`, где поле `'symbol'` содержало технический символ портфеля, а не описательное название с составом активов.

## Решение

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

## Результат

Теперь на графике Risk/Return будут отображаться названия вида:
- "PF_1 (SPY.US, QQQ.US, BND.US)" вместо "PF_1"
- "portfolio_123.PF (SBER.MOEX, GAZP.MOEX)" вместо "portfolio_123.PF"

Это позволяет пользователям легко сопоставить портфель с его составом активов.

## Файлы изменены

- `bot.py` - строка 2018: обновлено формирование `portfolio_contexts`

## Тестирование

Исправление требует тестирования с различными типами портфелей:
- Портфели с разным количеством активов
- Портфели с разными валютами
- Смешанные сравнения (портфели + отдельные активы)

## Дата исправления

2024-12-19
