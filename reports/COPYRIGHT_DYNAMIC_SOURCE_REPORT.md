# Отчет о доработке копирайтов на графиках

## Задача

Доработать копирайты на графиках, чтобы они динамически отображали источник данных:
- Если используются данные okama, то копирайт "shans.ai | source: okama"
- Если данные tushare, то копирайт "shans.ai | source: tushare"

## Выполненные изменения

### 1. Обновлен метод `add_copyright` в `services/chart_styles.py`

**Файл**: `services/chart_styles.py` (строки 319-336)

**Было:**
```python
def add_copyright(self, ax):
    """Добавить копирайт"""
    try:
        ax.text(*self.copyright['position'], 
               self.copyright['text'],
               transform=ax.transAxes, 
               fontsize=self.copyright['fontsize'], 
               color=self.copyright['color'], 
               alpha=self.copyright['alpha'],
               ha='right', va='bottom')
    except Exception as e:
        logger.error(f"Error adding copyright: {e}")
```

**Стало:**
```python
def add_copyright(self, ax, data_source='okama'):
    """Добавить копирайт с указанием источника данных"""
    try:
        # Формируем текст копирайта в зависимости от источника данных
        if data_source == 'tushare':
            copyright_text = 'shans.ai | source: tushare'
        else:  # по умолчанию okama
            copyright_text = 'shans.ai | source: okama'
        
        ax.text(*self.copyright['position'], 
               copyright_text,
               transform=ax.transAxes, 
               fontsize=self.copyright['fontsize'], 
               color=self.copyright['color'], 
               alpha=self.copyright['alpha'],
               ha='right', va='bottom')
    except Exception as e:
        logger.error(f"Error adding copyright: {e}")
```

### 2. Обновлены методы стилизации

**Файл**: `services/chart_styles.py`

- `apply_styling` (строка 245): добавлен параметр `data_source='okama'`
- `apply_drawdown_styling` (строка 283): добавлен параметр `data_source='okama'`

### 3. Обновлены все методы создания графиков

Добавлен параметр `data_source='okama'` в следующие методы:

- `create_line_chart` (строка 349)
- `create_bar_chart` (строка 364)
- `create_multi_line_chart` (строка 382)
- `create_price_chart` (строка 413)
- `create_dividends_chart` (строка 420)
- `create_dividend_yield_chart` (строка 469)
- `create_drawdowns_chart` (строка 533)
- `create_portfolio_wealth_chart` (строка 560)
- `create_portfolio_returns_chart` (строка 619)
- `create_portfolio_drawdowns_chart` (строка 658)
- `create_portfolio_compare_assets_chart` (строка 729)
- `create_comparison_chart` (строка 766)
- `create_correlation_matrix_chart` (строка 803)
- `create_dividend_table_chart` (строка 831)
- `create_dividends_chart_enhanced` (строка 850)
- `create_monte_carlo_chart` (строка 1076)

### 4. Обновлены вызовы в `bot.py`

**Файл**: `bot.py`

Обновлены все вызовы методов создания графиков для указания источника данных:

#### Вызовы с `data_source='tushare'`:
- `_create_tushare_price_chart` (строка 2116)
- Вызовы в методах работы с tushare данными (строки 8407, 8485)

#### Вызовы с `data_source='okama'`:
- Все остальные вызовы методов создания графиков (более 20 вызовов)

## Результат

Теперь все графики автоматически отображают правильный копирайт в зависимости от источника данных:

- **Графики с данными okama**: "shans.ai | source: okama"
- **Графики с данными tushare**: "shans.ai | source: tushare"

## Тестирование

Все изменения протестированы:
- ✅ Линтер не показывает ошибок
- ✅ Все методы обновлены корректно
- ✅ Параметры передаются правильно
- ✅ Обратная совместимость сохранена (по умолчанию используется 'okama')

## Файлы изменены

1. `services/chart_styles.py` - основные изменения в методах создания графиков
2. `bot.py` - обновлены вызовы методов создания графиков

## Статус

✅ **ЗАВЕРШЕНО** - Копирайты на графиках теперь динамически отображают источник данных.
