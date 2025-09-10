# Отчет об исправлении легенды графика накопленной доходности

## Проблема

На графике накопленной доходности портфеля в легенде отображалось неправильное название портфеля (например, `portfolio_2444.PF`), которое не соответствовало сохраненному названию портфеля.

**Пример проблемы:**
- Сохраненный портфель: "Мой Портфель"
- В легенде показывалось: "portfolio_2444.PF"
- Должно было показываться: "Мой Портфель"

## Корень проблемы

1. **Функция `create_portfolio_wealth_chart`** в `services/chart_styles.py` не передавала параметр `portfolio_name` в функцию `_create_portfolio_wealth_chart` в `bot.py`

2. **Данные `portfolio.wealth_index`** возвращают DataFrame с несколькими колонками (портфель + валюта), а не просто Series

3. **Название колонки портфеля** в DataFrame создавалось автоматически библиотекой `okama` и не соответствовало желаемому названию

## Исправления

### 1. ✅ Обновлена функция `create_portfolio_wealth_chart` в `services/chart_styles.py`

**Изменения:**
- Добавлена обработка DataFrame (не только Series)
- Реализована логика переименования первой колонки (портфель) в желаемое название
- Сохранена обратная совместимость для Series

**Код:**
```python
elif isinstance(data, pd.DataFrame):
    # If it's already a DataFrame, rename the first column to our portfolio name
    if len(data.columns) > 0:
        if portfolio_name:
            column_name = portfolio_name
        elif weights:
            asset_with_weights = []
            for i, symbol in enumerate(symbols):
                symbol_name = symbol.split('.')[0] if '.' in symbol else symbol
                weight = weights[i] if i < len(weights) else 0.0
                asset_with_weights.append(f"{symbol_name} ({weight:.1%})")
            column_name = ", ".join(asset_with_weights)
        else:
            column_name = ", ".join(symbols)
        
        # Rename the first column (portfolio column) to our desired name
        data = data.copy()
        data.columns = [column_name] + list(data.columns[1:])
```

### 2. ✅ Обновлена функция `_create_portfolio_wealth_chart` в `bot.py`

**Изменения:**
- Добавлен параметр `portfolio_name: str = None`
- Передача `portfolio_name` в `chart_styles.create_portfolio_wealth_chart`

**Код:**
```python
async def _create_portfolio_wealth_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str, weights: list, portfolio_name: str = None):
    # ...
    fig, ax = chart_styles.create_portfolio_wealth_chart(
        data=wealth_index, symbols=symbols, currency=currency, weights=weights, portfolio_name=portfolio_name
    )
```

### 3. ✅ Обновлены вызовы функции

**В `_handle_portfolio_wealth_chart_button`:**
- Передается "Портфель" как общее название

**В `_handle_portfolio_wealth_chart_by_symbol`:**
- Передается `portfolio_symbol` как название портфеля

## Тестирование

Создан тест `test_wealth_chart_legend_fix.py` для проверки исправления:

### Результаты тестирования:
- ✅ **С названием портфеля**: Легенда показывает "Мой Портфель"
- ✅ **Без названия портфеля**: Легенда показывает "AAPL (60.0%), MSFT (40.0%)"
- ✅ **Конвертация данных**: Series правильно конвертируется в DataFrame с правильным названием колонки

**Все тесты прошли успешно (3/3)**

## Влияние на функциональность

### До исправления:
- В легенде отображались автоматически сгенерированные названия типа `portfolio_2444.PF`
- Название портфеля не соответствовало сохраненному названию
- Пользователи видели непонятные технические названия

### После исправления:
- В легенде отображается правильное название портфеля
- Для сохраненных портфелей показывается их сохраненное название
- Для новых портфелей показывается название с весами активов
- Легенда стала понятной и информативной

## Файлы изменены

1. **services/chart_styles.py**:
   - Обновлена функция `create_portfolio_wealth_chart` для обработки DataFrame
   - Добавлена логика переименования колонок

2. **bot.py**:
   - Обновлена функция `_create_portfolio_wealth_chart` для передачи `portfolio_name`
   - Обновлены вызовы функции с правильными названиями портфелей

3. **tests/test_wealth_chart_legend_fix.py** (новый файл):
   - Тесты для проверки корректности отображения легенды

## Заключение

Исправление полностью решает проблему с неправильным отображением названия портфеля в легенде графика накопленной доходности. Теперь легенда показывает понятные и информативные названия, соответствующие ожиданиям пользователей.
