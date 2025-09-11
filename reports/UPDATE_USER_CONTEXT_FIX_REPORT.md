# Отчет об исправлении ошибки _update_user_context

## Описание проблемы

**Ошибка:** `ShansAi._update_user_context() takes 2 positional arguments but 3 were given`

**Контекст:** Ошибка возникала при нажатии на кнопки "Сравнить с" и "Добавить в портфель" в команде `/info`.

## Анализ проблемы

### Причина ошибки

Метод `_update_user_context` определен с сигнатурой:
```python
def _update_user_context(self, user_id: int, **kwargs):
```

Однако в двух местах кода он вызывался с неправильным синтаксисом:
```python
# ❌ Неправильно - передача словаря как позиционного аргумента
self._update_user_context(user_id, {
    'waiting_for_compare': True,
    'compare_base_symbol': symbol
})
```

### Найденные проблемные места

1. **Строка 7394** - `_handle_info_compare_button()`:
   ```python
   self._update_user_context(user_id, {
       'waiting_for_compare': True,
       'compare_base_symbol': symbol
   })
   ```

2. **Строка 7421** - `_handle_info_portfolio_button()`:
   ```python
   self._update_user_context(user_id, {
       'waiting_for_portfolio': True,
       'portfolio_base_symbol': symbol
   })
   ```

## Решение

### Исправления

Заменил вызовы с передачей словаря на правильный синтаксис с ключевыми аргументами:

**1. Исправление в `_handle_info_compare_button()`:**
```python
# ✅ Правильно - использование ключевых аргументов
self._update_user_context(user_id, 
    waiting_for_compare=True,
    compare_base_symbol=symbol
)
```

**2. Исправление в `_handle_info_portfolio_button()`:**
```python
# ✅ Правильно - использование ключевых аргументов
self._update_user_context(user_id, 
    waiting_for_portfolio=True,
    portfolio_base_symbol=symbol
)
```

## Тестирование

Создан и выполнен тест для проверки исправления:

```python
def test_update_user_context_fix():
    bot = ShansAi()
    user_id = 12345
    
    # Тест исправленных вызовов
    bot._update_user_context(user_id, 
        waiting_for_compare=True,
        compare_base_symbol='AAPL.US'
    )
    
    bot._update_user_context(user_id, 
        waiting_for_portfolio=True,
        portfolio_base_symbol='AAPL.US'
    )
    
    # Проверка обновления контекста
    context = bot._get_user_context(user_id)
    assert context.get('waiting_for_compare') == True
    assert context.get('compare_base_symbol') == 'AAPL.US'
    assert context.get('waiting_for_portfolio') == True
    assert context.get('portfolio_base_symbol') == 'AAPL.US'
```

**Результат тестирования:** ✅ Все тесты прошли успешно

## Результат

- ✅ Ошибка `takes 2 positional arguments but 3 were given` исправлена
- ✅ Кнопки "Сравнить с" и "Добавить в портфель" теперь работают корректно
- ✅ Контекст пользователя обновляется правильно
- ✅ Код соответствует сигнатуре метода `_update_user_context`

## Файлы изменены

- `bot.py` - исправлены вызовы `_update_user_context` в строках 7394-7397 и 7421-7424

## Дата исправления

11 сентября 2025 г.
