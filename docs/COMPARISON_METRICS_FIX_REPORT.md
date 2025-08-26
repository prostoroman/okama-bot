# Исправление метрик в сравнении активов

## 🐛 Проблема

При сравнении активов (например, "Динамика цен на нефть и золото") не отображались ключевые метрики:

```
**Сравнение активов**

**Активы:** GC.COMM, BRENT.COMM
**Валюта:** USD
**Период:** 5Y

**Ключевые метрики:** не отображаются
```

## 🔍 Причина

1. **Ошибки в `_create_metrics_table`**: Неправильная обработка `None` значений и ошибок форматирования
2. **Отсутствие диагностики**: Не было понимания, какие данные приходят и где происходят ошибки
3. **Проблемы с товарными активами**: GC.COMM и BRENT.COMM могли не обрабатываться корректно
4. **Отсутствие fallback**: Если основные метрики не работали, не было альтернативного способа показать данные

## ✅ Исправления

### 1. Улучшен `_create_metrics_table` в `report_builder_enhanced.py`

**Добавлена безопасная обработка значений:**
```python
# Безопасное извлечение значений с проверкой типов
cagr = metric_data.get('cagr')
volatility = metric_data.get('volatility')
sharpe = metric_data.get('sharpe')
max_drawdown = metric_data.get('max_drawdown')
total_return = metric_data.get('total_return')

# Форматируем значения с проверкой на None
'CAGR (%)': f"{cagr*100:.2f}" if cagr is not None else "N/A"
```

**Добавлена диагностика и fallback:**
- Логирование структуры метрик для отладки
- Fallback на текстовый формат при ошибках создания DataFrame
- Добавлено поле "Общая доходность (%)"

### 2. Улучшен `_build_comparison_report` в `report_builder_enhanced.py`

**Добавлена диагностика данных:**
```python
# Диагностика данных
logger.info(f"Building comparison report for tickers: {tickers}")
logger.info(f"Metrics keys: {list(metrics.keys()) if metrics else 'No metrics'}")
logger.info(f"Metrics structure: {metrics}")
logger.info(f"Prices shape: {prices.shape if hasattr(prices, 'shape') else 'No prices'}")
```

**Добавлен fallback для метрик:**
- Если основные метрики недоступны, создаются простые метрики из цен
- Отображение предупреждения о недоступности метрик
- Попытка вычисления базовых показателей (доходность, волатильность)

### 3. Добавлен метод `_compute_simple_metrics`

**Вычисление базовых метрик из цен:**
```python
def _compute_simple_metrics(self, prices: pd.Series) -> Dict[str, Any]:
    # Общая доходность
    total_return = (prices.iloc[-1] / prices.iloc[0]) - 1.0
    
    # Волатильность (годовая)
    returns = prices.pct_change().dropna()
    volatility = float(np.std(returns, ddof=1)) * np.sqrt(periods_per_year)
    
    return {'total_return': total_return, 'volatility': volatility}
```

### 4. Улучшен `_handle_asset_comparison` в `okama_handler_enhanced.py`

**Добавлена детальная диагностика:**
```python
logger.info(f"Aligned data shape: {aligned_data.shape}")
logger.info(f"Aligned data columns: {list(aligned_data.columns)}")
logger.info(f"Returns data shape: {returns_data.shape}")
logger.info(f"Computing metrics for {asset}, prices length: {len(asset_prices)}")
logger.info(f"Metrics for {asset}: {asset_metrics}")
```

**Улучшена обработка ошибок:**
- Try-catch блоки для каждого актива
- Проверка достаточности данных перед вычислением метрик
- Продолжение обработки при ошибках отдельных активов

## 🎯 Результат

Теперь сравнение активов:

✅ **Корректно отображает метрики:**
- CAGR, Волатильность, Sharpe Ratio
- Максимальная просадка, Общая доходность
- Безопасная обработка отсутствующих значений

✅ **Предоставляет диагностику:**
- Логирование всех этапов обработки
- Информация о структуре данных
- Отслеживание ошибок

✅ **Имеет fallback механизмы:**
- Простые метрики из цен при недоступности основных
- Текстовый формат при ошибках создания таблиц
- Продолжение работы при частичных ошибках

✅ **Улучшена обработка товарных активов:**
- GC.COMM (золото), BRENT.COMM (нефть)
- Корректное вычисление метрик для всех типов активов

## 🔧 Технические детали

**Поток обработки метрик:**
1. `okama_handler._handle_asset_comparison` → получение данных и вычисление метрик
2. `report_builder._build_comparison_report` → диагностика и отображение
3. `_create_metrics_table` → безопасное создание таблицы метрик
4. Fallback → простые метрики из цен при необходимости

**Структура метрик:**
```python
{
    'GC.COMM': {
        'cagr': 0.0856,
        'volatility': 0.2341,
        'sharpe': 0.366,
        'max_drawdown': -0.1567,
        'total_return': 0.4567
    },
    'BRENT.COMM': {
        'cagr': 0.0234,
        'volatility': 0.3456,
        'sharpe': 0.0678,
        'max_drawdown': -0.2345,
        'total_return': 0.1234
    }
}
```

Теперь сравнение активов работает корректно и отображает все ключевые метрики с красивым форматированием!
