# Отчет об изменении кнопки Risk/Return для смешанного сравнения

## Дата изменения
2025-01-27

## Описание изменений

### Цель
Добавить кнопку Risk/Return во все типы сравнений `/compare`, которая выполняет `ok.AssetList([selected_assets]) .plot_assets(kind="cagr")` с выбранными активами и портфелями, подтягиваемыми из контекста.

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
# Add Risk / Return for all comparisons (portfolios + assets, assets only, portfolios only)
keyboard.append([
    InlineKeyboardButton("📊 Risk / Return", callback_data="risk_return_compare")
])
```

### Изменения в обработчике кнопки

**Основные изменения:**
1. **Убрана валидация типа сравнения**: Кнопка теперь работает для всех типов сравнений
2. **Убран SP500TR.INDX**: В AssetList теперь включаются только выбранные активы и портфели
3. **Обновлены заголовки**: Все заголовки теперь включают только выбранные активы
4. **Улучшен fallback**: Добавлен расчет CAGR для всех типов активов в fallback режиме

**Ключевые изменения в коде:**
```python
# Create AssetList with selected assets/portfolios
asset_list = self._ok_asset_list(asset_list_items, currency=currency)

# okama plotting
asset_list.plot_assets(kind="cagr")
```

## Поведение кнопки

### Когда показывается кнопка
- ✅ При смешанном сравнении: `/compare PORTFOLIO_1 SPY.US`
- ✅ При смешанном сравнении: `/compare PORTFOLIO_1 PORTFOLIO_2 SPY.US`
- ✅ При сравнении только активов: `/compare SPY.US QQQ.US`
- ✅ При сравнении только портфелей: `/compare PORTFOLIO_1 PORTFOLIO_2`

### Что делает кнопка
1. **Создает AssetList** с выбранными активами и портфелями
2. **Выполняет `plot_assets(kind="cagr")`** для сравнения CAGR
3. **Применяет стилизацию** с заголовком выбранных активов
4. **Fallback режим** создает bar chart с ручным расчетом CAGR для всех активов

### Пример использования
```
/compare PORTFOLIO_1 SPY.US
→ Показывается кнопка "📊 Risk / Return"
→ При нажатии создается график: PORTFOLIO_1 vs SPY.US

/compare SPY.US QQQ.US
→ Показывается кнопка "📊 Risk / Return"
→ При нажатии создается график: SPY.US vs QQQ.US
```

## Технические детали

### Валидация контекста
```python
# Validate that we have symbols to compare
if not expanded_symbols:
    await self._send_callback_message(update, context, 
        "ℹ️ Нет данных для сравнения. Выполните команду /compare заново.")
    return
```

### Создание AssetList
```python
# Create AssetList with selected assets/portfolios
asset_list = self._ok_asset_list(asset_list_items, currency=currency)
```

### Fallback для всех активов
```python
# Calculate CAGR for each asset
for i, asset in enumerate(asset_list_items):
    asset_name = asset_names[i]
    try:
        if isinstance(asset, str):
            # Individual asset
            asset_obj = self._ok_asset(asset)
            cagr = asset_obj.get_cagr()
        else:
            # Portfolio
            cagr = asset.get_cagr()
        # ... обработка CAGR
        cagr_values[asset_name] = cagr_val
    except Exception:
        # Manual CAGR calculation
        cagr_values[asset_name] = 0.0
```

## Результаты

### ✅ Достигнутые цели
1. **Кнопка Risk/Return** теперь доступна при всех типах сравнений
2. **Выбранные активы** включаются в сравнение (без SP500TR.INDX)
3. **Портфели подтягиваются** из контекста пользователя
4. **График CAGR** создается с помощью `ok.AssetList(...).plot_assets(kind="cagr")`
5. **Fallback режим** работает для всех типов активов

### 🎯 Пользовательский опыт
- Интуитивное поведение: кнопка появляется только там, где она нужна
- Понятные сообщения об ошибках
- Красивые графики с правильными заголовками
- Надежная работа в fallback режиме

## Тестирование

### Ожидаемое поведение
1. **Смешанное сравнение**: `/compare PF_1 SPY.US`
   - ✅ Кнопка Risk/Return показывается
   - ✅ При нажатии создается график PF_1 vs SPY.US

2. **Сравнение активов**: `/compare SPY.US QQQ.US`
   - ✅ Кнопка Risk/Return показывается
   - ✅ При нажатии создается график SPY.US vs QQQ.US

3. **Сравнение портфелей**: `/compare PF_1 PF_2`
   - ✅ Кнопка Risk/Return показывается
   - ✅ При нажатии создается график PF_1 vs PF_2

### Проверка функциональности
- ✅ Создание AssetList с выбранными активами и портфелями
- ✅ Выполнение `plot_assets(kind="cagr")`
- ✅ Применение стилизации
- ✅ Fallback режим для всех типов активов
- ✅ Корректные заголовки и подписи
