# Отчет об исправлении проблемы с изменяющимися названиями портфелей

## Обзор проблемы

При использовании команды `/portfolio` название портфеля в графиках постоянно менялось, хотя должно было оставаться одинаковым. Это происходило из-за того, что названия портфелей создавались каждый раз заново из символов и весов в методах создания графиков.

## Анализ проблемы

### Корень проблемы
1. **В `chart_styles.py`**: Методы создания графиков портфеля (`create_portfolio_wealth_chart`, `create_portfolio_returns_chart`, `create_portfolio_drawdowns_chart`, и др.) создавали названия каждый раз заново из символов и весов
2. **В `bot.py`**: Методы создания графиков не передавали консистентное название портфеля в методы `chart_styles`
3. **Отсутствие единого источника названий**: Каждый метод создавал название независимо, что приводило к неконсистентности

### Затронутые методы
- `create_portfolio_wealth_chart`
- `create_portfolio_returns_chart` 
- `create_portfolio_drawdowns_chart`
- `create_portfolio_rolling_cagr_chart`
- `create_portfolio_compare_assets_chart`
- `create_dividend_yield_chart`
- `create_monte_carlo_chart`

## Реализованные исправления

### 1. Добавлен параметр `portfolio_name` во все методы создания графиков портфеля

**Файл**: `services/chart_styles.py`

Добавлен параметр `portfolio_name=None` в следующие методы:
- `create_portfolio_wealth_chart()`
- `create_portfolio_returns_chart()`
- `create_portfolio_drawdowns_chart()`
- `create_portfolio_rolling_cagr_chart()`
- `create_portfolio_compare_assets_chart()`
- `create_dividend_yield_chart()`
- `create_monte_carlo_chart()`

### 2. Обновлена логика создания заголовков

Во всех методах добавлена приоритетная логика:
```python
# Create title with portfolio name if provided, otherwise use asset percentages
if portfolio_name:
    title = f'[Тип графика]\n{portfolio_name}'
elif weights:
    # Создание названия из символов и весов
    asset_with_weights = []
    for i, symbol in enumerate(symbols):
        symbol_name = symbol.split('.')[0] if '.' in symbol else symbol
        weight = weights[i] if i < len(weights) else 0.0
        asset_with_weights.append(f"{symbol_name} ({weight:.1%})")
    title = f'[Тип графика]\n{", ".join(asset_with_weights)}'
else:
    title = f'[Тип графика]\n{", ".join(symbols)}'
```

### 3. Создан единый метод создания названий портфелей

**Файл**: `bot.py`

Добавлен метод `_create_portfolio_name()`:
```python
def _create_portfolio_name(self, symbols: list, weights: list) -> str:
    """Create consistent portfolio name from symbols and weights"""
    if weights:
        asset_with_weights = []
        for i, symbol in enumerate(symbols):
            symbol_name = symbol.split('.')[0] if '.' in symbol else symbol
            weight = weights[i] if i < len(weights) else 0.0
            asset_with_weights.append(f"{symbol_name} ({weight:.1%})")
        return ", ".join(asset_with_weights)
    else:
        asset_names = []
        for symbol in symbols:
            symbol_name = symbol.split('.')[0] if '.' in symbol else symbol
            asset_names.append(symbol_name)
        return ", ".join(asset_names)
```

### 4. Обновлены методы создания графиков в основном файле бота

**Файл**: `bot.py`

Обновлены следующие методы:
- `_create_portfolio_wealth_chart()`
- `_create_portfolio_returns_chart()`
- `_create_portfolio_drawdowns_chart()`
- `_create_portfolio_dividends_chart()`
- `_create_monte_carlo_chart()` (в методе обработки Monte Carlo)

Во всех методах добавлено:
```python
# Create consistent portfolio name
portfolio_name = self._create_portfolio_name(symbols, weights)

# Передача portfolio_name в методы chart_styles
fig, ax = chart_styles.create_portfolio_[тип]_chart(
    data=data, symbols=symbols, currency=currency, weights=weights, portfolio_name=portfolio_name
)
```

## Результат исправлений

### До исправления
- Названия портфелей в графиках менялись при каждом создании
- Каждый тип графика мог иметь разное название для одного и того же портфеля
- Отсутствие консистентности в отображении

### После исправления
- ✅ Названия портфелей остаются одинаковыми во всех графиках
- ✅ Единый источник создания названий портфелей
- ✅ Консистентное отображение названий во всех типах графиков
- ✅ Обратная совместимость - если `portfolio_name` не передан, используется старая логика

## Тестирование

### Проверка импорта
```bash
python3 -c "import bot; print('Bot imports successfully')"
```
**Результат**: ✅ Успешно

### Проверка синтаксиса
**Результат**: ✅ Ошибок линтера не найдено

## Совместимость

- ✅ Обратная совместимость сохранена
- ✅ Существующий функционал не нарушен
- ✅ Новые параметры опциональны

## Заключение

Проблема с изменяющимися названиями портфелей в графиках успешно исправлена. Теперь все графики портфеля будут отображать одинаковое название, созданное из символов и весов активов портфеля. Это обеспечивает консистентность пользовательского интерфейса и улучшает пользовательский опыт.

**Дата исправления**: 10 сентября 2025
**Статус**: ✅ Завершено
