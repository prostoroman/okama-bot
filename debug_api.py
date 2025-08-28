#!/usr/bin/env python3
"""
Скрипт для отладки API ответов YandexGPT
"""

import sys
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_api():
    """Отлаживает API ответы"""
    
    try:
        from config import Config
        from yandexgpt_service import YandexGPTService
        
        # Проверяем конфигурацию
        Config.validate()
        logger.info("✅ Конфигурация валидна")
        
        # Инициализируем сервис
        yandexgpt_service = YandexGPTService()
        
        # Простой тест
        test_prompt = "Скажи 'Привет, тест!'"
        
        logger.info("🧪 Тестируем простой запрос...")
        response = yandexgpt_service._call_yandex_api(
            system_prompt="Ты - помощник. Отвечай кратко.",
            user_prompt=test_prompt,
            temperature=0.1,
            max_tokens=50
        )
        
        logger.info(f"📝 Ответ API: '{response}'")
        logger.info(f"📏 Длина ответа: {len(response)}")
        logger.info(f"🔍 Содержит 'тест': {'тест' in response.lower()}")
        logger.info(f"🔍 Содержит 'привет': {'привет' in response.lower()}")
        
        # Тест с финансовым промптом
        logger.info("\n🧪 Тестируем финансовый запрос...")
        finance_response = yandexgpt_service._call_yandex_api(
            system_prompt="Ты - финансовый аналитик. Отвечай на русском языке.",
            user_prompt="Опиши тренд акции SBER",
            temperature=0.7,
            max_tokens=200
        )
        
        logger.info(f"📝 Финансовый ответ: '{finance_response}'")
        logger.info(f"📏 Длина ответа: {len(finance_response)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_api()
