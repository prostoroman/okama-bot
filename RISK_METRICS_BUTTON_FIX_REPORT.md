# Отчет об исправлениях кнопки "Риск метрики" - Обновление

## Дата исправления
2025-01-27

## Описание проблемы

При нажатии на кнопку "📊 Риск метрики" возникала ошибка:
```
❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.
```

## Анализ проблемы

### 1. Проверка обработчика button_callback
- ✅ Обработчик `risk_metrics_` уже добавлен в `button_callback`
- ✅ Логика парсинга callback_data корректна
- ✅ Вызов метода `_handle_risk_metrics_button` присутствует

### 2. Проверка метода _handle_risk_metrics_button
- ✅ Метод существует и корректно определен
- ✅ Параметры метода соответствуют вызову
- ✅ Обработка ошибок присутствует

### 3. Корневая причина ошибки
**Проблема**: В контексте пользователя не находятся данные о портфеле (`current_symbols` не найден)

**Анализ**:
- В команде `/portfolio` данные сохраняются в контекст
- Но в `_handle_risk_metrics_button` мы ищем только `current_symbols`
- В других методах (drawdowns, dividends, correlation) используется тот же ключ
- Возможно, данные сохраняются под другим ключом или не сохраняются вообще

## Внесенные исправления

### 1. Улучшенное логирование в button_callback
**Файл**: `bot.py`  
**Строки**: 1830-1832

**Добавлено**:
```python
elif callback_data.startswith('risk_metrics_'):
    symbols = callback_data.replace('risk_metrics_', '').split(',')
    self.logger.info(f"Risk metrics button clicked for symbols: {symbols}")
    self.logger.info(f"Callback data: {callback_data}")
    self.logger.info(f"Extracted symbols: {symbols}")
    await self._handle_risk_metrics_button(update, context, symbols)
```

### 2. Расширенное логирование в _handle_risk_metrics_button
**Файл**: `bot.py`  
**Строки**: 2265-2285

**Добавлено**:
```python
user_context = self._get_user_context(user_id)
self.logger.info(f"User context keys: {list(user_context.keys())}")
self.logger.info(f"User context content: {user_context}")

# ... и далее ...

self.logger.info(f"Creating risk metrics for portfolio: {symbols}, currency: {currency}, weights: {weights}")

# ... и в блоке except ...

import traceback
self.logger.error(f"Traceback: {traceback.format_exc()}")
```

### 3. Улучшенная логика поиска символов в контексте
**Файл**: `bot.py`  
**Строки**: 2275-2285

**Добавлено**:
```python
# Try to get symbols from different possible keys
symbols = None
self.logger.info(f"Available keys in user context: {list(user_context.keys())}")

if 'current_symbols' in user_context:
    symbols = user_context['current_symbols']
    self.logger.info(f"Found symbols in current_symbols: {symbols}")
elif 'last_assets' in user_context:
    symbols = user_context['last_assets']
    self.logger.info(f"Found symbols in last_assets: {symbols}")
else:
    self.logger.warning(f"Neither current_symbols nor last_assets found in user context")
    self.logger.warning(f"Available keys: {list(user_context.keys())}")
    await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
    return
```

### 4. Логирование сохранения контекста в команде portfolio
**Файл**: `bot.py`  
**Строки**: 1580-1595

**Добавлено**:
```python
# Store portfolio data in context
user_id = update.effective_user.id
self.logger.info(f"Storing portfolio data in context for user {user_id}")
self.logger.info(f"Symbols: {symbols}")
self.logger.info(f"Currency: {currency}")
self.logger.info(f"Weights: {weights}")

self._update_user_context(
    user_id, 
    last_assets=symbols,
    last_analysis_type='portfolio',
    last_period='MAX',
    current_symbols=symbols,
    current_currency=currency,
    current_currency_info=currency_info,
    portfolio_weights=weights
)

# Verify context was saved
saved_context = self._get_user_context(user_id)
self.logger.info(f"Saved context keys: {list(saved_context.keys())}")
self.logger.info(f"Saved current_symbols: {saved_context.get('current_symbols')}")
self.logger.info(f"Saved last_assets: {saved_context.get('last_assets')}")
self.logger.info(f"Saved portfolio_weights: {saved_context.get('portfolio_weights')}")
```

## Диагностические возможности

### Логирование callback_data
- Полный callback_data для проверки формата
- Извлеченные символы для проверки парсинга
- Количество символов для валидации

### Логирование контекста пользователя
- Все ключи в контексте пользователя
- Полное содержимое контекста
- Проверка наличия необходимых данных

### Логирование создания портфеля
- Символы, валюта и веса
- Проверка корректности данных
- Отслеживание процесса создания

### Логирование сохранения контекста
- Подтверждение сохранения данных
- Проверка сохраненных ключей
- Валидация сохраненных значений

### Детальное логирование ошибок
- Полный traceback для отладки
- Контекст возникновения ошибки
- Информация о состоянии данных

## Инструкции по отладке

### 1. Проверка логов при создании портфеля
После выполнения команды `/portfolio` в логах должно появиться:
```
Storing portfolio data in context for user {user_id}
Symbols: ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX']
Currency: RUB
Weights: [0.4, 0.3, 0.3]
Saved context keys: ['last_assets', 'last_analysis_type', 'last_period', 'current_symbols', 'current_currency', 'current_currency_info', 'portfolio_weights']
Saved current_symbols: ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX']
Saved last_assets: ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX']
Saved portfolio_weights: [0.4, 0.3, 0.3]
```

### 2. Проверка логов при нажатии кнопки
После нажатия на кнопку "Риск метрики" в логах должно появиться:
```
Button callback received: risk_metrics_SBER.MOEX,GAZP.MOEX,LKOH.MOEX
Processing callback data: risk_metrics_SBER.MOEX,GAZP.MOEX,LKOH.MOEX
Risk metrics button clicked for symbols: ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX']
Callback data: risk_metrics_SBER.MOEX,GAZP.MOEX,LKOH.MOEX
Extracted symbols: ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX']
Handling risk metrics button for user {user_id}
User context keys: ['last_assets', 'last_analysis_type', 'last_period', 'current_symbols', 'current_currency', 'current_currency_info', 'portfolio_weights']
User context content: {...}
Available keys in user context: ['last_assets', 'last_analysis_type', 'last_period', 'current_symbols', 'current_currency', 'current_currency_info', 'portfolio_weights']
Found symbols in current_symbols: ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX']
Creating risk metrics for portfolio: ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX'], currency: RUB, weights: [0.4, 0.3, 0.3]
```

### 3. Проверка контекста пользователя
Убедитесь, что в контексте присутствуют:
- `current_symbols` - список символов портфеля
- `last_assets` - альтернативный ключ для символов
- `current_currency` - базовая валюта
- `portfolio_weights` - веса активов

## Возможные решения

### Если проблема в контексте пользователя:
1. Проверить, что команда `/portfolio` выполняется успешно
2. Убедиться, что контекст сохраняется корректно
3. Проверить, что пользователь не очищает контекст

### Если проблема в создании портфеля:
1. Проверить доступность библиотеки Okama
2. Убедиться в корректности символов
3. Проверить доступность данных для указанных активов

### Если проблема в методе describe():
1. Проверить версию библиотеки Okama
2. Убедиться в корректности объекта Portfolio
3. Проверить доступность методов risk_annual, semideviation_annual и др.

## Тестирование исправлений

### 1. Компиляция
```bash
python3 -m py_compile bot.py
```
✅ Файл компилируется без ошибок

### 2. Логика парсинга
Создан и выполнен тестовый скрипт, который подтвердил:
- ✅ Корректный парсинг callback_data
- ✅ Правильное извлечение символов
- ✅ Валидацию весов портфеля

### 3. Интеграция
- ✅ Обработчик добавлен в button_callback
- ✅ Метод _handle_risk_metrics_button существует
- ✅ Логирование добавлено во все ключевые точки
- ✅ Улучшена логика поиска символов в контексте

### 4. Логирование контекста
- ✅ Добавлено логирование сохранения контекста
- ✅ Добавлено логирование доступных ключей
- ✅ Добавлена проверка сохраненных данных

## Следующие шаги

1. **Перезапустить бота** с обновленным кодом
2. **Выполнить команду** `/portfolio SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3`
3. **Проверить логи** на наличие информации о сохранении контекста
4. **Нажать кнопку** "📊 Риск метрики"
5. **Проверить логи** на наличие детальной информации о поиске символов
6. **Определить точную причину** ошибки по логам

## Заключение

Добавлено расширенное логирование и улучшена логика поиска символов в контексте пользователя для диагностики проблемы с кнопкой "Риск метрики". 

**Ключевые улучшения**:
- Поиск символов в `current_symbols` и `last_assets`
- Логирование сохранения контекста в команде portfolio
- Проверка сохраненных данных после обновления контекста
- Детальное логирование доступных ключей

Теперь при возникновении ошибки в логах будет доступна полная информация о:
- Данных, пришедших в callback
- Состоянии контекста пользователя
- Процессе сохранения контекста
- Процессе поиска символов
- Детальном traceback ошибки

Это позволит точно определить причину проблемы и исправить её в следующей итерации. 🚀
