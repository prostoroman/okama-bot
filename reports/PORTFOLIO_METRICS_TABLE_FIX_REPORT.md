# Отчет об исправлении ошибки создания таблицы метрик портфеля

## 🐛 Проблема

При использовании кнопки "Метрики" в команде `/portfolio` возникала ошибка:

```
❌ Не удалось создать таблицу метрик
ERROR - Error creating summary metrics table: [Errno portfolio_5533.PF is not found in the database.] 404
```

## 🔍 Причина

Проблема заключалась в том, что функция `_create_summary_metrics_table` пыталась создать `ok.AssetList(symbols, ccy=currency)` с символом портфеля (например, `portfolio_5533.PF`), но портфели не являются обычными активами в базе данных okama и не могут быть найдены через `ok.AssetList`.

### Анализ кода
- **Расположение**: `bot.py`, строки 11098-11115
- **Проблемная логика**: Передача символа портфеля в `_create_summary_metrics_table`
- **Ошибка**: `ok.AssetList(['portfolio_5533.PF'], ccy='RUB')` - портфель не найден в базе данных

## ✅ Исправления

### 1. Создана новая функция `_create_portfolio_summary_metrics_table`

**Расположение**: `bot.py`, строки 8217-8376

**Функциональность**:
- Создает таблицу метрик специально для портфелей
- Использует объект `ok.Portfolio` вместо `ok.AssetList`
- Рассчитывает метрики на основе данных `portfolio.wealth_index`
- Возвращает таблицу в том же формате, что и `_create_summary_metrics_table`

**Ключевые метрики**:
- Среднегодовая доходность (CAGR)
- Волатильность
- Коэффициент Шарпа
- Максимальная просадка
- Безрисковая ставка
- Состав портфеля

### 2. Обновлена логика кнопки "Метрики" портфеля

**Расположение**: `bot.py`, строки 11117-11125

**Изменения**:
```python
# Старый код (ПРОБЛЕМНЫЙ)
summary_table = self._create_summary_metrics_table(
    symbols=[portfolio_symbol], 
    currency=currency, 
    expanded_symbols=expanded_symbols, 
    portfolio_contexts=portfolio_contexts, 
    specified_period=None
)

# Новый код (ИСПРАВЛЕННЫЙ)
portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
summary_table = self._create_portfolio_summary_metrics_table(
    portfolio, valid_symbols, valid_weights, currency
)
```

### 3. Исправлена подготовка данных для AI-анализа

**Расположение**: `bot.py`, строки 14736-14747

**Изменения**:
```python
# Старый код (ПРОБЛЕМНЫЙ)
expanded_symbols = [portfolio_symbol]  # Portfolio symbol as single item
data_info = await self._prepare_data_for_analysis([portfolio_symbol], currency, expanded_symbols, portfolio_contexts, user_id)

# Новый код (ИСПРАВЛЕННЫЙ)
expanded_symbols = valid_symbols  # Individual assets
data_info = await self._prepare_data_for_analysis(valid_symbols, currency, expanded_symbols, portfolio_contexts, user_id)
```

## 🔧 Технические детали

### Алгоритм расчета метрик

1. **Получение данных**: Из `portfolio.wealth_index`
2. **CAGR**: `((final_price / initial_price) ^ (1 / years)) - 1`
3. **Волатильность**: `returns.std() * sqrt(12)` (annualized для месячных данных)
4. **Sharpe Ratio**: `(cagr - risk_free_rate) / volatility`
5. **Max Drawdown**: `min((prices - running_max) / running_max)`

### Обработка ошибок

- **Проверка данных**: Валидация наличия `wealth_index`
- **Fallback значения**: "N/A" для недоступных метрик
- **Логирование**: Предупреждения о проблемах расчета
- **Graceful degradation**: Частичные результаты при ошибках

### Формат таблицы

```markdown
| Метрика | Значение |
| :--- | :--- |
| Среднегодовая доходность (CAGR) | 12.34% |
| Волатильность | 15.67% |
| Коэфф. Шарпа | 0.789 |
| Макс. просадка | -8.90% |
| Безрисковая ставка | 5.25% |
| Состав портфеля | SBER.MOEX (60.0%), LKOH.MOEX (40.0%) |
```

## 📊 Результаты тестирования

### Создан тест `test_portfolio_metrics_fix.py`

**Результаты**:
```
✅ Функция _create_portfolio_summary_metrics_table существует
✅ Таблица метрик портфеля создана успешно
✅ Все ключевые метрики присутствуют
🎉 Все тесты прошли успешно!
```

### Проверенные сценарии

1. **Создание таблицы**: Успешно для портфеля SBER.MOEX + LKOH.MOEX
2. **Формат метрик**: Все ключевые метрики присутствуют
3. **Обработка ошибок**: Graceful handling при недоступности данных

## 🎯 Ожидаемый результат

После исправления:

1. **Кнопка "Метрики"** в `/portfolio` работает без ошибок
2. **Таблица метрик** отображается в правильном формате
3. **AI-анализ** портфеля работает корректно
4. **Консистентность** с командой `/compare` сохранена

## 📝 Заключение

Ошибка была успешно исправлена путем:

1. **Создания специализированной функции** для портфелей
2. **Использования правильных объектов** okama (Portfolio вместо AssetList)
3. **Исправления подготовки данных** для AI-анализа
4. **Сохранения консистентности** интерфейса

Теперь команда `/portfolio` работает стабильно и предоставляет пользователям корректные таблицы метрик и AI-анализ.
