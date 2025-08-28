# Команда /namespace добавлена

## Описание
Добавлена новая команда `/namespace` в Okama Finance Bot для просмотра доступных пространств имен и символов в них.

## Функциональность

### Без аргументов: `/namespace`
Выводит список всех доступных пространств имен с описанием:
```
📚 Доступные пространства имен (namespaces):

CBR - Central Banks official currency exchange rates
CC - Cryptocurrency pairs with USD
COMM - Commodities prices
FX - FOREX currency market
INDX - Indexes
INFL - Inflation
LSE - London Stock Exchange
MOEX - Moscow Exchange
PF - Investment Portfolios
PIF - Russian open-end mutual funds
RATE - Bank deposit rates
RATIO - Financial ratios
RE - Real estate prices
US - US Stock Exchanges and mutual funds
XAMS - Euronext Amsterdam
XETR - XETRA Exchange
XFRA - Frankfurt Stock Exchange
XSTU - Stuttgart Exchange
XTAE - Tel Aviv Stock Exchange (TASE)
```

### С аргументом: `/namespace INDX`
Выводит все символы в указанном пространстве имен в виде таблицы, сгруппированной по первой букве:
```
📊 Символы в пространстве INDX:

A:
`AEX` | `AFX` | `ASX`

B:
`BET` | `BETX` | `BETXTR`

C:
`CAC` | `CAC40` | `CAC40TR`

...

📈 Всего символов: 1781
```

## Техническая реализация

### Добавленные файлы
- Обновлен `bot.py` с новым методом `namespace_command()`

### Изменения в существующих файлах
1. **bot.py**:
   - Добавлен метод `async def namespace_command()`
   - Зарегистрирован обработчик команды в `run()`
   - Обновлена справка в `help_command()`
   - Обновлена справка в `start_command()`

### Особенности реализации
- Использует библиотеку `okama` для получения данных
- Обрабатывает ошибки импорта и выполнения
- Форматирует вывод в читаемом виде
- Группирует символы по алфавиту для лучшей читаемости
- Ограничивает количество символов в строке для избежания переполнения

## Использование

### Примеры команд
```
/namespace                    # Список всех пространств имен
/namespace INDX              # Символы в пространстве индексов
/namespace US                # Символы в пространстве US бирж
/namespace MOEX              # Символы Московской биржи
/namespace FX                # Валютные пары
/namespace COMM              # Товарные активы
```

### Интеграция с существующими командами
Команда `/namespace` дополняет существующие команды:
- `/start` - общая справка
- `/help` - подробная справка по командам
- `/asset` - анализ конкретного актива
- `/namespace` - **НОВОЕ** - просмотр пространств имен и символов

## Тестирование
Функциональность протестирована:
- ✅ Импорт библиотеки okama
- ✅ Получение списка namespaces
- ✅ Получение символов в конкретном namespace
- ✅ Компиляция кода без ошибок
- ✅ Импорт класса бота без ошибок

## Совместимость
- Python 3.7+
- python-telegram-bot
- okama библиотека
- Все существующие функции бота сохранены
