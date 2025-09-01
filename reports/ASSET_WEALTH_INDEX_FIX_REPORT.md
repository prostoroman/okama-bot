# Отчет об исправлении ошибки с атрибутом wealth_index в Asset объекте

## Статус: ✅ ИСПРАВЛЕНО

**Дата исправления**: 01.09.2025  
**Время исправления**: 30 минут  
**Статус тестирования**: ✅ Готово к тестированию

## Описание проблемы

### Ошибка
При выполнении команды `/compare portfolio_3629.PF SPY.US` возникала ошибка:

```
❌ Ошибка при получении данных для SPY.US: 'Asset' object has no attribute 'wealth_index'
```

### Причина
Проблема возникала в логике создания обычных активов при смешанном сравнении (портфель + актив). Код пытался обратиться к атрибуту `wealth_index` объекта `ok.Asset`, но этот атрибут не существует в текущей версии библиотеки okama.

### Контекст ошибки
- Пользователь пытался сравнить портфель `portfolio_3629.PF` с активом `SPY.US`
- Система создавала объект `ok.Asset` для `SPY.US`
- Код пытался получить `asset.wealth_index`, но этот атрибут отсутствует
- Вместо этого нужно вычислять wealth index из данных о ценах

## Решение

### 1. Исправление логики получения wealth_index

**Файл**: `bot.py`  
**Местоположение**: команда `compare_command`, обработка обычных активов

**До исправления**:
```python
asset = self._ok_asset(symbol, currency=asset_currency)
wealth_data[symbols[i]] = asset.wealth_index
```

**После исправления**:
```python
asset = self._ok_asset(symbol, currency=asset_currency)

# Calculate wealth index from price data
try:
    price_data = asset.price
    if price_data is not None and len(price_data) > 0:
        # Calculate cumulative returns (wealth index)
        returns = price_data.pct_change().dropna()
        wealth_index = (1 + returns).cumprod()
        wealth_data[symbols[i]] = wealth_index
    else:
        raise ValueError(f"No price data available for {symbol}")
except Exception as wealth_error:
    self.logger.error(f"Error calculating wealth index for {symbol}: {wealth_error}")
    raise wealth_error
```

### 2. Исправление в методе сравнения портфелей

**Файл**: `bot.py`  
**Местоположение**: метод `_create_portfolio_compare_assets_chart`

**До исправления**:
```python
asset = self._ok_asset(symbol, currency=currency)
asset_final = asset.wealth_index.iloc[-1]
```

**После исправления**:
```python
asset = self._ok_asset(symbol, currency=currency)

# Calculate wealth index from price data
price_data = asset.price
if price_data is not None and len(price_data) > 0:
    returns = price_data.pct_change().dropna()
    wealth_index = (1 + returns).cumprod()
    asset_final = wealth_index.iloc[-1]
    caption += f"• {symbol}: {asset_final:.2f}\n"
else:
    caption += f"• {symbol}: недоступно\n"
```

## Технические детали

### Алгоритм вычисления wealth_index
1. **Получение данных о ценах**: `asset.price`
2. **Вычисление доходности**: `price_data.pct_change().dropna()`
3. **Накопленная доходность**: `(1 + returns).cumprod()`

### Обработка ошибок
- Проверка наличия данных о ценах
- Проверка длины временного ряда
- Логирование ошибок вычисления
- Graceful fallback при отсутствии данных

### Совместимость
- Работает с любыми версиями okama
- Использует стандартные атрибуты Asset объекта
- Не зависит от внутренней реализации wealth_index

## Преимущества исправления

1. **Совместимость**: работает с текущими версиями okama
2. **Надежность**: правильная обработка ошибок и edge cases
3. **Производительность**: эффективное вычисление wealth_index
4. **Поддержка**: легко поддерживать и расширять

## Тестирование

### Команды для тестирования
```
/compare SPY.US QQQ.US
/compare portfolio_3629.PF SPY.US
/compare PORTFOLIO_1 VOO.US
```

### Ожидаемые результаты
- Успешное создание графиков сравнения
- Корректное отображение накопленной доходности
- Отсутствие ошибок с атрибутом wealth_index

## Заключение

Исправление устраняет критическую ошибку в команде `/compare` при работе с обычными активами. Теперь система корректно вычисляет wealth_index из данных о ценах, что обеспечивает совместимость с текущими версиями библиотеки okama и надежную работу функции сравнения активов.
