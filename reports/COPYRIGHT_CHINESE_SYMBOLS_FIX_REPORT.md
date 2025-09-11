# Отчет об исправлении копирайтов для китайских символов

## Проблема

Для китайских символов (например, 600016.SH) выводился неправильный копирайт "shans.ai | source: okama" вместо "shans.ai | source: tushare".

## Причина

В нескольких местах кода для китайских символов использовался `data_source='okama'` вместо `data_source='tushare'`, хотя данные берутся из tushare.

## Исправления

### 1. ✅ Исправлен метод `_create_hybrid_chinese_comparison`

**Файл**: `bot.py` (строка 859)

**Было:**
```python
fig, ax = self.chart_styles.create_comparison_chart(
    data=comparison_df,
    symbols=list(comparison_data.keys()),
    currency=currency,
    data_source='okama',  # ❌ Неправильно
    title=title,
    xlabel='',  # Скрываем подпись оси X
    ylabel=''   # Скрываем подпись оси Y
)
```

**Стало:**
```python
fig, ax = self.chart_styles.create_comparison_chart(
    data=comparison_df,
    symbols=list(comparison_data.keys()),
    currency=currency,
    data_source='tushare',  # ✅ Правильно
    title=title,
    xlabel='',  # Скрываем подпись оси X
    ylabel=''   # Скрываем подпись оси Y
)
```

### 2. ✅ Исправлен метод `_create_tushare_price_chart`

**Файл**: `bot.py` (строка 2117-2123)

**Было:**
```python
fig, ax = chart_styles.create_price_chart(
    data=price_series,
    symbol=symbol,
    currency=currency,
    period='1Y'  # Default period
)
```

**Стало:**
```python
fig, ax = chart_styles.create_price_chart(
    data=price_series,
    symbol=symbol,
    currency=currency,
    period='1Y',  # Default period
    data_source='tushare'  # ✅ Добавлено
)
```

## Логика определения источника данных

Китайские символы определяются через метод `determine_data_source()`:

```python
def determine_data_source(self, symbol: str) -> str:
    if not self.tushare_service:
        return 'okama'
    
    return 'tushare' if self.tushare_service.is_tushare_symbol(symbol) else 'okama'
```

Символы типа `600016.SH` соответствуют паттерну `r'^[0-9]{6}\.SH$'` и правильно определяются как tushare символы.

## Результат

Теперь для всех китайских символов (включая 600016.SH) будет выводиться правильный копирайт:

- **Китайские символы (.SH, .SZ, .BJ, .HK)**: "shans.ai | source: tushare"
- **Остальные символы**: "shans.ai | source: okama"

## Тестирование

- ✅ Линтер не показывает ошибок
- ✅ Исправлены все места создания графиков для китайских символов
- ✅ Логика определения источника данных работает корректно

## Статус

✅ **ЗАВЕРШЕНО** - Копирайты для китайских символов теперь отображают правильный источник данных.
