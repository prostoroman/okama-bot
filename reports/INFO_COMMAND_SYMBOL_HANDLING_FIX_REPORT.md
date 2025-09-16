# Отчет об исправлении обработки символов в команде /info

## Проблема

При использовании команды `/info` и последующем вводе символа (например, `RGBITR.INDX`) вместо анализа актива создавался портфель. Это происходило из-за конфликта флагов контекста пользователя.

## Причина

1. Когда пользователь вводил команду `/portfolio` без аргументов, устанавливался флаг `waiting_for_portfolio=True`
2. При последующем использовании команды `/info` флаг `waiting_for_portfolio` не сбрасывался
3. В функции `handle_message` проверка `waiting_for_portfolio` происходила раньше проверки `waiting_for_info`
4. В результате символы обрабатывались как ввод портфеля вместо анализа

## Исправление

### 1. Очистка флагов в команде /info

В функции `info_command` добавлена очистка всех флагов ожидания:

```python
# Set flag that user is waiting for info input and clear portfolio flags
user_id = update.effective_user.id
self._update_user_context(user_id, 
    waiting_for_info=True,
    waiting_for_portfolio=False,
    waiting_for_portfolio_weights=False,
    waiting_for_compare=False
)
```

### 2. Очистка флагов при обработке символа с аргументами

При обработке символа с аргументами в команде `/info`:

```python
# Update user context - clear all waiting flags
user_id = update.effective_user.id
self._update_user_context(user_id, 
    waiting_for_info=False,
    waiting_for_portfolio=False,
    waiting_for_portfolio_weights=False,
    waiting_for_compare=False
)
```

### 3. Очистка флагов в handle_message

При обработке ввода для команды `/info` в функции `handle_message`:

```python
# Clear all waiting flags
self._update_user_context(user_id, 
    waiting_for_info=False,
    waiting_for_portfolio=False,
    waiting_for_portfolio_weights=False,
    waiting_for_compare=False
)
```

## Результат

Теперь команда `/info` корректно обрабатывает символы:
- При вводе `/info` без аргументов устанавливается только флаг `waiting_for_info=True`
- Все остальные флаги ожидания сбрасываются
- При вводе символа после `/info` он обрабатывается как анализ актива, а не как создание портфеля

## Тестирование

Исправление протестировано с символом `RGBITR.INDX`:
- Команда `/info` → запрос на ввод символа
- Ввод `RGBITR.INDX` → анализ актива (а не создание портфеля)

## Файлы изменены

- `bot.py` - функция `info_command` и `handle_message`

## Дата исправления

16 сентября 2025 года

