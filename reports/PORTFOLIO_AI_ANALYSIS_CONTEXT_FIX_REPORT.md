# Portfolio AI Analysis Context Fix Report

## Проблема

При запуске AI анализа портфеля вместо него выполняется AI анализ сравнения. Это происходит когда пользователь создает портфель, а затем выполняет команду сравнения - система неправильно определяет контекст для кнопки "▫️ AI-анализ".

## Анализ проблемы

### Исходная проблема
В функции `_handle_reply_keyboard_button` (строки 9853-9871) была упрощенная логика приоритизации контекстов для кнопок, которые существуют как в портфеле, так и в сравнении:

```python
if is_compare_button and is_portfolio_button:
    # Button exists in both contexts - prioritize portfolio context over compare context
    if saved_portfolios and len(saved_portfolios) > 0:
        # User has portfolio data - use portfolio context (Gemini analysis)
        await self._handle_portfolio_reply_keyboard_button(update, context, text)
    elif last_assets and len(last_assets) > 0:
        # User has compare data - use compare context (YandexGPT analysis)
        await self._handle_compare_reply_keyboard_button(update, context, text)
```

### Причина проблемы
Кнопка "▫️ AI-анализ" существует в обоих контекстах:
- В портфеле: использует Gemini сервис через `_handle_portfolio_ai_analysis_button`
- В сравнении: использует Gemini сервис через `_handle_yandexgpt_analysis_compare_button`

Когда пользователь создает портфель, а затем выполняет команду сравнения:
1. Команда `/portfolio` сохраняет данные в `saved_portfolios` и `last_assets`
2. Команда `/compare` перезаписывает `last_assets` данными сравнения
3. При нажатии "▫️ AI-анализ" система видит что есть `saved_portfolios`, но `last_assets` содержит данные сравнения
4. Система выбирает портфельный контекст, но использует неправильные данные

## Решение

Улучшена логика определения контекста с использованием поля `last_analysis_type` для определения последнего типа анализа:

### Изменения в коде

**Файл:** `bot.py`
**Функция:** `_handle_reply_keyboard_button` (строки 9853-9871)

**Было:**
```python
if is_compare_button and is_portfolio_button:
    # Button exists in both contexts - prioritize portfolio context over compare context
    if saved_portfolios and len(saved_portfolios) > 0:
        # User has portfolio data - use portfolio context (Gemini analysis)
        await self._handle_portfolio_reply_keyboard_button(update, context, text)
    elif last_assets and len(last_assets) > 0:
        # User has compare data - use compare context (YandexGPT analysis)
        await self._handle_compare_reply_keyboard_button(update, context, text)
    else:
        # No data available - show appropriate error message
        await self._send_message_safe(update, f"❌ Нет данных для анализа. Создайте сравнение командой `/compare` или портфель командой `/portfolio`")
```

**Стало:**
```python
if is_compare_button and is_portfolio_button:
    # Button exists in both contexts - determine by last analysis type and data availability
    last_analysis_type = user_context.get('last_analysis_type')
    
    if last_analysis_type == 'portfolio' and saved_portfolios and len(saved_portfolios) > 0:
        # User's last action was portfolio creation - use portfolio context (Gemini analysis)
        await self._handle_portfolio_reply_keyboard_button(update, context, text)
    elif last_analysis_type == 'comparison' and last_assets and len(last_assets) > 0:
        # User's last action was comparison - use compare context (Gemini analysis)
        await self._handle_compare_reply_keyboard_button(update, context, text)
    elif saved_portfolios and len(saved_portfolios) > 0:
        # Fallback: User has portfolio data - use portfolio context (Gemini analysis)
        await self._handle_portfolio_reply_keyboard_button(update, context, text)
    elif last_assets and len(last_assets) > 0:
        # Fallback: User has compare data - use compare context (Gemini analysis)
        await self._handle_compare_reply_keyboard_button(update, context, text)
    else:
        # No data available - show appropriate error message
        await self._send_message_safe(update, f"❌ Нет данных для анализа. Создайте сравнение командой `/compare` или портфель командой `/portfolio`")
```

## Логика определения контекста

### Приоритет 1: По типу последнего анализа
- Если `last_analysis_type == 'portfolio'` и есть `saved_portfolios` → портфельный контекст
- Если `last_analysis_type == 'comparison'` и есть `last_assets` → контекст сравнения

### Приоритет 2: Fallback по наличию данных
- Если есть `saved_portfolios` → портфельный контекст
- Если есть `last_assets` → контекст сравнения

### Приоритет 3: Ошибка
- Если нет данных → показать сообщение об ошибке

## Результат

Теперь при нажатии кнопки "▫️ AI-анализ":

### Сценарий 1: Пользователь создал портфель, затем сравнение
- ✅ `last_analysis_type = 'comparison'`
- ✅ Будет вызван анализ сравнения (Gemini)
- ✅ Используются правильные данные сравнения

### Сценарий 2: Пользователь создал сравнение, затем портфель
- ✅ `last_analysis_type = 'portfolio'`
- ✅ Будет вызван анализ портфеля (Gemini)
- ✅ Используются правильные данные портфеля

### Сценарий 3: Только портфель
- ✅ `last_analysis_type = 'portfolio'`
- ✅ Будет вызван анализ портфеля (Gemini)

### Сценарий 4: Только сравнение
- ✅ `last_analysis_type = 'comparison'`
- ✅ Будет вызван анализ сравнения (Gemini)

## Тестирование

Исправление протестировано на уровне кода:
- ✅ Синтаксическая проверка пройдена
- ✅ Линтер ошибок не обнаружено
- ✅ Логика определения контекста улучшена
- ✅ Добавлена поддержка `last_analysis_type`

## Дополнительная информация

### Поля контекста пользователя
- `last_analysis_type`: 'portfolio' или 'comparison' - тип последнего анализа
- `saved_portfolios`: словарь сохраненных портфелей
- `last_assets`: символы из последней команды

### Сохранение контекста
- Команда `/portfolio` устанавливает `last_analysis_type = 'portfolio'`
- Команда `/compare` устанавливает `last_analysis_type = 'comparison'`

## Дата исправления

19 января 2025 г.

