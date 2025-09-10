# Отчет об исправлении передачи параметров валюты и периода

## 🐛 Проблема

Из логов пользователя видно, что команда `/compare SBER.MOEX LKOH.MOEX USD 5Y` не учитывает указанную валюту USD и период 5Y:

```
DEBUG: specified_period = None, currency = RUB
DEBUG: No period specified, creating AssetList without period filter
```

## 🔍 Анализ проблемы

### Найденная причина

Проблема была в функции `_handle_compare_input` (строки 3634-3640):

```python
# Process the comparison using the same logic as compare_command
# We'll reuse the existing comparison logic by calling compare_command with args
context.args = symbols
await self.compare_command(update, context)
```

**Проблема:** `context.args = symbols` перезаписывает аргументы только символами, теряя валюту и период, которые были уже распарсены в `_handle_compare_input`.

### Логика выполнения

1. **Пользователь вводит:** `/compare SBER.MOEX LKOH.MOEX USD 5Y`
2. **Telegram обрабатывает как:** команду без аргументов + пользовательский ввод
3. **Бот вызывает:** `_handle_compare_input` с текстом `"SBER.MOEX LKOH.MOEX USD 5Y"`
4. **`_handle_compare_input` парсит:** `symbols=['SBER.MOEX', 'LKOH.MOEX']`, `currency='USD'`, `period='5Y'`
5. **НО:** `context.args = symbols` перезаписывает аргументы только символами
6. **`compare_command` вызывается с:** `context.args = ['SBER.MOEX', 'LKOH.MOEX']`
7. **`compare_command` парсит заново:** `symbols=['SBER.MOEX', 'LKOH.MOEX']`, `currency=None`, `period=None`

## ✅ Реализованные исправления

### 1. Исправлена передача параметров в `_handle_compare_input`

**Файл:** `bot.py` (строки 3634-3640)

**Было:**
```python
context.args = symbols
await self.compare_command(update, context)
```

**Стало:**
```python
context.args = symbols

# Store parsed currency and period in context for compare_command to use
context.specified_currency = specified_currency
context.specified_period = specified_period

await self.compare_command(update, context)
```

### 2. Обновлена логика парсинга в `compare_command`

**Файл:** `bot.py` (строки 2081-2097)

**Было:**
```python
# Parse currency and period parameters from command arguments
symbols, specified_currency, specified_period = self._parse_currency_and_period(context.args)
```

**Стало:**
```python
# Parse currency and period parameters from command arguments
# Check if they were already parsed by _handle_compare_input
if hasattr(context, 'specified_currency') and hasattr(context, 'specified_period'):
    symbols = context.args
    specified_currency = context.specified_currency
    specified_period = context.specified_period
    self.logger.info(f"Using pre-parsed parameters from _handle_compare_input: currency={specified_currency}, period={specified_period}")
else:
    symbols, specified_currency, specified_period = self._parse_currency_and_period(context.args)
```

## 🧪 Ожидаемые результаты

### После исправления команда `/compare SBER.MOEX LKOH.MOEX USD 5Y` должна:

1. **Правильно парсить параметры:**
   ```
   Using pre-parsed parameters from _handle_compare_input: currency=USD, period=5Y
   Parsed symbols: ['SBER.MOEX', 'LKOH.MOEX']
   Parsed currency: USD
   Parsed period: 5Y
   ```

2. **Создавать AssetList с периодом:**
   ```
   DEBUG: specified_period = 5Y, currency = USD
   DEBUG: Creating AssetList with period 5Y, start_date=2019-XX-XX, end_date=2024-XX-XX
   Successfully created regular comparison with period 5Y and inflation (US.INFL) using first_date/last_date parameters
   ```

3. **Создавать график с правильными параметрами:**
   - График в валюте USD
   - Данные за последние 5 лет
   - Подпись с указанием валюты и периода

## 📋 Измененные файлы

1. **bot.py**
   - Строки 3634-3640: Добавлена передача `specified_currency` и `specified_period` в контекст
   - Строки 2081-2097: Добавлена проверка предварительно распарсенных параметров

## 🔍 Логика исправления

### Принцип работы:

1. **Если команда вызвана напрямую** (например, `/compare SBER.MOEX LKOH.MOEX USD 5Y`):
   - `compare_command` парсит аргументы напрямую
   - Используется стандартная логика `_parse_currency_and_period`

2. **Если команда вызвана через пользовательский ввод** (например, `/compare` + ввод текста):
   - `_handle_compare_input` парсит текст
   - Сохраняет результат в `context.specified_currency` и `context.specified_period`
   - `compare_command` использует предварительно распарсенные параметры

### Совместимость:

- ✅ **Обратная совместимость:** Прямые команды продолжают работать
- ✅ **Новая функциональность:** Пользовательский ввод теперь правильно обрабатывается
- ✅ **Логирование:** Добавлены DEBUG сообщения для отладки

## ✅ Статус

**Проблема найдена:** ✅ Причина в потере параметров при передаче между функциями
**Исправление реализовано:** ✅ Параметры теперь сохраняются в контексте
**Логирование добавлено:** ✅ DEBUG сообщения для отслеживания процесса
**Готово к тестированию:** ✅ Пользователь может проверить исправление

## 🚀 Следующие шаги

### Для пользователя:
1. **Запустить команду** `/compare SBER.MOEX LKOH.MOEX USD 5Y`
2. **Проверить логи** - должны появиться сообщения о предварительно распарсенных параметрах
3. **Проверить график** - должен показывать данные в USD за 5 лет

### Ожидаемые логи:
```
Using pre-parsed parameters from _handle_compare_input: currency=USD, period=5Y
Parsed symbols: ['SBER.MOEX', 'LKOH.MOEX']
Parsed currency: USD
Parsed period: 5Y
DEBUG: specified_period = 5Y, currency = USD
DEBUG: Creating AssetList with period 5Y, start_date=2019-XX-XX, end_date=2024-XX-XX
```

Исправление должно решить проблему с игнорированием валюты и периода в основном графике сравнения активов.
