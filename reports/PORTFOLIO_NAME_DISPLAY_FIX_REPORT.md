# Отчет об исправлении отображения названия портфеля в графике сравнения с активами

## Проблема
В графике "Портфель vs Активы" отображалось случайное название портфеля вместо сохраненного названия из контекста пользователя.

## Анализ проблемы
Проблема заключалась в том, что функция `_create_portfolio_compare_assets_chart` не получала название портфеля из сохраненных данных пользователя. Название портфеля сохранялось в `saved_portfolios` в контексте пользователя, но не передавалось в функцию создания графика.

## Внесенные изменения

### 1. Обновление функции `_handle_portfolio_compare_assets_button`
- Добавлен код для поиска названия портфеля в сохраненных портфелях пользователя
- Название портфеля ищется по совпадению символов портфеля
- Добавлено логирование для отладки

```python
# Try to find portfolio name from saved portfolios
portfolio_name = None
saved_portfolios = user_context.get('saved_portfolios', {})

# Look for matching portfolio in saved portfolios
for portfolio_symbol, portfolio_data in saved_portfolios.items():
    if portfolio_data.get('symbols') == final_symbols:
        portfolio_name = portfolio_data.get('portfolio_name')
        self.logger.info(f"Found matching portfolio: {portfolio_symbol} with name: {portfolio_name}")
        break
```

### 2. Обновление функции `_handle_portfolio_compare_assets_by_symbol`
- Добавлено получение названия портфеля из `portfolio_info`
- Обновлено логирование для включения названия портфеля

```python
portfolio_name = portfolio_info.get('portfolio_name')
self.logger.info(f"Retrieved portfolio data: symbols={symbols}, weights={weights}, currency={currency}, name={portfolio_name}")
```

### 3. Обновление сигнатуры функции `_create_portfolio_compare_assets_chart`
- Добавлен параметр `portfolio_name: str = None`
- Обновлены все вызовы функции для передачи названия портфеля

### 4. Обновление вызова функции создания графика
- Передача параметра `portfolio_name` в `chart_styles.create_portfolio_compare_assets_chart`

## Результат
Теперь в графике "Портфель vs Активы" будет отображаться сохраненное название портфеля вместо случайного названия, основанного на символах и весах.

## Тестирование
Изменения протестированы на отсутствие ошибок линтера. Рекомендуется протестировать функциональность в реальных условиях использования бота.

## Файлы изменены
- `bot.py` - основные изменения в функциях обработки кнопок и создания графиков

## Дата исправления
${new Date().toISOString().split('T')[0]}
