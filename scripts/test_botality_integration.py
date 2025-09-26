#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции с Botality API
"""

import asyncio
import sys
import os
import logging
from unittest.mock import Mock

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.botality_service import BotalityService, initialize_botality_service, send_botality_analytics
from config import Config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_botality_service():
    """Тестирование Botality сервиса"""
    logger.info("🧪 Тестирование Botality сервиса...")
    
    # Тестовый токен
    test_token = "46422ed2-e3b1-4c71-846a-81694cf2b18c"
    
    # Создаем мок объект Update
    mock_update = Mock()
    mock_message = Mock()
    mock_user = Mock()
    
    mock_user.id = 12345
    mock_user.is_bot = False
    mock_user.username = "test_user"
    
    mock_message.message_id = 67890
    mock_message.from_user = mock_user
    mock_message.text = "Тестовое сообщение"
    mock_message.date = Mock()
    mock_message.date.timestamp.return_value = 1692612310
    
    mock_update.message = mock_message
    
    # Тестируем сервис
    service = BotalityService(test_token)
    
    # Подготавливаем данные
    message_data = service.prepare_message_data(mock_update)
    logger.info(f"📊 Подготовленные данные: {message_data}")
    
    # Отправляем аналитику синхронно
    result = service.send_message_analytics_sync(message_data)
    logger.info(f"✅ Результат синхронной отправки: {result}")
    
    # Отправляем аналитику асинхронно
    result_async = await service.send_message_analytics(message_data)
    logger.info(f"✅ Результат асинхронной отправки: {result_async}")
    
    # Тестируем асинхронную отправку
    await service.send_analytics_async(mock_update)
    logger.info("✅ Асинхронная отправка выполнена")
    
    logger.info("🎉 Тестирование завершено!")


async def test_global_service():
    """Тестирование глобального сервиса"""
    logger.info("🧪 Тестирование глобального Botality сервиса...")
    
    # Инициализируем глобальный сервис
    test_token = "46422ed2-e3b1-4c71-846a-81694cf2b18c"
    initialize_botality_service(test_token)
    
    # Создаем мок объект Update
    mock_update = Mock()
    mock_message = Mock()
    mock_user = Mock()
    
    mock_user.id = 54321
    mock_user.is_bot = False
    mock_user.username = "global_test_user"
    
    mock_message.message_id = 98765
    mock_message.from_user = mock_user
    mock_message.text = "Глобальное тестовое сообщение"
    mock_message.date = Mock()
    mock_message.date.timestamp.return_value = 1692612310
    
    mock_update.message = mock_message
    
    # Тестируем глобальную функцию
    await send_botality_analytics(mock_update)
    logger.info("✅ Глобальная отправка аналитики выполнена")
    
    logger.info("🎉 Тестирование глобального сервиса завершено!")


async def main():
    """Основная функция тестирования"""
    logger.info("🚀 Запуск тестирования интеграции Botality...")
    
    try:
        # Тестируем прямой сервис
        await test_botality_service()
        
        # Небольшая пауза
        await asyncio.sleep(1)
        
        # Тестируем глобальный сервис
        await test_global_service()
        
        logger.info("✅ Все тесты прошли успешно!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
