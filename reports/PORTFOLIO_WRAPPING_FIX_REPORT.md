# Отчет об исправлении проблемы с излишним обертыванием портфелей

## Проблема

При сравнении портфелей с активами наблюдалось излишнее обертывание портфелей, например:
- `portfolio_3460.PF (portfolio_8628.PF)` - портфель отображался с двойным именем

## Причина проблемы

1. **При создании портфеля** (команда `/portfolio`):
   - Okama создает портфель и присваивает ему символ типа `portfolio_3460.PF`
   - Этот символ сохраняется в контексте как `portfolio_symbol`

2. **При восстановлении портфеля** (команда `/compare`):
   - Портфель восстанавливается из контекста с правильным именем
   - НО при создании нового объекта `ok.Portfolio()` Okama присваивает ему НОВЫЙ символ типа `portfolio_8628.PF`
   - В результате получается `portfolio_3460.PF (portfolio_8628.PF)` - излишнее обертывание

## Решение

### 1. Сохранение оригинального символа портфеля в контексте

В функции восстановления портфелей из контекста (строка 2159) добавлено сохранение оригинального символа:

```python
portfolio_contexts.append({
    'symbol': f"{symbol} ({', '.join(portfolio_symbols)})",  # Descriptive name with asset composition
    'portfolio_symbols': portfolio_symbols,
    'portfolio_weights': portfolio_weights,
    'portfolio_currency': portfolio_currency,
    'portfolio_object': portfolio,
    'original_portfolio_symbol': portfolio_symbol  # Store original portfolio symbol
})
```

### 2. Использование существующего объекта портфеля

В функции сравнения портфелей (строки 2255-2266) изменена логика создания портфелей:

```python
# Use existing portfolio object if available, otherwise create new one
if 'portfolio_object' in portfolio_context and portfolio_context['portfolio_object'] is not None:
    portfolio = portfolio_context['portfolio_object']
    self.logger.info(f"Using existing portfolio object for {portfolio_context['symbol']}")
else:
    # Create portfolio object using okama
    portfolio = ok.Portfolio(
        portfolio_context['portfolio_symbols'], 
        weights=portfolio_context['portfolio_weights'], 
        ccy=portfolio_context['portfolio_currency']
    )
    self.logger.info(f"Created new portfolio object for {portfolio_context['symbol']}")
```

### 3. Добавление поля для обычных активов

Для обычных активов также добавлено поле `original_portfolio_symbol` (строка 2180):

```python
portfolio_contexts.append({
    'symbol': symbol,
    'portfolio_symbols': [symbol],
    'portfolio_weights': [1.0],
    'portfolio_currency': None,  # Will be determined later
    'portfolio_object': None,
    'original_portfolio_symbol': None  # Not a portfolio
})
```

## Результат

Теперь при сравнении портфелей с активами:
- Портфели сохраняют свои оригинальные имена
- Нет излишнего обертывания в виде `portfolio_3460.PF (portfolio_8628.PF)`
- Портфели отображаются корректно как `portfolio_3460.PF`

## Файлы изменены

- `bot.py` - основные изменения в логике работы с портфелями

## Тестирование

Рекомендуется протестировать:
1. Создание портфеля командой `/portfolio`
2. Сравнение портфеля с активом командой `/compare`
3. Сравнение двух портфелей командой `/compare`
4. Проверка отображения имен портфелей в результатах

## Дата исправления

2024-12-19
