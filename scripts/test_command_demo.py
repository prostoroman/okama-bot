#!/usr/bin/env python3
"""
Демонстрация работы команды /test
"""

import sys
import os
import asyncio

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
from tests.test_utilities import TestDataGenerator


async def demo_test_command():
    """Демонстрация работы команды /test"""
    print("🧪 Демонстрация команды /test")
    print("=" * 40)
    
    # Создаем бота
    bot = ShansAi()
    
    # Создаем mock объекты
    generator = TestDataGenerator()
    mock_update = generator.create_mock_update(12345, "/test quick")
    mock_context = generator.create_mock_context()
    
    print("📱 Тестирование команды /test quick...")
    
    try:
        # Запускаем команду
        await bot.test_command(mock_update, mock_context)
        
        # Проверяем, что сообщения были отправлены
        if mock_context.bot.send_message.called:
            print("✅ Команда /test успешно выполнена")
            
            # Получаем аргументы вызова
            call_args = mock_context.bot.send_message.call_args
            message_text = call_args[1]['text']
            parse_mode = call_args[1].get('parse_mode', None)
            
            print(f"📝 Отправлено сообщение (parse_mode: {parse_mode}):")
            print("-" * 40)
            print(message_text[:200] + "..." if len(message_text) > 200 else message_text)
            print("-" * 40)
        else:
            print("❌ Команда /test не отправила сообщение")
            
    except Exception as e:
        print(f"❌ Ошибка при выполнении команды: {e}")
    
    print("\n🔧 Тестирование различных типов тестов...")
    
    # Тестируем разные типы тестов
    test_types = ['quick', 'regression', 'all', 'comprehensive']
    
    for test_type in test_types:
        print(f"\n📊 Тестирование /test {test_type}...")
        
        # Создаем новый mock с нужным аргументом
        mock_update = generator.create_mock_update(12345, f"/test {test_type}")
        mock_context = generator.create_mock_context()
        
        try:
            await bot.test_command(mock_update, mock_context)
            print(f"✅ /test {test_type} выполнен успешно")
        except Exception as e:
            print(f"❌ Ошибка в /test {test_type}: {e}")
    
    print("\n🎯 Демонстрация форматирования результатов...")
    
    # Тестируем форматирование результатов
    test_results = [
        {
            'success': True,
            'stdout': 'Test passed\nAll tests completed successfully',
            'stderr': '',
            'duration': 1.5,
            'test_type': 'quick'
        },
        {
            'success': False,
            'stdout': 'Some output',
            'stderr': 'Test failed\nError message',
            'duration': 2.0,
            'test_type': 'regression'
        }
    ]
    
    for i, result in enumerate(test_results, 1):
        print(f"\n📋 Пример {i} - {'Успех' if result['success'] else 'Неудача'}:")
        formatted = bot._format_test_results(result, result['test_type'])
        print("-" * 40)
        print(formatted[:300] + "..." if len(formatted) > 300 else formatted)
        print("-" * 40)
    
    print("\n🎉 Демонстрация завершена!")


if __name__ == '__main__':
    print("🚀 Запуск демонстрации команды /test")
    
    try:
        asyncio.run(demo_test_command())
    except KeyboardInterrupt:
        print("\n⏹️ Демонстрация прервана пользователем")
    except Exception as e:
        print(f"\n💥 Ошибка при демонстрации: {e}")
        sys.exit(1)
