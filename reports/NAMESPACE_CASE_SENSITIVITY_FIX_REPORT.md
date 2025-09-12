# Отчет об исправлении проблемы с регистром namespace

## Проблема
При использовании команды `/compare` с символами, содержащими lowercase namespace (например, `sber.moex`, `lqdt.moex`), возникала ошибка:

```
❌ Ошибка при создании сравнения: moex is not in allowed assets namespaces: 'US', 'LSE', 'XETR', 'XFRA', 'XSTU', 'XAMS', 'MOEX', 'XTAE', 'PIF', 'FX', 'CC', 'INDX', 'COMM', 'RE', 'CBR', 'PF'
```

## Анализ проблемы
1. **Источник ошибки**: Okama библиотека ожидает namespace в uppercase формате (например, `MOEX`)
2. **Пользовательский ввод**: Пользователи часто вводят namespace в lowercase (например, `moex`)
3. **Отсутствие нормализации**: В коде не было механизма для конвертации lowercase namespace в uppercase

## Решение
Добавлена функция нормализации namespace и интегрирована в обработку символов:

### 1. Новая функция `_normalize_symbol_namespace`
```python
def _normalize_symbol_namespace(self, symbol: str) -> str:
    """
    Нормализовать регистр namespace в символе
    
    Args:
        symbol: Символ в формате TICKER.NAMESPACE
        
    Returns:
        str: Символ с нормализованным namespace (uppercase)
    """
    if '.' not in symbol:
        return symbol
    
    ticker, namespace = symbol.split('.', 1)
    
    # Known namespace mappings (lowercase -> uppercase)
    namespace_mappings = {
        'moex': 'MOEX',
        'us': 'US',
        'lse': 'LSE',
        'xetr': 'XETR',
        'xfra': 'XFRA',
        'xstu': 'XSTU',
        'xams': 'XAMS',
        'xtae': 'XTAE',
        'pif': 'PIF',
        'fx': 'FX',
        'cc': 'CC',
        'indx': 'INDX',
        'comm': 'COMM',
        're': 'RE',
        'cbr': 'CBR',
        'pf': 'PF'
    }
    
    # Convert namespace to uppercase if it's in our mappings
    normalized_namespace = namespace_mappings.get(namespace.lower(), namespace.upper())
    
    return f"{ticker}.{normalized_namespace}"
```

### 2. Интеграция в команду `/compare`
Добавлена нормализация символов после очистки:
```python
# Clean up symbols (remove empty strings and whitespace)
symbols = [symbol for symbol in symbols if symbol.strip()]

# Normalize namespace case (convert lowercase namespaces to uppercase)
symbols = [self._normalize_symbol_namespace(symbol) for symbol in symbols]
```

### 3. Интеграция в функцию `clean_symbol`
Обновлена функция `clean_symbol` для автоматической нормализации:
```python
def clean_symbol(self, symbol: str) -> str:
    """Очищает символ от случайных символов и нормализует его"""
    if not symbol:
        return symbol
        
    # Удаляем обратные слеши и другие проблемные символы
    cleaned = symbol.replace('\\', '').replace('/', '').replace('"', '').replace("'", '')
    
    # Удаляем лишние пробелы
    cleaned = cleaned.strip()
    
    # Удаляем множественные пробелы
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Нормализуем namespace (конвертируем lowercase в uppercase)
    cleaned = self._normalize_symbol_namespace(cleaned)
    
    return cleaned
```

## Тестирование
Протестированы следующие случаи:
- `sber.moex` -> `sber.MOEX` ✅
- `lqdt.moex` -> `lqdt.MOEX` ✅
- `AAPL.us` -> `AAPL.US` ✅
- `spy.US` -> `spy.US` (без изменений) ✅

## Затронутые команды
Исправление применяется ко всем командам, использующим символы:
- `/compare` - сравнение активов
- `/info` - информация об активе
- `/portfolio` - создание портфеля

## Результат
Теперь пользователи могут вводить символы с любым регистром namespace, и они будут автоматически нормализованы в правильный формат для okama библиотеки.

Команда `/compare sber.moex lqdt.moex` теперь работает корректно.
