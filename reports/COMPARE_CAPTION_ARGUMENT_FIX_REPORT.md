# Отчет об исправлении ошибки аргументов в функции _create_enhanced_chart_caption

## 🎯 Проблема
При выполнении команды `/compare` возникала ошибка:
```
❌ Ошибка при создании сравнения: ShansAi.createenhancedchartcaption() takes 4 positional arguments but 5 were given
```

## 🔍 Анализ проблемы

### Корневая причина
Функция `_create_enhanced_chart_caption` была определена с 3 параметрами:
```python
def _create_enhanced_chart_caption(self, symbols: list, currency: str, specified_period: str) -> str:
```

Но вызывалась с 4 аргументами:
```python
caption = self._create_enhanced_chart_caption(
    symbols, currency, specified_period, display_symbols  # ← лишний аргумент
)
```

### Местоположение проблемы
- **Файл**: `bot.py`
- **Строки**: 3715-3717
- **Функция**: `compare_command()`

## ✅ Исправление

### Что было изменено:
Удален лишний аргумент `display_symbols` из вызова функции:

**До исправления:**
```python
caption = self._create_enhanced_chart_caption(
    symbols, currency, specified_period, display_symbols
)
```

**После исправления:**
```python
caption = self._create_enhanced_chart_caption(
    symbols, currency, specified_period
)
```

## 🔧 Технические детали

### Функция `_create_enhanced_chart_caption`:
- **Назначение**: Создает подпись к графику накопленной доходности
- **Параметры**: 
  - `symbols`: список символов активов
  - `currency`: валюта расчета
  - `specified_period`: указанный период анализа
- **Возвращает**: HTML-отформатированную подпись

### Формат подписи:
```
📈 <b>График накопленной доходности</b>

<b>Активы:</b> SPY.US, QQQ.US
<b>Валюта:</b> USD
<b>Период:</b> 5Y
```

## ✅ Результат
- ✅ Ошибка аргументов исправлена
- ✅ Команда `/compare` работает корректно
- ✅ Подпись к графику отображается правильно
- ✅ Нет новых ошибок линтера

## 📝 Примечания
Параметр `display_symbols` не использовался в функции `_create_enhanced_chart_caption`, поэтому его удаление не влияет на функциональность. Функция использует параметр `symbols` для отображения списка активов в подписи.
