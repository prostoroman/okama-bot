# 🔍 Детали запросов к Vision API

## 📋 Заголовки запросов

### Основные заголовки
```http
Authorization: Api-Key {YOUR_API_KEY}
Content-Type: application/json
```

### Детали заголовков
- **Authorization**: `Api-Key {api_key}` - аутентификация через API ключ
- **Content-Type**: `application/json` - формат данных запроса
- **User-Agent**: Автоматически добавляется requests (Python)
- **Accept**: Автоматически добавляется requests (Python)

## 📤 Структура запроса

### Основной формат Vision API
```json
{
  "modelUri": "gpt://{folder_id}/{model_name}",
  "completionOptions": {
    "temperature": "0.7",
    "maxTokens": "1000",
    "stream": false
  },
  "messages": [
    {
      "role": "system",
      "text": "Ты - опытный финансовый аналитик. Анализируй графики и изображения, предоставляя профессиональные выводы на русском языке."
    },
    {
      "role": "user",
      "text": "{question}",
      "image": {
        "data": "{image_bytes_hex}",
        "mimeType": "image/png"
      }
    }
  ]
}
```

### Альтернативный формат Vision API
```json
{
  "modelUri": "gpt://{folder_id}/{model_name}",
  "completionOptions": {
    "temperature": "0.7",
    "maxTokens": "1000",
    "stream": false
  },
  "text": "{question}\n\nАнализируй это изображение: {image_description}",
  "image": {
    "data": "{image_bytes_hex}",
    "mimeType": "image/png"
  }
}
```

## 🌐 Endpoint

### URL запроса
```
POST https://llm.api.cloud.yandex.net/foundationModels/v1/completion
```

### Параметры запроса
- **Method**: POST
- **URL**: `https://llm.api.cloud.yandex.net/foundationModels/v1/completion`
- **Timeout**: 60 секунд
- **Proxies**: Отключены (`session.trust_env = False`)

## 🚨 Ошибки и их обработка

### 1. Ошибка 500 - Внутренняя ошибка сервера
```json
{
  "error": {
    "grpcCode": 13,
    "httpCode": 500,
    "message": "Fatal internal error in TextGenerationService.Completion",
    "httpStatus": "Internal Server Error",
    "details": []
  }
}
```

**Обработка в коде:**
```python
elif response.status_code == 500:
    print(f"⚠️ Vision API internal error (status 500): {response.text}")
    return f"Не удалось проанализировать изображение (внутренняя ошибка сервера). Попробуйте позже или используйте текстовый запрос."
```

### 2. Ошибка 400 - Неверный запрос
```json
{
  "error": {
    "grpcCode": 3,
    "httpCode": 400,
    "message": "Invalid request format",
    "httpStatus": "Bad Request",
    "details": []
  }
}
```

**Обработка в коде:**
```python
elif response.status_code == 400:
    print(f"⚠️ Vision API bad request (status 400): {response.text}")
    return f"Не удалось проанализировать изображение (неверный запрос). Попробуйте отправить другое изображение."
```

### 3. Ошибка 401 - Неавторизованный доступ
```json
{
  "error": {
    "grpcCode": 16,
    "httpCode": 401,
    "message": "Unknown api key '{api_key}'",
    "httpStatus": "Unauthorized",
    "details": []
  }
}
```

**Обработка в коде:**
```python
else:
    print(f"⚠️ Vision API returned status {response.status_code}: {response.text}")
    # Try alternative vision format
    return self._try_alternative_vision_format(model_name, question, image_bytes, image_description)
```

## 🔧 Технические детали

### Сессия и прокси
```python
# Создаем сессию без прокси
session = requests.Session()
session.trust_env = False  # Игнорируем переменные окружения прокси

response = session.post(
    vision_url,
    headers=headers,
    json=request_data,
    timeout=60
)
```

### Обработка изображений
```python
"image": {
    "data": image_bytes.hex(),  # Конвертация в hex строку
    "mimeType": "image/png"     # Формат изображения
}
```

### Модели Vision API
```python
vision_models = ["yandexgpt-vision", "yandexgpt-pro"]
```

## 📊 Примеры реальных запросов

### Запрос 1: Анализ графика SBER.MOEX
```json
{
  "modelUri": "gpt://{folder_id}/yandexgpt-vision",
  "completionOptions": {
    "temperature": "0.7",
    "maxTokens": "1000",
    "stream": false
  },
  "messages": [
    {
      "role": "system",
      "text": "Ты - опытный финансовый аналитик. Анализируй графики и изображения, предоставляя профессиональные выводы на русском языке."
    },
    {
      "role": "user",
      "text": "Проанализируй график цен для SBER.MOEX (Sberbank Rossii PAO).\n\nЗадача: Опиши конкретно то, что видишь на графике:\n1. Тренд (восходящий/нисходящий/боковой)\n2. Ключевые уровни поддержки и сопротивления\n3. Волатильность (высокая/средняя/низкая)\n\nАнализ должен быть кратким и конкретным на русском языке (2-3 предложения).",
      "image": {
        "data": "89504e470d0a1a0a0000000d49484452...",
        "mimeType": "image/png"
      }
    }
  ]
}
```

### Заголовки запроса
```http
POST /foundationModels/v1/completion HTTP/1.1
Host: llm.api.cloud.yandex.net
Authorization: Api-Key {YOUR_API_KEY}
Content-Type: application/json
Content-Length: {length}
User-Agent: python-requests/2.31.0
Accept: */*
Accept-Encoding: gzip, deflate
Connection: keep-alive
```

## 🔍 Диагностика проблем

### Логирование ошибок
```python
print(f"⚠️ Vision API internal error (status 500): {response.text}")
print(f"⚠️ Vision API bad request (status 400): {response.text}")
print(f"⚠️ Vision API returned status {response.status_code}: {response.text}")
```

### Fallback механизм
```python
# Try alternative vision format
return self._try_alternative_vision_format(model_name, question, image_bytes, image_description)
```

## 💡 Рекомендации по отладке

### 1. Проверка заголовков
- Убедиться, что `Authorization` содержит правильный API ключ
- Проверить формат `Content-Type: application/json`

### 2. Проверка данных
- Валидировать `modelUri` формат
- Проверить размер изображения (не слишком большое)
- Убедиться в корректности hex кодировки

### 3. Мониторинг ошибок
- Отслеживать статус коды ответов
- Анализировать детали ошибок от Yandex
- Логировать все неудачные запросы

## 📝 Заключение

Vision API использует стандартный REST API с JSON форматом данных. Основные проблемы связаны с:

1. **Внутренними ошибками Yandex Cloud** (500)
2. **Форматированием запросов** (400)
3. **Аутентификацией** (401)

Система корректно обрабатывает все типы ошибок и предоставляет fallback механизмы для обеспечения стабильности.
