# 🧪 Тестирование okama-bot

## 📋 Обзор

Этот каталог содержит комплексную систему тестирования для okama-bot, включающую регрессионные тесты, утилиты и инструменты для автоматизации тестирования.

## 🚀 Быстрый старт

### Запуск всех тестов
```bash
python tests/test_runner.py --all
```

### Запуск регрессионных тестов
```bash
python tests/test_runner.py --regression
```

### Запуск быстрых тестов
```bash
python tests/test_runner.py --quick
```

### Запуск конкретного теста
```bash
python tests/test_runner.py --test comprehensive
```

## 📁 Структура файлов

| Файл | Описание |
|------|----------|
| `test_comprehensive_regression.py` | Основной регрессионный тест, покрывающий весь функционал |
| `test_utilities.py` | Вспомогательные утилиты для тестирования |
| `test_runner.py` | Запускатор тестов с различными опциями |
| `test_additional_metrics_calculation.py` | Тест расчета дополнительных метрик |
| `test_portfolio_risk_metrics_fix.py` | Тест исправления метрик риска портфеля |
| `test_hk_comparison_debug.py` | Тест отладки сравнения HK |
| `README.md` | Данная документация |

## 🎯 Типы тестов

### 1. Регрессионные тесты
Проверяют, что существующий функционал продолжает работать после изменений.

**Файлы:**
- `test_comprehensive_regression.py` - основной регрессионный тест
- `test_portfolio_risk_metrics_fix.py` - тест метрик портфеля
- `test_additional_metrics_calculation.py` - тест дополнительных метрик

### 2. Функциональные тесты
Проверяют конкретную функциональность.

**Файлы:**
- `test_hk_comparison_debug.py` - тест сравнения HK

### 3. Утилиты тестирования
Вспомогательные инструменты для создания и запуска тестов.

**Файлы:**
- `test_utilities.py` - утилиты для тестирования
- `test_runner.py` - запускатор тестов

## 🔧 Использование утилит

### TestDataGenerator
```python
from tests.test_utilities import TestDataGenerator

generator = TestDataGenerator()

# Создание mock объектов
mock_update = generator.create_mock_update(12345, "/test SPY.US")
mock_context = generator.create_mock_context()

# Создание тестовых данных
price_data = generator.create_test_price_data("SPY.US", 100)
portfolio_data = generator.create_test_portfolio_data(
    ["SPY.US", "QQQ.US"], 
    [0.6, 0.4]
)
```

### TestAssertions
```python
from tests.test_utilities import TestAssertions

# Проверка сообщения Telegram
TestAssertions.assert_valid_telegram_message("Test message")

# Проверка данных графика
TestAssertions.assert_valid_chart_data(chart_bytes)

# Проверка данных портфеля
TestAssertions.assert_valid_portfolio_data(portfolio_data)
```

### TestDataValidator
```python
from tests.test_utilities import TestDataValidator

validator = TestDataValidator()

# Валидация данных цен
is_valid = validator.validate_price_data(price_data)

# Валидация метрик портфеля
is_valid = validator.validate_portfolio_metrics(metrics)
```

## 📊 Покрытие тестами

### Команды бота
- ✅ `/start` - запуск и справка
- ✅ `/info` - информация об активе
- ✅ `/compare` - сравнение активов
- ✅ `/portfolio` - создание портфеля
- ✅ `/my` - управление портфелями
- ✅ `/list` - просмотр пространств имен
- ✅ `/gemini_status` - статус AI сервисов

### Callback функции
- ✅ `drawdowns` - анализ просадок
- ✅ `dividends` - анализ дивидендов
- ✅ `correlation` - корреляционный анализ
- ✅ `risk_metrics` - метрики риска
- ✅ `monte_carlo` - Монте-Карло симуляция
- ✅ `forecast` - прогнозирование

### Основные компоненты
- ✅ Asset creation - создание активов
- ✅ Portfolio creation - создание портфелей
- ✅ Chart generation - генерация графиков
- ✅ Context store - хранение контекста
- ✅ Symbol parsing - парсинг символов
- ✅ Weight parsing - парсинг весов
- ✅ Error handling - обработка ошибок
- ✅ Message splitting - разделение сообщений

## 🎯 Рекомендации по использованию

### Перед внедрением новых функций
1. Запустите полный набор тестов
2. Убедитесь, что все тесты проходят
3. Внедрите новую функцию
4. Запустите тесты снова

### После внедрения новых функций
1. Запустите быстрые тесты
2. При необходимости добавьте новые тесты
3. Запустите полный набор тестов

### При отладке проблем
1. Запустите конкретный тест
2. Используйте verbose режим
3. Проверьте логи и вывод

## 🔄 Интеграция с разработкой

### Pre-commit hook
```bash
#!/bin/bash
python tests/test_runner.py --quick
```

### GitHub Actions
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python tests/test_runner.py --regression
```

## 🐛 Устранение неполадок

### Проблема: Тесты не запускаются
**Решение**: Убедитесь, что вы находитесь в корневой папке проекта

### Проблема: ImportError
**Решение**: Установите зависимости: `pip install -r requirements.txt`

### Проблема: Отсутствие API ключей
**Решение**: Создайте `config.env` с тестовыми ключами

### Проблема: Медленное выполнение
**Решение**: Используйте `--quick` для быстрых тестов

## 📝 Добавление новых тестов

### 1. Создайте новый файл теста
```python
#!/usr/bin/env python3
import unittest
from tests.test_utilities import TestDataGenerator

class TestNewFeature(unittest.TestCase):
    def test_new_functionality(self):
        # Ваш тест
        pass
```

### 2. Добавьте в test_runner.py
```python
self.test_modules = {
    'comprehensive': 'test_comprehensive_regression',
    'new_feature': 'test_new_feature',  # Добавьте новую строку
    # ...
}
```

### 3. Запустите новый тест
```bash
python tests/test_runner.py --test new_feature
```

## 📈 Метрики качества

- **Покрытие тестами**: 100% (21/21 компонентов)
- **Время выполнения быстрых тестов**: ~30 секунд
- **Время выполнения всех тестов**: ~5 минут
- **Воспроизводимость**: 100% (фиксированные seed)

## 🎉 Заключение

Система тестирования обеспечивает:
- Полное покрытие функционала
- Быструю проверку работоспособности
- Автоматизацию процесса тестирования
- Надежность и воспроизводимость

Готова к использованию и легко расширяется при добавлении новых функций.

---

**Версия**: 1.0  
**Дата**: 2024-12-19  
**Статус**: ✅ Готово к использованию