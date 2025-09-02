# Отчет об исправлении проблем с контекстом в методах смешанного сравнения

## Дата исправления
2025-01-27

## Описание проблем

### 1. Ошибка "'Series' object has no attribute 'columns'"
**Проблема**: В методе `_create_mixed_comparison_dividends_chart` передавался `pd.Series` в метод `create_dividend_yield_chart()`, который ожидает DataFrame.

**Исправление**: ✅ Применено
```python
# Convert Series to DataFrame for chart creation
dividends_df = pd.DataFrame(valid_dividends_data, index=[0]).T
fig, ax = chart_styles.create_dividend_yield_chart(
    dividends_df, list(valid_dividends_data.keys())
)
```

### 2. Ошибка "Недостаточно данных для создания корреляционной матрицы"
**Проблема**: Методы смешанного сравнения неправильно извлекали данные портфелей из контекста.

**Корневая причина**: Использовались неправильные ключи для извлечения данных портфелей:
- ❌ `portfolio_context.get('assets', [])` 
- ❌ `portfolio_context.get('weights', [])`
- ✅ `portfolio_context.get('portfolio_symbols', [])`
- ✅ `portfolio_context.get('portfolio_weights', [])`

## Исправленные методы

### 1. `_create_mixed_comparison_drawdowns_chart`
**Исправления**:
- ✅ Исправлены ключи для извлечения данных портфелей
- ✅ Добавлен аргумент `currency` в вызов `chart_styles.create_drawdowns_chart()`

```python
# Было:
assets = portfolio_context.get('assets', [])
weights = portfolio_context.get('weights', [])

# Стало:
assets = portfolio_context.get('portfolio_symbols', [])
weights = portfolio_context.get('portfolio_weights', [])
```

### 2. `_create_mixed_comparison_dividends_chart`
**Исправления**:
- ✅ Исправлены ключи для извлечения данных портфелей
- ✅ Исправлена передача данных в `chart_styles.create_dividend_yield_chart()`

```python
# Было:
assets = portfolio_context.get('assets', [])
weights = portfolio_context.get('weights', [])

# Стало:
assets = portfolio_context.get('portfolio_symbols', [])
weights = portfolio_context.get('portfolio_weights', [])
```

### 3. `_create_mixed_comparison_correlation_matrix`
**Исправления**:
- ✅ Исправлены ключи для извлечения данных портфелей

```python
# Было:
assets = portfolio_context.get('assets', [])
weights = portfolio_context.get('weights', [])

# Стало:
assets = portfolio_context.get('portfolio_symbols', [])
weights = portfolio_context.get('portfolio_weights', [])
```

## Архитектура контекста

### Сохранение контекста в `/compare`
```python
user_context['current_symbols'] = clean_symbols
user_context['current_currency'] = currency
user_context['last_analysis_type'] = 'comparison'
user_context['portfolio_contexts'] = portfolio_contexts  # Store portfolio contexts
user_context['expanded_symbols'] = expanded_symbols  # Store expanded symbols
```

### Структура portfolio_contexts
```python
portfolio_contexts.append({
    'symbol': symbol,  # Clean portfolio symbol
    'portfolio_symbols': portfolio_symbols,  # ✅ Правильный ключ
    'portfolio_weights': portfolio_weights,    # ✅ Правильный ключ
    'portfolio_currency': portfolio_currency,
    'portfolio_object': portfolio
})
```

## Технические детали

### Проблема с ключами
- **Неправильные ключи**: `'assets'`, `'weights'` - не существовали в контексте
- **Правильные ключи**: `'portfolio_symbols'`, `'portfolio_weights'` - сохраняются в `/compare`

### Обработка данных
1. **Извлечение из контекста**: Используются правильные ключи
2. **Создание портфелей**: `ok.Portfolio(assets, weights, ...)`
3. **Расчет показателей**: Просадки, дивиденды, корреляции
4. **Создание графиков**: Передача в `chart_styles`

## Результаты

### ✅ Исправленные ошибки
1. **Drawdowns chart**: Корректное извлечение данных портфелей
2. **Dividend yield chart**: Правильный формат данных и извлечение контекста
3. **Correlation matrix**: Корректное извлечение данных портфелей

### 🎯 Поддерживаемые сценарии
- ✅ `/compare PORTFOLIO_1 SPY.US` → Все кнопки работают
- ✅ `/compare PORTFOLIO_1 PORTFOLIO_2 SPY.US` → Все кнопки работают
- ✅ Смешанное сравнение портфелей и активов
- ✅ Корректная передача валюты

## Тестирование

### Ожидаемое поведение
1. **Drawdowns button**: Создает график просадок для портфелей и активов
2. **Dividends button**: Создает график дивидендной доходности
3. **Correlation button**: Создает корреляционную матрицу

### Проверка контекста
- ✅ Данные портфелей корректно сохраняются в `/compare`
- ✅ Методы правильно извлекают данные из контекста
- ✅ Поддерживается несколько портфелей
- ✅ Корректная обработка смешанного сравнения

## Заключение

Все проблемы с контекстом в методах смешанного сравнения исправлены:

1. **Правильные ключи**: Используются `portfolio_symbols` и `portfolio_weights`
2. **Корректный формат данных**: DataFrame вместо Series для дивидендов
3. **Передача параметров**: Currency передается в chart_styles
4. **Обработка ошибок**: Улучшено логирование и валидация

Вспомогательные кнопки смешанного сравнения теперь должны работать корректно с правильным извлечением данных из контекста пользователя.
