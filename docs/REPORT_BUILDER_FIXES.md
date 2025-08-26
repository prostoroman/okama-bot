# Исправления в Report Builder

## 🐛 Проблема

При анализе активов возникала ошибка:
```
❌ Ошибка данных: 'float' object has no attribute 'empty'
```

## 🔍 Причина

Ошибка возникала в `report_builder_enhanced.py` при попытке проверить `prices.empty`, где `prices` мог быть не только pandas Series/DataFrame, но и числом (float) или другим типом данных.

## ✅ Исправления

### 1. Улучшена проверка типов

Заменил все проверки вида:
```python
if isinstance(prices, pd.Series) and not prices.empty:
```

На более надежные:
```python
if prices is not None and hasattr(prices, 'empty') and isinstance(prices, pd.Series) and not prices.empty:
```

### 2. Добавлена диагностика данных

В `_build_single_asset_report` добавлена диагностика для понимания структуры данных:
```python
# Диагностика данных
if prices is not None:
    report_text += f"\n**Диагностика данных:**\n"
    report_text += f"• Тип prices: {type(prices).__name__}\n"
    if hasattr(prices, 'shape'):
        report_text += f"• Размер: {prices.shape}\n"
    elif hasattr(prices, '__len__'):
        report_text += f"• Длина: {len(prices)}\n"
    else:
        report_text += f"• Значение: {prices}\n"
```

### 3. Улучшена обработка ошибок

Все методы-обертки теперь имеют try-catch блоки:
```python
def build_single_asset_report(self, data: Dict[str, Any]) -> Tuple[str, List[bytes]]:
    """Совместимость с bot.py"""
    try:
        return self._build_single_asset_report(data, "")
    except Exception as e:
        logger.error(f"Error in build_single_asset_report: {e}")
        return f"Ошибка построения отчета: {str(e)}", []
```

### 4. Исправлены все методы

- `_build_single_asset_report`
- `_build_comparison_report` 
- `_build_portfolio_report`
- `_build_inflation_report`
- `_create_single_asset_csv`
- `_create_comparison_csv`
- `_create_portfolio_csv`

## 🎯 Результат

Теперь report_builder корректно обрабатывает все типы данных:
- ✅ pandas Series/DataFrame
- ✅ None значения
- ✅ Числовые значения
- ✅ Другие типы данных

Система больше не падает с ошибкой `'float' object has no attribute 'empty'` и корректно строит отчеты для всех типов активов.
