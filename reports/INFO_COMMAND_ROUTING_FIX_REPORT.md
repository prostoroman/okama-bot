# Отчет об исправлении маршрутизации команды /info

## Проблема

Пользователь сообщил о неправильной маршрутизации сообщений в команде `/info`:

1. **Пользователь отправляет:** `/info`
2. **Бот отвечает правильно:** "📊 Информация об активе Примеры: BP.LSE, HSBA.LSE, SI.COMM Просто отправьте название инструмента"
3. **Пользователь отправляет:** `HSBA.LSE`
4. **Бот отвечает неправильно:** "❌ Некорректный формат: HSBA.LSE. Используйте формат символ:доля"
5. **Пользователь отправляет:** `BP.LSE`
6. **Бот отвечает неправильно:** "Вы указали только 1 символ, а для сравнения нужно 2 и больше, напишите дополнительный символ для сравнения, например AGG.US, 800001.BJ, SI.COMM"

## Анализ проблемы

Проблема была в функции `handle_message` в файле `bot.py`. Когда пользователь отправлял символ после команды `/info`, система проверяла контекст пользователя и неправильно интерпретировала это как команду сравнения (`/compare`).

### Логика до исправления:

```python
# Check if user is waiting for compare input or has stored compare symbol
if user_context.get('waiting_for_compare', False) or user_context.get('compare_first_symbol') or user_context.get('compare_base_symbol'):
    self.logger.info(f"Processing as compare input: {text}")
    # Process as compare input
    await self._handle_compare_input(update, context, text)
    return
```

Эта проверка срабатывала даже когда пользователь просто хотел использовать команду `/info`, потому что система не знала, что пользователь находится в контексте команды `/info` и ожидает ввода символа.

## ✅ Реализованные исправления

### 1. Добавлен флаг `waiting_for_info` в команду `/info`

**Файл:** `bot.py` - функция `info_command`

```python
async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /info command - показывает ежедневный график с базовой информацией и AI анализом"""
    if not context.args:
        # Get random examples for user
        examples = self.get_random_examples(3)
        examples_text = ", ".join(examples)
        
        # Set flag that user is waiting for info input
        user_id = update.effective_user.id
        self._update_user_context(user_id, waiting_for_info=True)
        
        await self._send_message_safe(update, 
            f"📊 *Информация об активе*\n\n"
            f"*Примеры:* {examples_text}\n\n"
            f"*Просто отправьте название инструмента*")
        return
```

### 2. Обновлена логика маршрутизации в `handle_message`

**Файл:** `bot.py` - функция `handle_message`

```python
# Check if user is waiting for info input
if user_context.get('waiting_for_info', False):
    self.logger.info(f"Processing as info input: {text}")
    # Clear the waiting flag
    self._update_user_context(user_id, waiting_for_info=False)
    # Process as info command with the symbol
    context.args = [text]
    await self.info_command(update, context)
    return
```

### 3. Очистка флага при получении аргументов

**Файл:** `bot.py` - функция `info_command`

```python
symbol = self.clean_symbol(context.args[0]).upper()

# Update user context
user_id = update.effective_user.id
self._update_user_context(user_id, 
                        last_assets=[symbol] + self._get_user_context(user_id).get('last_assets', []),
                        waiting_for_info=False)
```

## 📋 Логика работы после исправления

### Сценарий 1: Команда /info без аргументов
1. **Пользователь вводит:** `/info`
2. **Система:** Устанавливает `waiting_for_info=True`
3. **Результат:** Показывает справку "Просто отправьте название инструмента"

### Сценарий 2: Ввод символа после /info
1. **Пользователь вводит:** `HSBA.LSE`
2. **Система:** Проверяет `waiting_for_info=True`
3. **Система:** Очищает флаг `waiting_for_info=False`
4. **Система:** Обрабатывает как команду `/info HSBA.LSE`
5. **Результат:** Показывает информацию об активе HSBA.LSE

### Сценарий 3: Команда /info с аргументами
1. **Пользователь вводит:** `/info HSBA.LSE`
2. **Система:** Очищает флаг `waiting_for_info=False`
3. **Результат:** Показывает информацию об активе HSBA.LSE

## 🎯 Результат

Теперь команда `/info` работает правильно:

1. ✅ **Команда `/info`** показывает справку и устанавливает флаг ожидания
2. ✅ **Ввод символа** после `/info` обрабатывается как команда `/info`, а не `/compare`
3. ✅ **Маршрутизация** работает корректно для всех сценариев
4. ✅ **Контекст пользователя** правильно отслеживается

## 📝 Тестирование

Создан тест `tests/test_info_routing_fix.py` для проверки:
- Установки флага `waiting_for_info` при вызове `/info` без аргументов
- Обработки ввода как команды `/info` когда `waiting_for_info=True`
- Игнорирования флага когда `waiting_for_info=False`

## 🚀 Развертывание

Исправление готово к развертыванию. Все изменения внесены в файл `bot.py` и не требуют дополнительных зависимостей.

---

**Статус:** ✅ **ИСПРАВЛЕНО** - Команда `/info` теперь работает корректно с правильной маршрутизацией сообщений
