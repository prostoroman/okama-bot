# Отчет об изменении кнопки Risk/Return для смешанного сравнения

## Дата изменения
2025-01-27

## Описание изменений

### Цель
Добавить кнопку Risk/Return в смешанное сравнение `/compare`, которая выполняет `ok.AssetList(["SP500TR.INDX", rf3, rf4]) .plot_assets(kind="cagr")` с портфелями, подтягиваемыми из контекста.

### Изменения в логике показа кнопки

**До изменения:**
```python
# Add Risk / Return for portfolio-only comparisons
if has_portfolios_only:
    keyboard.append([
        InlineKeyboardButton("📊 Risk / Return", callback_data="risk_return_compare")
    ])
```

**После изменения:**
```python
# Add Risk / Return for mixed comparisons (portfolios + assets)
if is_mixed_comparison:
    keyboard.append([
        InlineKeyboardButton("📊 Risk / Return", callback_data="risk_return_compare")
    ])
```

### Изменения в обработчике кнопки

**Основные изменения:**
1. **Изменена валидация**: Теперь проверяется наличие смешанного сравнения вместо только портфелей
2. **Добавлен SP500TR.INDX**: В AssetList теперь включается `["SP500TR.INDX"] + portfolios`
3. **Обновлены заголовки**: Все заголовки теперь включают "SP500TR.INDX vs портфели"
4. **Улучшен fallback**: Добавлен расчет CAGR для SP500TR.INDX в fallback режиме

**Ключевые изменения в коде:**
```python
# Create AssetList with SP500TR.INDX and portfolios
asset_list_items = ["SP500TR.INDX"] + portfolios
asset_list = self._ok_asset_list(asset_list_items, currency=currency)

# okama plotting
asset_list.plot_assets(kind="cagr")
```

## Поведение кнопки

### Когда показывается кнопка
- ✅ При смешанном сравнении: `/compare PORTFOLIO_1 SPY.US`
- ✅ При смешанном сравнении: `/compare PORTFOLIO_1 PORTFOLIO_2 SPY.US`
- ❌ При сравнении только активов: `/compare SPY.US QQQ.US`
- ❌ При сравнении только портфелей: `/compare PORTFOLIO_1 PORTFOLIO_2`

### Что делает кнопка
1. **Создает AssetList** с `["SP500TR.INDX", portfolio1, portfolio2, ...]`
2. **Выполняет `plot_assets(kind="cagr")`** для сравнения CAGR
3. **Применяет стилизацию** с заголовком "SP500TR.INDX vs портфели"
4. **Fallback режим** создает bar chart с ручным расчетом CAGR

### Пример использования
```
/compare PORTFOLIO_1 SPY.US
→ Показывается кнопка "📊 Risk / Return"
→ При нажатии создается график: SP500TR.INDX vs PORTFOLIO_1
```

## Технические детали

### Валидация контекста
```python
# Validate that this is a mixed comparison
if not expanded_symbols or not portfolio_contexts:
    await self._send_callback_message(update, context, 
        "ℹ️ Кнопка доступна только при смешанном сравнении (портфели + активы)")
    return
```

### Создание AssetList
```python
# Create list with SP500TR.INDX and portfolios
asset_list_items = ["SP500TR.INDX"] + portfolios
asset_list = self._ok_asset_list(asset_list_items, currency=currency)
```

### Fallback для SP500TR.INDX
```python
# Add SP500TR.INDX CAGR
try:
    sp500 = self._ok_asset("SP500TR.INDX")
    sp500_cagr = sp500.get_cagr()
    # ... обработка CAGR
    cagr_values["SP500TR.INDX"] = sp500_val
except Exception as e:
    self.logger.warning(f"Failed to get SP500TR.INDX CAGR: {e}")
    cagr_values["SP500TR.INDX"] = 0.0
```

## Результаты

### ✅ Достигнутые цели
1. **Кнопка Risk/Return** теперь доступна при смешанном сравнении
2. **SP500TR.INDX** включается в сравнение автоматически
3. **Портфели подтягиваются** из контекста пользователя
4. **График CAGR** создается с помощью `ok.AssetList(...).plot_assets(kind="cagr")`
5. **Fallback режим** работает для всех компонентов

### 🎯 Пользовательский опыт
- Интуитивное поведение: кнопка появляется только там, где она нужна
- Понятные сообщения об ошибках
- Красивые графики с правильными заголовками
- Надежная работа в fallback режиме

## Тестирование

### Ожидаемое поведение
1. **Смешанное сравнение**: `/compare PF_1 SPY.US`
   - ✅ Кнопка Risk/Return показывается
   - ✅ При нажатии создается график SP500TR.INDX vs PF_1

2. **Сравнение активов**: `/compare SPY.US QQQ.US`
   - ❌ Кнопка Risk/Return НЕ показывается

3. **Сравнение портфелей**: `/compare PF_1 PF_2`
   - ❌ Кнопка Risk/Return НЕ показывается

### Проверка функциональности
- ✅ Создание AssetList с SP500TR.INDX и портфелями
- ✅ Выполнение `plot_assets(kind="cagr")`
- ✅ Применение стилизации
- ✅ Fallback режим для всех компонентов
- ✅ Корректные заголовки и подписи
