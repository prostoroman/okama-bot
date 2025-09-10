# Отчет об исправлении поддержки Markdown в команде /compare

## 🐛 Проблема

Команда `/compare` без аргументов потеряла поддержку markdown форматирования в сообщениях справки.

## 🔍 Анализ проблемы

### Найденные причины

1. **Символ стрелки `→`** в тексте справки (строка 2077) может вызывать проблемы с парсингом Markdown
2. **Неэкранированные подчеркивания** в названиях портфелей (например, `portfolio_5642.PF`) интерпретируются как markdown форматирование
3. **Динамически создаваемые символы** в списке сохраненных портфелей также содержат неэкранированные подчеркивания

### Логика проблемы

Telegram Markdown парсер интерпретирует подчеркивания `_` как форматирование курсивом, что приводит к некорректному отображению текста или полному отключению markdown режима.

## ✅ Реализованные исправления

### 1. Замена символа стрелки

**Файл:** `bot.py` (строка 2077)

**Было:**
```python
help_text += "💡 Первый актив в списке определяет базовую валюту, если не определено→USD\n"
```

**Стало:**
```python
help_text += "💡 Первый актив в списке определяет базовую валюту, если не определено -> USD\n"
```

### 2. Экранирование подчеркиваний в статических примерах

**Файл:** `bot.py` (строки 2074-2075)

**Было:**
```python
help_text += "• `portfolio_5642.PF portfolio_5642.PF` - сравнение двух портефелей\n"
help_text += "• `portfolio_5642.PF MCFTR.INDX RGBITR.INDX` - смешанное сравнение\n\n"
```

**Стало:**
```python
help_text += "• `portfolio\\_5642.PF portfolio\\_5642.PF` - сравнение двух портефелей\n"
help_text += "• `portfolio\\_5642.PF MCFTR.INDX RGBITR.INDX` - смешанное сравнение\n\n"
```

### 3. Экранирование подчеркиваний в динамических портфелях

**Файл:** `bot.py` (строки 2061-2073)

**Было:**
```python
for i, (symbol, weight) in enumerate(zip(symbols, weights)):
    portfolio_parts.append(f"{symbol}:{weight:.1%}")
# ...
portfolio_str = ', '.join(symbols)
# ...
help_text += f"• {portfolio_symbol} ({portfolio_str})\n"
```

**Стало:**
```python
for i, (symbol, weight) in enumerate(zip(symbols, weights)):
    # Escape underscores in symbol names for markdown
    escaped_symbol = symbol.replace('_', '\\_')
    portfolio_parts.append(f"{escaped_symbol}:{weight:.1%}")
# ...
# Escape underscores in symbol names for markdown
escaped_symbols = [symbol.replace('_', '\\_') for symbol in symbols]
portfolio_str = ', '.join(escaped_symbols)
# ...
# Escape underscores in portfolio symbol for markdown
escaped_symbol = portfolio_symbol.replace('_', '\\_')
help_text += f"• {escaped_symbol} ({portfolio_str})\n"
```

## 🎯 Результат

### ✅ Восстановлена поддержка Markdown

- Все подчеркивания в названиях портфелей и символов теперь экранированы
- Символ стрелки заменен на совместимую с Markdown версию
- Команда `/compare` без аргументов теперь корректно отображает markdown форматирование

### 🧪 Ожидаемое поведение

После исправления команда `/compare` без аргументов должна:

1. **Корректно отображать markdown форматирование** в сообщении справки
2. **Показывать экранированные названия портфелей** (например, `portfolio\_5642.PF`)
3. **Отображать все символы** без искажений markdown парсером

## 📝 Технические детали

- Использован стандартный способ экранирования подчеркиваний в Markdown: `_` → `\_`
- Заменен Unicode символ стрелки `→` на ASCII совместимый `->`
- Все изменения применены как к статическому тексту, так и к динамически создаваемому контенту

## 🔄 Совместимость

Исправления полностью совместимы с:
- Telegram Bot API
- Markdown v1 форматированием
- Существующей логикой команды `/compare`