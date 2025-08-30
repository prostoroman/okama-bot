# Отчет об исправлениях кнопки "Риск метрики"

## Дата исправления
2025-01-27

## Описание проблемы

При нажатии на кнопку "📊 Риск метрики" возникала ошибка:
```
❌ Неизвестная кнопка
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

### 3. Возможные причины ошибки
- Проблема с сохранением контекста пользователя
- Ошибка в методе `_create_risk_metrics_report`
- Проблема с импортом библиотеки Okama
- Ошибка в методе `portfolio.describe()`

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

### Детальное логирование ошибок
- Полный traceback для отладки
- Контекст возникновения ошибки
- Информация о состоянии данных

## Инструкции по отладке

### 1. Проверка логов
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
```

### 2. Проверка контекста пользователя
Убедитесь, что в контексте присутствуют:
- `current_symbols` - список символов портфеля
- `current_currency` - базовая валюта
- `portfolio_weights` - веса активов

### 3. Проверка создания портфеля
Логи должны показать:
```
Creating risk metrics for portfolio: ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX'], currency: RUB, weights: [0.4, 0.3, 0.3]
```

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

## Следующие шаги

1. **Перезапустить бота** с обновленным кодом
2. **Выполнить команду** `/portfolio SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3`
3. **Нажать кнопку** "📊 Риск метрики"
4. **Проверить логи** на наличие детальной информации
5. **Определить точную причину** ошибки по логам

## Заключение

Добавлено расширенное логирование для диагностики проблемы с кнопкой "Риск метрики". Теперь при возникновении ошибки в логах будет доступна полная информация о:

- Данных, пришедших в callback
- Состоянии контекста пользователя
- Процессе создания портфеля
- Детальном traceback ошибки

Это позволит точно определить причину проблемы и исправить её в следующей итерации. 🚀
