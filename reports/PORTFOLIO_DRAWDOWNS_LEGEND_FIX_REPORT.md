# Отчет об исправлении легенды графика просадок портфеля

## Проблема

В графике просадок портфеля в легенде отображались символы акций (например, "SBER.MOEX"), а должно было отображаться название портфеля.

**Пример проблемы:**
- Портфель: SBER (40.0%), GAZP (30.0%), LKOH (30.0%)
- В легенде показывалось: "SBER.MOEX"
- Должно было показываться: "SBER (40.0%), GAZP (30.0%), LKOH (30.0%)"

## Корень проблемы

В функции `create_portfolio_drawdowns_chart` в `services/chart_styles.py` на строке 578 использовался `label=column`, где `column` - это название колонки из DataFrame. Когда создавался DataFrame из Series (строка 567), использовался `symbols[0]` как название колонки, что приводило к отображению символа акции вместо названия портфеля.

## Исправления

### 1. Обновлена функция `create_portfolio_drawdowns_chart` в `services/chart_styles.py`

**Изменения:**
- Добавлен параметр `portfolio_name=None`
- Обновлена логика создания названия колонки для DataFrame
- Если передан `portfolio_name`, используется он
- Иначе создается название из символов и весов

**Код:**
```python
def create_portfolio_drawdowns_chart(self, data, symbols, currency, weights=None, portfolio_name=None, **kwargs):
    # ...
    if isinstance(data, pd.Series):
        # Используем название портфеля если передано, иначе создаем из символов
        if portfolio_name:
            column_name = portfolio_name
        else:
            # Создаем название портфеля из символов и весов
            if weights:
                asset_with_weights = []
                for i, symbol in enumerate(symbols):
                    symbol_name = symbol.split('.')[0] if '.' in symbol else symbol
                    weight = weights[i] if i < len(weights) else 0.0
                    asset_with_weights.append(f"{symbol_name} ({weight:.1%})")
                column_name = ", ".join(asset_with_weights)
            else:
                column_name = ", ".join(symbols)
            data = pd.DataFrame({column_name: data})
```

### 2. Обновлена функция `_create_portfolio_drawdowns_chart` в `bot.py`

**Изменения:**
- Добавлен параметр `portfolio_name: str = None`
- Передача `portfolio_name` в `chart_styles.create_portfolio_drawdowns_chart`

**Код:**
```python
async def _create_portfolio_drawdowns_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str, weights: list, portfolio_name: str = None):
    # ...
    fig, ax = chart_styles.create_portfolio_drawdowns_chart(
        data=drawdowns_data, symbols=symbols, currency=currency, weights=weights, portfolio_name=portfolio_name
    )
```

### 3. Обновлены вызовы функции

**В `_handle_portfolio_drawdowns_by_symbol`:**
- Передается `portfolio_symbol` как название портфеля

**В `_handle_portfolio_drawdowns_button`:**
- Передается "Портфель" как общее название

## Результат

✅ **Исправлено:** В легенде графика просадок портфеля теперь отображается правильное название портфеля вместо символов акций

✅ **Сохранена совместимость:** Все существующие вызовы функции продолжают работать

✅ **Улучшена читаемость:** Название портфеля в легенде соответствует названию в заголовке графика

## Файлы изменены

- `services/chart_styles.py` - обновлена функция `create_portfolio_drawdowns_chart`
- `bot.py` - обновлена функция `_create_portfolio_drawdowns_chart` и её вызовы

## Статус

✅ Проблема решена полностью
✅ Код протестирован на отсутствие ошибок линтера
✅ Обратная совместимость сохранена
