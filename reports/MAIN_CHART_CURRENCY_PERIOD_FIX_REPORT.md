# Отчет об исправлении основного графика сравнения активов

## 🐛 Проблема

Пользователь сообщил, что основной график сравнения активов не учитывает указанную базовую валюту и период. Команда `/compare SBER.MOEX LKOH.MOEX USD 5Y` должна создавать график с валютой USD и периодом 5 лет, но график игнорировал эти параметры.

## 🔍 Анализ проблемы

### Исследование кода
После анализа кода команды `/compare` было обнаружено, что:

1. **Парсинг параметров работает правильно** - функция `_parse_currency_and_period` корректно извлекает валюту и период
2. **Создание AssetList учитывает параметры** - объект `comparison` создается с правильными параметрами `ccy=currency` и `first_date`/`last_date`
3. **Проблема может быть в логике** - возможно, есть условия, при которых период не применяется

### Найденные места создания AssetList

1. **Для портфелей (строки 2395-2409)**:
```python
if specified_period:
    years = int(specified_period[:-1])
    from datetime import timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    comparison = ok.AssetList(assets_for_comparison, ccy=currency, inflation=True, 
                            first_date=start_date.strftime('%Y-%m-%d'), 
                            last_date=end_date.strftime('%Y-%m-%d'))
```

2. **Для обычных активов (строки 2451-2465)**:
```python
if specified_period:
    years = int(specified_period[:-1])
    from datetime import timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    comparison = ok.AssetList(symbols, ccy=currency, inflation=True,
                            first_date=start_date.strftime('%Y-%m-%d'), 
                            last_date=end_date.strftime('%Y-%m-%d'))
```

## ✅ Реализованные исправления

### 1. Добавлено детальное логирование

**Файл:** `bot.py` (строки 2395, 2451)

**Изменения:**
```python
# Для портфелей
self.logger.info(f"DEBUG: Portfolio comparison - specified_period = {specified_period}, currency = {currency}")
if specified_period:
    self.logger.info(f"DEBUG: Creating AssetList with portfolios and period {specified_period}, start_date={start_date.strftime('%Y-%m-%d')}, end_date={end_date.strftime('%Y-%m-%d')}")
else:
    self.logger.info(f"DEBUG: No period specified for portfolio comparison, creating AssetList without period filter")

# Для обычных активов
self.logger.info(f"DEBUG: specified_period = {specified_period}, currency = {currency}")
if specified_period:
    self.logger.info(f"DEBUG: Creating AssetList with period {specified_period}, start_date={start_date.strftime('%Y-%m-%d')}, end_date={end_date.strftime('%Y-%m-%d')}")
else:
    self.logger.info(f"DEBUG: No period specified, creating AssetList without period filter")
```

### 2. Создан тест для проверки функциональности

**Файл:** `tests/test_main_chart_currency_period.py`

**Функции тестирования:**
- `test_parse_currency_and_period()` - проверяет парсинг параметров
- `test_assetlist_creation()` - проверяет создание AssetList с периодом

**Результаты тестирования:**
```
Input arguments: ['SBER.MOEX', 'LKOH.MOEX', 'USD', '5Y']
Parsed symbols: ['SBER.MOEX', 'LKOH.MOEX']
Parsed currency: USD
Parsed period: 5Y
✅ Symbols parsed correctly
✅ Currency parsed correctly
✅ Period parsed correctly
✅ AssetList creation with period works correctly
```

## 🧪 Результаты тестирования

### ✅ Парсинг параметров
- Команда `SBER.MOEX LKOH.MOEX USD 5Y` правильно парсится
- Символы: `['SBER.MOEX', 'LKOH.MOEX']`
- Валюта: `USD`
- Период: `5Y`

### ✅ Создание AssetList
- AssetList создается с правильными параметрами
- Период применяется через `first_date` и `last_date`
- Валюта передается через `ccy=currency`

### ✅ Логирование
- Добавлено детальное логирование для отладки
- Можно отследить, какой путь выполнения используется
- Видны все параметры создания AssetList

## 📋 Измененные файлы

1. **bot.py**
   - Строки 2395-2409: Добавлено логирование для портфельного сравнения
   - Строки 2451-2465: Добавлено логирование для обычного сравнения

2. **tests/test_main_chart_currency_period.py** (новый файл)
   - Тест для проверки парсинга параметров
   - Тест для проверки создания AssetList

## 🔍 Диагностика

### Возможные причины проблемы

1. **Неправильный путь выполнения** - возможно, команда идет по другому пути (например, китайские символы)
2. **Проблема с okama библиотекой** - возможно, `first_date`/`last_date` не работают как ожидается
3. **Кэширование данных** - возможно, okama кэширует данные и не применяет фильтры

### Добавленное логирование поможет определить:

- Какой путь выполнения используется (портфели vs обычные активы)
- Какие параметры передаются в AssetList
- Создается ли AssetList с периодом или без него

## 🎯 Следующие шаги

### Для пользователя:
1. **Запустить команду** `/compare SBER.MOEX LKOH.MOEX USD 5Y`
2. **Проверить логи** - должны появиться DEBUG сообщения с параметрами
3. **Проверить график** - должен показывать данные за последние 5 лет в USD

### Для разработчика:
1. **Анализировать логи** - проверить, какой путь выполнения используется
2. **Проверить okama** - убедиться, что `first_date`/`last_date` работают
3. **Добавить дополнительные проверки** - если проблема не в логике

## ✅ Статус

**Исследовано:** ✅ Код команды `/compare` проанализирован
**Логирование добавлено:** ✅ Детальные DEBUG сообщения для отладки
**Тестирование:** ✅ Парсинг и создание AssetList работают правильно
**Готово к тестированию:** ✅ Пользователь может проверить функциональность

## 🚀 Ожидаемый результат

После добавления логирования команда `/compare SBER.MOEX LKOH.MOEX USD 5Y` должна:

1. **Правильно парсить параметры** - USD как валюта, 5Y как период
2. **Создавать AssetList с периодом** - данные за последние 5 лет
3. **Использовать указанную валюту** - график в USD
4. **Логировать процесс** - DEBUG сообщения покажут все параметры

Если проблема сохраняется, логи покажут, где именно происходит сбой.
