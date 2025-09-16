# Portfolio AI Analysis Priority Fix Report

## Проблема

При нажатии кнопки "▫️ AI-анализ" в reply keyboard для портфеля вызывался анализ YandexGPT вместо анализа Gemini.

## Анализ проблемы

### Исходная проблема
В функции `_handle_reply_keyboard_button` (строки 9717-9724) была логика приоритизации контекстов для кнопок, которые существуют как в портфеле, так и в сравнении:

```python
if is_compare_button and is_portfolio_button:
    # Button exists in both contexts - determine by data availability
    if last_assets and len(last_assets) > 0:
        # User has compare data - use compare context
        await self._handle_compare_reply_keyboard_button(update, context, text)
    elif saved_portfolios and len(saved_portfolios) > 0:
        # User has portfolio data - use portfolio context
        await self._handle_portfolio_reply_keyboard_button(update, context, text)
```

### Причина проблемы
Кнопка "▫️ AI-анализ" существует в обоих контекстах:
- В портфеле: использует Gemini сервис через `_handle_portfolio_ai_analysis_button`
- В сравнении: использует YandexGPT сервис через `_handle_yandexgpt_analysis_compare_button`

Когда у пользователя были данные и для сравнения, и для портфеля, система отдавала приоритет контексту сравнения, что приводило к вызову YandexGPT вместо Gemini для анализа портфеля.

## Решение

Изменен порядок приоритизации контекстов - теперь приоритет отдается портфелю над сравнением:

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

## Изменения в коде

### Файл: `bot.py`
**Функция:** `_handle_reply_keyboard_button` (строки 9717-9727)

**Изменение:** Поменялся порядок проверки контекстов - теперь сначала проверяется наличие портфелей, затем данных сравнения.

## Результат

Теперь при нажатии кнопки "▫️ AI-анализ" в контексте портфеля:
- ✅ Будет вызываться анализ Gemini (функция `_handle_portfolio_ai_analysis_button`)
- ✅ Будет использоваться правильный AI сервис для анализа портфеля
- ✅ Пользователь получит качественный анализ портфеля от Gemini

## Тестирование

Исправление протестировано на уровне кода:
- ✅ Синтаксическая проверка пройдена
- ✅ Линтер ошибок не обнаружено
- ✅ Логика приоритизации исправлена

## Дополнительная информация

### Контексты AI анализа
1. **Портфель → Gemini**
   - Функция: `_handle_portfolio_ai_analysis_button`
   - Сервис: `self.gemini_service.analyze_portfolio()`
   - Специализированный анализ портфеля

2. **Сравнение → YandexGPT**
   - Функция: `_handle_yandexgpt_analysis_compare_button`
   - Сервис: `self.yandexgpt_service.analyze_data()`
   - Анализ данных сравнения

### Поведение после исправления
- При наличии только портфеля → Gemini анализ
- При наличии только данных сравнения → YandexGPT анализ  
- При наличии и портфеля, и данных сравнения → **Приоритет Gemini** (исправлено)

---

**Дата:** 16 сентября 2025  
**Автор:** AI Assistant  
**Статус:** ✅ Исправлено и готово к тестированию
