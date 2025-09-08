# Ephemeral Messages Implementation Report

**Date:** September 8, 2025  
**Feature:** Реализация исчезающих сообщений для системных уведомлений  
**Status:** ✅ Implemented and Tested

## Описание задачи

**Цель:** Добавить функцию исчезающих сообщений для всех системных вспомогательных сообщений пользователю (например, "создаю отчет", "загружаю график" и т.п.), чтобы они не оставались в ленте и исчезали автоматически. В ленте должны сохраняться только данные, несущие смысл.

## Реализованные изменения

### 1. Новая функция `_send_ephemeral_message`

**Файл:** `bot.py` (строки 3522-3564)

**Функциональность:**
- Отправляет сообщение пользователю
- Автоматически удаляет сообщение через указанное время (по умолчанию 5 секунд)
- Поддерживает Markdown форматирование
- Имеет fallback на обычные сообщения при ошибках
- Работает как с callback_query, так и с обычными сообщениями

**Параметры:**
- `update`: Объект Update от Telegram
- `context`: Контекст бота
- `text`: Текст сообщения
- `parse_mode`: Режим парсинга (Markdown/HTML)
- `delete_after`: Время до удаления в секундах (по умолчанию 5)

**Код функции:**
```python
async def _send_ephemeral_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, parse_mode: str = None, delete_after: int = 5):
    """Отправить исчезающее сообщение, которое удаляется через указанное время"""
    try:
        # Проверяем, что update и context не None
        if update is None or context is None:
            self.logger.error("Cannot send ephemeral message: update or context is None")
            return
        
        # Clean Markdown if parse_mode is Markdown
        if parse_mode == 'Markdown':
            text = self._safe_markdown(text)
        
        chat_id = None
        if hasattr(update, 'callback_query') and update.callback_query is not None:
            chat_id = update.callback_query.message.chat_id
        elif hasattr(update, 'message') and update.message is not None:
            chat_id = update.message.chat_id
        else:
            self.logger.error("Cannot send ephemeral message: no chat_id available")
            return
        
        # Отправляем сообщение
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode
        )
        
        # Планируем удаление сообщения через указанное время
        async def delete_message():
            try:
                await asyncio.sleep(delete_after)
                await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            except Exception as delete_error:
                self.logger.warning(f"Could not delete ephemeral message: {delete_error}")
        
        # Запускаем удаление в фоне
        asyncio.create_task(delete_message())
        
    except Exception as e:
        self.logger.error(f"Error sending ephemeral message: {e}")
        # Fallback: отправляем обычное сообщение
        await self._send_callback_message(update, context, text, parse_mode)
```

### 2. Обновленные системные сообщения

**Все следующие типы сообщений теперь используют исчезающие сообщения:**

#### 2.1 Создание портфеля
- **Старое:** `await self._send_message_safe(update, f"Создаю портфель: {', '.join(symbols)}...")`
- **Новое:** `await self._send_ephemeral_message(update, context, f"Создаю портфель: {', '.join(symbols)}...", delete_after=3)`

#### 2.2 Создание графиков
- **Risk/Return график:** `await self._send_ephemeral_message(update, context, "📊 Создаю график Risk / Return (CAGR)…", delete_after=3)`
- **Drawdowns график:** `await self._send_ephemeral_message(update, context, "📉 Создаю график drawdowns...", delete_after=3)`
- **Дивидендная доходность:** `await self._send_ephemeral_message(update, context, "💰 Создаю график дивидендной доходности...", delete_after=3)`
- **Корреляционная матрица:** `await self._send_ephemeral_message(update, context, "🔗 Создаю корреляционную матрицу...", delete_after=3)`

#### 2.3 Графики по периодам
- **1 год:** `await self._send_ephemeral_message(update, context, "📈 Создаю график за 1 год...", delete_after=3)`
- **5 лет:** `await self._send_ephemeral_message(update, context, "📅 Создаю график за 5 лет...", delete_after=3)`
- **Весь период:** `await self._send_ephemeral_message(update, context, "📊 Создаю график за весь период...", delete_after=3)`

#### 2.4 Анализ данных
- **Gemini AI:** `await self._send_ephemeral_message(update, context, "🤖 Анализирую данные с помощью Gemini AI...", parse_mode='Markdown', delete_after=3)`
- **YandexGPT:** `await self._send_ephemeral_message(update, context, "🤖 Анализирую данные с помощью YandexGPT...", parse_mode='Markdown', delete_after=3)`
- **Детальная статистика:** `await self._send_ephemeral_message(update, context, "📊 Подготавливаю детальную статистику...", parse_mode='Markdown', delete_after=3)`

#### 2.5 Анализ рисков и прогнозы
- **Анализ рисков:** `await self._send_ephemeral_message(update, context, "📊 Анализирую риски портфеля...", delete_after=3)`
- **Monte Carlo:** `await self._send_ephemeral_message(update, context, "🎲 Создаю прогноз Monte Carlo...", delete_after=3)`
- **Процентили:** `await self._send_ephemeral_message(update, context, "📈 Создаю прогноз с процентилями...", delete_after=3)`

#### 2.6 Дополнительные графики
- **Просадки:** `await self._send_ephemeral_message(update, context, "📉 Создаю график просадок...", delete_after=3)`
- **Доходность:** `await self._send_ephemeral_message(update, context, "💰 Создаю график доходности...", delete_after=3)`
- **Накопленная доходность:** `await self._send_ephemeral_message(update, context, "📈 Создаю график накопленной доходности...", delete_after=3)`
- **Rolling CAGR:** `await self._send_ephemeral_message(update, context, "📈 Создаю график Rolling CAGR...", delete_after=3)`
- **Сравнение активов:** `await self._send_ephemeral_message(update, context, "📊 Создаю график сравнения с активами...", delete_after=3)`

#### 2.7 Создание файлов
- **Excel файлы:** `await self._send_ephemeral_message(update, context, f"📊 Создаю Excel файл...", delete_after=3)`

#### 2.8 Получение информации
- **Информация об активе:** `await self._send_ephemeral_message(update, context, f"📊 Получаю информацию об активе {symbol}...", delete_after=3)`

### 3. Тестирование

**Файл:** `tests/test_ephemeral_messages.py`

**Покрытые тесты:**
1. **test_ephemeral_message_sends_and_deletes** - Проверка отправки и удаления сообщения
2. **test_ephemeral_message_with_markdown** - Проверка работы с Markdown форматированием
3. **test_ephemeral_message_fallback_on_error** - Проверка fallback при ошибках
4. **test_ephemeral_message_with_regular_message_update** - Проверка работы с обычными сообщениями
5. **test_ephemeral_message_no_chat_id_error** - Проверка обработки ошибок отсутствия chat_id

**Результат тестирования:**
```
----------------------------------------------------------------------
Ran 5 tests in 4.762s

OK
```

## Преимущества реализации

### 1. Чистота ленты сообщений
- Системные уведомления больше не засоряют историю чата
- Пользователь видит только важную информацию
- Улучшенный пользовательский опыт

### 2. Автоматическое управление
- Сообщения исчезают автоматически через заданное время
- Не требует ручного удаления
- Настраиваемое время удаления для разных типов сообщений

### 3. Надежность
- Fallback на обычные сообщения при ошибках
- Обработка различных типов update (callback_query, message)
- Логирование ошибок для отладки

### 4. Гибкость
- Поддержка Markdown форматирования
- Настраиваемое время удаления
- Совместимость с существующим кодом

## Технические детали

### Использование asyncio
- Функция использует `asyncio.create_task()` для асинхронного удаления
- Не блокирует основной поток выполнения
- Автоматическая обработка исключений при удалении

### Время удаления
- **По умолчанию:** 5 секунд
- **Системные уведомления:** 3 секунды (быстрее исчезают)
- **Настраиваемо:** Можно изменить для каждого сообщения

### Совместимость
- Работает с существующими функциями отправки сообщений
- Не нарушает текущую функциональность
- Легко интегрируется в существующий код

## Заключение

Реализация исчезающих сообщений успешно завершена. Все системные уведомления теперь автоматически исчезают из ленты сообщений, оставляя только важную информацию для пользователя. Функция протестирована и готова к использованию.

**Статус:** ✅ Готово к продакшену
