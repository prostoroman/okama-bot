# Отчет об исправлении параметра copyright для команды /info

## Проблема

При выполнении команды `/info SBER.MOEX` бот отвечал:
```
📊 Получаю информацию об активе SBER.MOEX...
📈 Получаю ежедневный график...
❌ Не удалось получить ежедневный график
```

**Причина:** Ошибка в методе `create_price_chart` в `services/chart_styles.py`:
```
services.chart_styles.ChartStyles.create_line_chart() got multiple values for keyword argument 'copyright'
```

Проблема заключалась в том, что метод `create_price_chart` передавал параметр `copyright=False` как позиционный аргумент в `create_line_chart`, но `create_line_chart` ожидает только `(data, title, ylabel, xlabel='', **kwargs)`. Это приводило к конфликту параметров.

## Решение

### 1. Исправление `create_price_chart` в `services/chart_styles.py`

**Было:**
```python
def create_price_chart(self, data, symbol, currency, period='', **kwargs):
    """Создать график цен актива"""
    title = f'Динамика цены: {symbol} ({period})' if period else f'Динамика цены: {symbol}'
    ylabel = f'Цена ({currency})' if currency else 'Цена'
    return self.create_line_chart(data, title, ylabel, copyright=False, **kwargs)
```

**Стало:**
```python
def create_price_chart(self, data, symbol, currency, period='', **kwargs):
    """Создать график цен актива"""
    title = f'Динамика цены: {symbol} ({period})' if period else f'Динамика цены: {symbol}'
    ylabel = f'Цена ({currency})' if currency else 'Цена'
    # Pass copyright=False through kwargs to avoid duplicate parameter error
    kwargs['copyright'] = False
    return self.create_line_chart(data, title, ylabel, **kwargs)
```

### 2. Обновление `create_line_chart` для обработки параметра copyright

**Было:**
```python
def create_line_chart(self, data, title, ylabel, xlabel='', **kwargs):
    """Создать линейный график"""
    fig, ax = self.create_chart(**kwargs)
    
    if hasattr(data, 'plot'):
        data.plot(ax=ax, linewidth=self.lines['width'], alpha=self.lines['alpha'])
    else:
        ax.plot(data.index, data.values, linewidth=self.lines['width'], alpha=self.lines['alpha'])
    
    self.apply_styling(ax, title=title, ylabel=ylabel, xlabel=xlabel, legend=False)
    return fig, ax
```

**Стало:**
```python
def create_line_chart(self, data, title, ylabel, xlabel='', **kwargs):
    """Создать линейный график"""
    fig, ax = self.create_chart(**kwargs)
    
    if hasattr(data, 'plot'):
        data.plot(ax=ax, linewidth=self.lines['width'], alpha=self.lines['alpha'])
    else:
        ax.plot(data.index, data.values, linewidth=self.lines['width'], alpha=self.lines['alpha'])
    
    # Extract copyright parameter from kwargs and pass to apply_styling
    copyright_param = kwargs.pop('copyright', True)
    self.apply_styling(ax, title=title, ylabel=ylabel, xlabel=xlabel, legend=False, copyright=copyright_param)
    return fig, ax
```

## Затронутые файлы

- `services/chart_styles.py`
  - Исправлен метод `create_price_chart`
  - Обновлен метод `create_line_chart`

## Проверка

Создан тестовый скрипт `test_info_fix.py` для проверки исправления:

```bash
python3 test_info_fix.py
```

**Результат:**
```
✅ Asset info successful: Sberbank Rossii PAO
✅ Price history successful
   - Has charts: True
   - Has prices: True
   - Currency: RUB
   - Chart types: ['adj_close', 'close_monthly']
   - Price data points: 365
   - Price data type: <class 'pandas.core.series.Series'>
✅ All tests passed! The info command fix is working correctly.
```

## Технические детали

- **Проблема:** Конфликт параметров при передаче `copyright=False` как позиционного аргумента
- **Решение:** Передача параметра через `**kwargs` и извлечение в `create_line_chart`
- **Результат:** Успешное создание ежедневных графиков для MOEX активов

## Примечания

- Исправление не влияет на другие типы графиков
- Сохранена обратная совместимость с существующим кодом
- Параметр `copyright` по умолчанию остается `True` для других вызовов
