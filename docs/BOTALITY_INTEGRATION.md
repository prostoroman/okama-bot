# Интеграция с Botality Analytics

## Обзор

Бот интегрирован с [Botality](https://botality.cc/) для сбора аналитики использования. Botality предоставляет детальную статистику по сообщениям, пользователям и активности бота.

## Конфигурация

### Переменные окружения

Добавьте в ваш `config.env` файл:

```env
# Botality Analytics Configuration
# Get your token from https://botality.cc/
BOTALITY_TOKEN=your_botality_token_here
```

### Тестовый токен

Для тестирования используется токен: `46422ed2-e3b1-4c71-846a-81694cf2b18c`

## Архитектура

### Сервис BotalityService

Основной сервис находится в `services/botality_service.py`:

- **BotalityService**: Класс для работы с Botality API
- **initialize_botality_service()**: Инициализация глобального сервиса
- **send_botality_analytics()**: Удобная функция для отправки аналитики

### Интеграция в бот

Аналитика автоматически отправляется в следующих случаях:

1. **Команды**: `/start`, `/info`, `/compare`, `/portfolio`
2. **Сообщения**: Все текстовые сообщения пользователей
3. **Callback queries**: Нажатия на кнопки

### Данные, отправляемые в Botality

```json
{
  "token": "your_botality_token",
  "data": {
    "message_id": 123456,
    "from": {
      "id": 78910,
      "is_bot": false,
      "username": "user123"
    },
    "date": 1692612310,
    "text": "Hello, world!"
  }
}
```

## Использование

### Автоматическая отправка

Аналитика отправляется автоматически при каждом сообщении пользователя. Никаких дополнительных действий не требуется.

### Ручная отправка

```python
from services.botality_service import send_botality_analytics

# В обработчике сообщения
await send_botality_analytics(update)
```

### Тестирование

Запустите тестовый скрипт:

```bash
python scripts/test_botality_integration.py
```

## API Botality

### Endpoint

- **URL**: `https://botality.cc/api/v1/messages`
- **Method**: `POST`
- **Content-Type**: `application/json`

### Ответ

```json
{
  "status": "ok"
}
```

## Обработка ошибок

Сервис включает надежную обработку ошибок:

- **Таймауты**: 10 секунд
- **Сетевые ошибки**: Логируются как предупреждения
- **Неблокирующая отправка**: Аналитика не влияет на работу бота

## Логирование

Все события логируются с соответствующими уровнями:

- **DEBUG**: Успешная отправка
- **WARNING**: Ошибки сети/API
- **ERROR**: Неожиданные ошибки

## Мониторинг

Проверьте логи бота для мониторинга работы аналитики:

```bash
# Поиск сообщений Botality в логах
grep -i "botality" logs/bot.log
```

## Безопасность

- Токен хранится в переменных окружения
- Данные пользователей отправляются только в Botality
- Нет локального хранения аналитических данных

## Troubleshooting

### Проблемы с сетью

Если возникают проблемы с подключением к Botality:

1. Проверьте интернет-соединение
2. Убедитесь, что нет блокировки прокси
3. Проверьте правильность токена

### Отсутствие данных в Botality

1. Проверьте токен в конфигурации
2. Убедитесь, что бот отправляет сообщения
3. Проверьте логи на наличие ошибок

## Дополнительные ресурсы

- [Botality Documentation](https://botality.cc/docs/api-integration/)
- [Botality Dashboard](https://botality.cc/dashboard)
- [API Reference](https://botality.cc/api/v1/docs)
