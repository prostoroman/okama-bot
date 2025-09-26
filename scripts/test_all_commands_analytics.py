#!/usr/bin/env python3
"""
Тестовый скрипт для проверки аналитики во всех командах бота
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


def create_mock_update(command: str = None, text: str = None, callback_data: str = None):
    """Создание мок объекта Update для тестирования"""
    mock_update = Mock()
    mock_user = Mock()
    
    mock_user.id = 12345
    mock_user.is_bot = False
    mock_user.username = "test_user"
    
    if command:
        # Для команд
        mock_message = Mock()
        mock_message.message_id = 67890
        mock_message.from_user = mock_user
        mock_message.text = f"/{command}"
        mock_message.date = Mock()
        mock_message.date.timestamp.return_value = 1692612310
        
        mock_update.message = mock_message
        mock_update.callback_query = None
        
    elif text:
        # Для текстовых сообщений
        mock_message = Mock()
        mock_message.message_id = 67891
        mock_message.from_user = mock_user
        mock_message.text = text
        mock_message.date = Mock()
        mock_message.date.timestamp.return_value = 1692612310
        
        mock_update.message = mock_message
        mock_update.callback_query = None
        
    elif callback_data:
        # Для callback queries
        mock_callback = Mock()
        mock_callback.id = "callback_123"
        mock_callback.from_user = mock_user
        mock_callback.data = callback_data
        mock_callback.message = Mock()
        mock_callback.message.message_id = 67892
        mock_callback.message.date = Mock()
        mock_callback.message.date.timestamp.return_value = 1692612310
        
        mock_update.message = None
        mock_update.callback_query = mock_callback
    
    return mock_update


async def test_command_analytics():
    """Тестирование аналитики для всех команд"""
    logger.info("🧪 Тестирование аналитики для всех команд...")
    
    # Инициализируем сервис
    test_token = "46422ed2-e3b1-4c71-846a-81694cf2b18c"
    initialize_botality_service(test_token)
    
    # Список всех команд
    commands = [
        "start", "help", "support", "rate", "limits", 
        "info", "list", "search", "compare", "portfolio"
    ]
    
    results = {}
    
    for command in commands:
        try:
            mock_update = create_mock_update(command=command)
            await send_botality_analytics(mock_update)
            results[command] = "✅ OK"
            logger.info(f"  {command}: ✅ OK")
        except Exception as e:
            results[command] = f"❌ Error: {e}"
            logger.error(f"  {command}: ❌ Error: {e}")
    
    return results


async def test_message_analytics():
    """Тестирование аналитики для текстовых сообщений"""
    logger.info("🧪 Тестирование аналитики для текстовых сообщений...")
    
    test_messages = [
        "AAPL.US",
        "VOO.US, SPY.US",
        "Hello bot!",
        "Test message"
    ]
    
    results = {}
    
    for message in test_messages:
        try:
            mock_update = create_mock_update(text=message)
            await send_botality_analytics(mock_update)
            results[message] = "✅ OK"
            logger.info(f"  '{message}': ✅ OK")
        except Exception as e:
            results[message] = f"❌ Error: {e}"
            logger.error(f"  '{message}': ❌ Error: {e}")
    
    return results


async def test_callback_analytics():
    """Тестирование аналитики для callback queries"""
    logger.info("🧪 Тестирование аналитики для callback queries...")
    
    test_callbacks = [
        "analyze_chart",
        "show_portfolio",
        "compare_assets",
        "button_click"
    ]
    
    results = {}
    
    for callback in test_callbacks:
        try:
            mock_update = create_mock_update(callback_data=callback)
            await send_botality_analytics(mock_update)
            results[callback] = "✅ OK"
            logger.info(f"  '{callback}': ✅ OK")
        except Exception as e:
            results[callback] = f"❌ Error: {e}"
            logger.error(f"  '{callback}': ❌ Error: {e}")
    
    return results


async def test_reply_keyboard_analytics():
    """Тестирование аналитики для reply keyboard"""
    logger.info("🧪 Тестирование аналитики для reply keyboard...")
    
    test_buttons = [
        "📊 Портфель",
        "🔍 Поиск",
        "📈 Сравнить",
        "ℹ️ Информация"
    ]
    
    results = {}
    
    for button in test_buttons:
        try:
            mock_update = create_mock_update(text=button)
            await send_botality_analytics(mock_update)
            results[button] = "✅ OK"
            logger.info(f"  '{button}': ✅ OK")
        except Exception as e:
            results[button] = f"❌ Error: {e}"
            logger.error(f"  '{button}': ❌ Error: {e}")
    
    return results


async def main():
    """Основная функция тестирования"""
    logger.info("🚀 Запуск тестирования аналитики для всех команд...")
    
    try:
        # Тестируем команды
        command_results = await test_command_analytics()
        
        # Небольшая пауза
        await asyncio.sleep(0.5)
        
        # Тестируем сообщения
        message_results = await test_message_analytics()
        
        # Небольшая пауза
        await asyncio.sleep(0.5)
        
        # Тестируем callback queries
        callback_results = await test_callback_analytics()
        
        # Небольшая пауза
        await asyncio.sleep(0.5)
        
        # Тестируем reply keyboard
        keyboard_results = await test_reply_keyboard_analytics()
        
        # Выводим итоговый отчет
        logger.info("\n📊 ИТОГОВЫЙ ОТЧЕТ:")
        logger.info("=" * 50)
        
        logger.info("\n🔹 КОМАНДЫ:")
        for command, result in command_results.items():
            logger.info(f"  /{command}: {result}")
        
        logger.info("\n🔹 СООБЩЕНИЯ:")
        for message, result in message_results.items():
            logger.info(f"  '{message}': {result}")
        
        logger.info("\n🔹 CALLBACK QUERIES:")
        for callback, result in callback_results.items():
            logger.info(f"  '{callback}': {result}")
        
        logger.info("\n🔹 REPLY KEYBOARD:")
        for button, result in keyboard_results.items():
            logger.info(f"  '{button}': {result}")
        
        # Подсчитываем успешные тесты
        all_results = list(command_results.values()) + list(message_results.values()) + list(callback_results.values()) + list(keyboard_results.values())
        successful = sum(1 for result in all_results if result.startswith("✅"))
        total = len(all_results)
        
        logger.info(f"\n📈 СТАТИСТИКА: {successful}/{total} тестов прошли успешно")
        
        if successful == total:
            logger.info("🎉 Все тесты прошли успешно!")
            return 0
        else:
            logger.warning(f"⚠️ {total - successful} тестов завершились с ошибками")
            return 1
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при тестировании: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
