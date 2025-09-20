# Исправление поддержки китайских бирж

## 🐛 Проблема

При попытке анализа актива `002594.SZSE` возникала ошибка:
```
❌ Ошибка при получении информации об активе: SZSE is not in allowed assets namespaces: 'US', 'LSE', 'XETR', 'XFRA', 'XSTU', 'XAMS', 'MOEX', 'XTAE', 'PIF', 'FX', 'CC', 'INDX', 'COMM', 'RE', 'CBR', 'PF'
```

## 🔍 Анализ проблемы

Проблема была в двух местах:

1. **Список разрешенных бирж в `bot.py`**: Китайские биржи (SSE, SZSE, HKEX, BSE) не были включены в список `allowed_exchanges` в функции `_select_best_search_result`

2. **Паттерны распознавания в `TushareService`**: Функция `is_tushare_symbol` не распознавала символы с суффиксами `.SZSE`, `.SSE`, `.HKEX`, `.BSE`, только с `.SZ`, `.SH`, `.HK`, `.BJ`

## ✅ Исправления

### 1. Обновлен список разрешенных бирж в `bot.py`

**Файл:** `bot.py`, строка 980

**До:**
```python
allowed_exchanges = ['US', 'LSE', 'XETR', 'XFRA', 'XSTU', 'XAMS', 'MOEX', 'XTAE', 'PIF', 'FX', 'CC', 'INDX', 'COMM', 'RE', 'CBR', 'PF', 'INFL', 'RATE', 'RATIO']
```

**После:**
```python
allowed_exchanges = ['US', 'LSE', 'XETR', 'XFRA', 'XSTU', 'XAMS', 'MOEX', 'XTAE', 'PIF', 'FX', 'CC', 'INDX', 'COMM', 'RE', 'CBR', 'PF', 'INFL', 'RATE', 'RATIO', 'SSE', 'SZSE', 'HKEX', 'BSE']
```

### 2. Обновлен список приоритетных бирж

**Файл:** `bot.py`, строка 983

**До:**
```python
priority_exchanges = ['US', 'MOEX', 'LSE', 'XETR', 'XFRA', 'XAMS']
```

**После:**
```python
priority_exchanges = ['US', 'MOEX', 'LSE', 'XETR', 'XFRA', 'XAMS', 'SSE', 'SZSE', 'HKEX']
```

### 3. Обновлены паттерны распознавания в `TushareService`

**Файл:** `services/tushare_service.py`, строки 34-39

**До:**
```python
self.symbol_patterns = {
    'SSE': r'^[0-9]{6}\.SH$',      # 600000.SH, 000001.SH
    'SZSE': r'^[0-9]{6}\.SZ$',     # 000001.SZ, 399005.SZ
    'BSE': r'^[0-9]{6}\.BJ$',      # 900001.BJ, 800001.BJ
    'HKEX': r'^[0-9]{5}\.HK$'      # 00001.HK, 00700.HK
}
```

**После:**
```python
self.symbol_patterns = {
    'SSE': r'^[0-9]{6}\.(SH|SSE)$',      # 600000.SH, 000001.SH, 600000.SSE
    'SZSE': r'^[0-9]{6}\.(SZ|SZSE)$',    # 000001.SZ, 399005.SZ, 002594.SZSE
    'BSE': r'^[0-9]{6}\.(BJ|BSE)$',      # 900001.BJ, 800001.BJ, 900001.BSE
    'HKEX': r'^[0-9]{5}\.(HK|HKEX)$'     # 00001.HK, 00700.HK, 00001.HKEX
}
```

### 4. Обновлен маппинг бирж

**Файл:** `services/tushare_service.py`, строки 26-31

**До:**
```python
self.exchange_mappings = {
    'SSE': '.SH',      # Shanghai Stock Exchange
    'SZSE': '.SZ',     # Shenzhen Stock Exchange  
    'BSE': '.BJ',      # Beijing Stock Exchange
    'HKEX': '.HK'      # Hong Kong Stock Exchange
}
```

**После:**
```python
self.exchange_mappings = {
    'SSE': ['.SH', '.SSE'],      # Shanghai Stock Exchange
    'SZSE': ['.SZ', '.SZSE'],    # Shenzhen Stock Exchange  
    'BSE': ['.BJ', '.BSE'],      # Beijing Stock Exchange
    'HKEX': ['.HK', '.HKEX']     # Hong Kong Stock Exchange
}
```

### 5. Обновлена функция `get_exchange_from_symbol`

**Файл:** `services/tushare_service.py`, строки 49-55

**До:**
```python
def get_exchange_from_symbol(self, symbol: str) -> Optional[str]:
    """Get exchange code from symbol"""
    for exchange, suffix in self.exchange_mappings.items():
        if symbol.endswith(suffix):
            return exchange
    return None
```

**После:**
```python
def get_exchange_from_symbol(self, symbol: str) -> Optional[str]:
    """Get exchange code from symbol"""
    for exchange, suffixes in self.exchange_mappings.items():
        for suffix in suffixes:
            if symbol.endswith(suffix):
                return exchange
    return None
```

### 6. Обновлена функция `_get_index_info`

**Файл:** `services/tushare_service.py`, строки 267-268

**До:**
```python
exchange_suffix = self.exchange_mappings.get(exchange, f'.{exchange}')
ts_code = f"{symbol_code}{exchange_suffix}"
```

**После:**
```python
exchange_suffixes = self.exchange_mappings.get(exchange, [f'.{exchange}'])
exchange_suffix = exchange_suffixes[0]  # Use first suffix for Tushare API
ts_code = f"{symbol_code}{exchange_suffix}"
```

## 🧪 Тестирование

Создан тест `tests/test_chinese_symbol_fix.py` для проверки всех изменений:

### Результаты тестирования:

✅ **TushareService symbol recognition:**
- `600000.SH` → is_tushare=True, exchange=SSE
- `000001.SZ` → is_tushare=True, exchange=SZSE  
- `900001.BJ` → is_tushare=True, exchange=BSE
- `00001.HK` → is_tushare=True, exchange=HKEX
- `600000.SSE` → is_tushare=True, exchange=SSE
- `002594.SZSE` → is_tushare=True, exchange=SZSE ✅
- `900001.BSE` → is_tushare=True, exchange=BSE
- `00001.HKEX` → is_tushare=True, exchange=HKEX

✅ **Bot data source determination:**
- `600000.SH` → tushare
- `000001.SZ` → tushare
- `002594.SZSE` → tushare ✅
- `600000.SSE` → tushare
- `00001.HK` → tushare
- `00001.HKEX` → tushare
- `AAPL.US` → okama
- `SBER.MOEX` → okama
- `VOD.LSE` → okama

✅ **Allowed exchanges:**
- `002594.SZSE` correctly determined as tushare ✅

## 📊 Поддерживаемые форматы символов

Теперь бот поддерживает следующие форматы китайских символов:

### Шанхайская биржа (SSE):
- `600000.SH` (оригинальный формат)
- `600000.SSE` (новый формат)

### Шэньчжэньская биржа (SZSE):
- `000001.SZ` (оригинальный формат)
- `002594.SZSE` (новый формат) ✅

### Пекинская биржа (BSE):
- `900001.BJ` (оригинальный формат)
- `900001.BSE` (новый формат)

### Гонконгская биржа (HKEX):
- `00001.HK` (оригинальный формат)
- `00001.HKEX` (новый формат)

## 🎯 Результат

Проблема с символом `002594.SZSE` полностью решена:

1. ✅ Символ теперь распознается как китайский актив
2. ✅ Автоматически направляется на обработку через Tushare API
3. ✅ Включен в список разрешенных бирж
4. ✅ Поддерживает оба формата суффиксов (.SZ и .SZSE)

## 📝 Дополнительные улучшения

- Добавлена поддержка всех форматов суффиксов для китайских бирж
- Улучшена совместимость с различными источниками данных
- Создан комплексный тест для проверки функциональности
- Обновлена документация в коде

---

**Дата исправления:** 20 сентября 2025  
**Статус:** ✅ Завершено  
**Тестирование:** ✅ Пройдено
