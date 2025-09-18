# Отчет об универсальной системе управления Reply Keyboard

## 🎯 Цель
Создать универсальную систему управления reply keyboard на основе контекста пользователя, чтобы клавиатура показывалась только для команд `/portfolio` и `/compare`, а навигация сохранялась в контексте.

## 🔍 Анализ проблемы

### Проблемы:
1. **Reply keyboard не скрывалась**: Клавиатура отображалась на всех методах, хотя должна только на portfolio и compare
2. **Отсутствие централизованного управления**: Каждая команда вручную вызывала `_remove_*_reply_keyboard`
3. **Нет отслеживания активной клавиатуры**: Контекст не хранил информацию о том, какая клавиатура активна
4. **Дублирование кода**: Много повторяющегося кода для скрытия клавиатур
5. **Навигация не сохранялась**: При переходе между командами контекст клавиатуры терялся

## ✅ Выполненные изменения

### 1. Добавление поля активной клавиатуры в контекст

**Файл:** `services/context_store.py`
**Строки:** 58-59

```python
# Reply keyboard management
"active_reply_keyboard": None,  # None, "portfolio", "compare"
```

### 2. Создание универсальной системы управления клавиатурой

**Файл:** `bot.py`
**Функция:** `_manage_reply_keyboard()`
**Строки:** 6476-6521

```python
async def _manage_reply_keyboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE, keyboard_type: str = None):
    """
    Универсальное управление reply keyboard на основе контекста
    
    Args:
        update: Telegram update object
        context: Telegram context object
        keyboard_type: Тип клавиатуры для показа ("portfolio", "compare") или None для скрытия
    """
    try:
        user_id = update.effective_user.id
        user_context = self._get_user_context(user_id)
        current_keyboard = user_context.get('active_reply_keyboard')
        
        # Если нужно скрыть клавиатуру
        if keyboard_type is None:
            if current_keyboard is not None:
                self.logger.info(f"Removing active reply keyboard: {current_keyboard}")
                await self._remove_reply_keyboard_silently(update, context)
                self._update_user_context(user_id, active_reply_keyboard=None)
            return
        
        # Если нужно показать клавиатуру
        if current_keyboard != keyboard_type:
            # Скрываем текущую клавиатуру если она есть
            if current_keyboard is not None:
                self.logger.info(f"Switching from {current_keyboard} to {keyboard_type} keyboard")
                await self._remove_reply_keyboard_silently(update, context)
            
            # Показываем новую клавиатуру
            if keyboard_type == "portfolio":
                await self._show_portfolio_reply_keyboard(update, context)
            elif keyboard_type == "compare":
                await self._show_compare_reply_keyboard(update, context)
            else:
                self.logger.warning(f"Unknown keyboard type: {keyboard_type}")
                return
            
            # Обновляем контекст
            self._update_user_context(user_id, active_reply_keyboard=keyboard_type)
            self.logger.info(f"Active reply keyboard set to: {keyboard_type}")
        else:
            self.logger.info(f"Reply keyboard {keyboard_type} is already active")
            
    except Exception as e:
        self.logger.error(f"Error managing reply keyboard: {e}")
```

### 3. Создание вспомогательной функции для скрытия клавиатуры

**Файл:** `bot.py`
**Функция:** `_ensure_no_reply_keyboard()`
**Строки:** 6523-6525

```python
async def _ensure_no_reply_keyboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Убедиться что reply keyboard скрыта (для команд которые не должны показывать клавиатуру)"""
    await self._manage_reply_keyboard(update, context, keyboard_type=None)
```

### 4. Обновление всех команд для использования новой системы

#### Команды без клавиатуры (используют `_ensure_no_reply_keyboard`):
- `/start` - строка 2150
- `/help` - строка 2181  
- `/info` - строка 2571
- `/namespace` - строка 3530
- `/search` - строка 3665
- `/my_portfolios` - строка 4449

#### Команды с клавиатурой:
- `/compare` - строка 3786 (скрывает клавиатуру при входе, показывает при успешном сравнении)
- `/portfolio` - строка 4553 (скрывает клавиатуру при входе, показывает при создании портфеля)

### 5. Обновление функций отправки сообщений

**Функция:** `_send_portfolio_message_with_reply_keyboard()`
**Строки:** 6358-6370

```python
async def _send_portfolio_message_with_reply_keyboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, parse_mode: str = None):
    """Отправить сообщение портфеля с reply keyboard"""
    try:
        # Ensure portfolio keyboard is shown
        await self._manage_reply_keyboard(update, context, "portfolio")
        
        # Send message
        await self._send_message_safe(update, text, parse_mode=parse_mode)
        
    except Exception as e:
        self.logger.error(f"Error in _send_portfolio_message_with_reply_keyboard: {e}")
        # Fallback: send message without keyboard
        await self._send_message_safe(update, text)
```

**Функция:** `_send_portfolio_ai_analysis_with_keyboard()`
**Строки:** 6372-6427

Обновлена для использования новой системы управления клавиатурой.

### 6. Обновление всех мест создания portfolio reply keyboard

Заменены все прямые вызовы `self._create_portfolio_reply_keyboard()` на использование `_manage_reply_keyboard(update, context, "portfolio")`:

- Функции создания графиков портфеля
- Функции отправки Excel файлов
- Функции отправки сообщений с информацией о портфеле

### 7. Обновление функций удаления клавиатуры

**Функции:** `_remove_portfolio_reply_keyboard()` и `_remove_compare_reply_keyboard()`
**Строки:** 9981-9993

```python
async def _remove_portfolio_reply_keyboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove portfolio Reply Keyboard if it exists - DEPRECATED: Use _manage_reply_keyboard instead"""
    try:
        await self._manage_reply_keyboard(update, context, keyboard_type=None)
    except Exception as e:
        self.logger.warning(f"Could not remove portfolio reply keyboard: {e}")
```

## 🚀 Преимущества новой системы

### 1. **Централизованное управление**
- Одна функция `_manage_reply_keyboard()` управляет всеми клавиатурами
- Автоматическое переключение между типами клавиатур
- Отслеживание активной клавиатуры в контексте пользователя

### 2. **Контекстная навигация**
- Состояние клавиатуры сохраняется в контексте пользователя
- Автоматическое скрытие при переходе к командам без клавиатуры
- Показ соответствующей клавиатуры при работе с portfolio/compare

### 3. **Универсальность**
- Легко добавить новые типы клавиатур
- Единый интерфейс для всех команд
- Автоматическая обработка конфликтов между клавиатурами

### 4. **Оптимизация кода**
- Устранение дублирования кода
- Упрощение логики команд
- Более читаемый и поддерживаемый код

### 5. **Надежность**
- Обработка ошибок на уровне системы управления
- Fallback механизмы при сбоях
- Логирование всех операций с клавиатурами

## 📋 Логика работы

### При вызове команды:
1. **Команды без клавиатуры**: Вызывают `_ensure_no_reply_keyboard()` → скрывают любую активную клавиатуру
2. **Команды с клавиатурой**: Вызывают `_manage_reply_keyboard(update, context, "portfolio"/"compare")` → показывают нужную клавиатуру

### При переключении между командами:
1. Система проверяет текущую активную клавиатуру в контексте
2. Если нужно показать другую клавиатуру → скрывает текущую и показывает новую
3. Если клавиатура уже активна → ничего не делает
4. Обновляет контекст пользователя с новым состоянием

## 🔧 Технические детали

### Состояния клавиатуры:
- `None` - клавиатура скрыта
- `"portfolio"` - активна клавиатура портфеля
- `"compare"` - активна клавиатура сравнения

### Автоматическое переключение:
- При переходе от portfolio к compare → автоматически переключается
- При переходе к команде без клавиатуры → автоматически скрывается
- При повторном вызове той же команды → ничего не меняется

## ✅ Результат

Теперь reply keyboard:
- ✅ Показывается только для команд `/portfolio` и `/compare`
- ✅ Автоматически скрывается при переходе к другим командам
- ✅ Сохраняет навигацию в контексте пользователя
- ✅ Использует универсальную систему управления
- ✅ Оптимизирована и не содержит дублирования кода
- ✅ Обеспечивает надежную работу без визуальных артефактов

Система полностью готова к использованию и легко расширяется для добавления новых типов клавиатур в будущем.
