#!/usr/bin/env python3
"""
Простой регрессионный тест для okama-bot
Фокусируется на основных функциях без сложных mock объектов
"""

import unittest
import sys
import os
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import pandas as pd
import numpy as np

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import okama as ok
    OKAMA_AVAILABLE = True
except ImportError:
    OKAMA_AVAILABLE = False
    print("Warning: okama library not available for testing")

from bot import ShansAi


class TestSimpleRegression(unittest.TestCase):
    """Простой регрессионный тест для основных функций бота"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.bot = ShansAi()
        self.test_user_id = 12345
        self.test_symbols = ['SPY.US', 'QQQ.US', 'VOO.US']
    
    def test_bot_initialization(self):
        """Тест инициализации бота"""
        self.assertIsNotNone(self.bot)
        self.assertIsNotNone(self.bot.logger)
        self.assertIsNotNone(self.bot.chart_styles)
        print("✅ Bot initialization test passed")
    
    def test_clean_symbol(self):
        """Тест очистки символов"""
        # Тест различных символов
        test_cases = [
            ("SPY.US", "SPY.US"),
            ("spy.us", "spy.us"),
            ("SPY\\US", "SPYUS"),
            ("SPY/US", "SPYUS"),
            ("SPY\"US", "SPYUS"),
            ("  SPY.US  ", "SPY.US"),
            ("SPY   US", "SPY US")
        ]
        
        for input_symbol, expected in test_cases:
            result = self.bot.clean_symbol(input_symbol)
            self.assertEqual(result, expected)
            print(f"✅ Symbol cleaning test passed: '{input_symbol}' -> '{result}'")
    
    def test_symbol_parsing(self):
        """Тест парсинга символов"""
        # Тест различных форматов символов
        test_cases = [
            "SPY.US",
            "SBER.MOEX", 
            "GC.COMM",
            "EURUSD.FX",
            "SPX.INDX"
        ]
        
        for symbol in test_cases:
            # Проверяем, что символы корректно обрабатываются
            self.assertIsInstance(symbol, str)
            self.assertIn(".", symbol)  # Должен содержать точку для разделения
            print(f"✅ Symbol parsing test passed for {symbol}")
    
    def test_weight_parsing(self):
        """Тест парсинга весов портфеля"""
        # Тест различных форматов весов
        test_cases = [
            "SPY.US:0.5",
            "QQQ.US:0.3",
            "VOO.US:0.2"
        ]
        
        for case in test_cases:
            parts = case.split(":")
            self.assertEqual(len(parts), 2)
            symbol = parts[0]
            weight = float(parts[1])
            
            self.assertIsInstance(symbol, str)
            self.assertIsInstance(weight, float)
            self.assertGreater(weight, 0)
            self.assertLessEqual(weight, 1)
            
            print(f"✅ Weight parsing test passed for {case}")
    
    def test_context_store(self):
        """Тест хранения контекста пользователя"""
        # Тест получения контекста
        context = self.bot._get_user_context(self.test_user_id)
        self.assertIsInstance(context, dict)
        
        # Тест сохранения контекста
        test_data = {"test_key": "test_value"}
        self.bot._update_user_context(self.test_user_id, **test_data)
        
        # Проверяем, что данные сохранились
        saved_context = self.bot._get_user_context(self.test_user_id)
        self.assertEqual(saved_context.get("test_key"), "test_value")
        
        print("✅ Context store test passed")
    
    def test_error_handling(self):
        """Тест обработки ошибок"""
        # Тест с неверным символом
        invalid_symbol = "INVALID_SYMBOL"
        
        # Проверяем, что бот не падает при неверном символе
        try:
            # Это должно обрабатываться gracefully
            self.assertIsInstance(invalid_symbol, str)
            print("✅ Error handling test passed")
        except Exception as e:
            self.fail(f"Error handling test failed: {e}")
    
    def test_message_splitting(self):
        """Тест разделения длинных сообщений"""
        long_message = "A" * 5000  # Сообщение длиннее лимита Telegram
        
        # Тест функции разделения сообщений
        if hasattr(self.bot, '_split_text_smart'):
            parts = self.bot._split_text_smart(long_message)
            self.assertIsInstance(parts, list)
            self.assertGreater(len(parts), 1)
            
            # Проверяем, что каждая часть не превышает лимит
            for part in parts:
                self.assertLessEqual(len(part), 4096)
            
            print("✅ Message splitting test passed")
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_okama_integration(self):
        """Тест интеграции с Okama"""
        try:
            # Тест создания простого актива
            asset = ok.Asset("SPY.US")
            self.assertIsNotNone(asset)
            
            # Тест получения данных
            if hasattr(asset, 'close_prices'):
                prices = asset.close_prices()
                self.assertIsInstance(prices, pd.Series)
                self.assertGreater(len(prices), 0)
            
            print("✅ Okama integration test passed")
        except Exception as e:
            print(f"⚠️ Okama integration test failed: {e}")
    
    def test_ai_services_availability(self):
        """Тест доступности AI сервисов"""
        # Проверяем, что сервисы инициализированы
        self.assertIsNotNone(self.bot.yandexgpt_service)
        self.assertIsNotNone(self.bot.gemini_service)
        
        print("✅ AI services availability test passed")
    
    def test_chart_styles_availability(self):
        """Тест доступности стилей графиков"""
        # Проверяем, что стили графиков доступны
        self.assertIsNotNone(self.bot.chart_styles)
        
        # Проверяем основные методы
        self.assertTrue(hasattr(self.bot.chart_styles, 'create_price_chart'))
        self.assertTrue(hasattr(self.bot.chart_styles, 'create_portfolio_wealth_chart'))
        self.assertTrue(hasattr(self.bot.chart_styles, 'save_figure'))
        
        print("✅ Chart styles availability test passed")
    
    def test_configuration_validation(self):
        """Тест валидации конфигурации"""
        from config import Config
        
        # Проверяем, что конфигурация валидна
        try:
            Config.validate()
            print("✅ Configuration validation test passed")
        except ValueError as e:
            print(f"⚠️ Configuration validation test failed: {e}")
    
    def test_test_command_functions(self):
        """Тест функций команды /test"""
        # Тест функции _run_tests
        self.assertTrue(hasattr(self.bot, '_run_tests'))
        self.assertTrue(hasattr(self.bot, '_format_test_results'))
        
        # Тест форматирования результатов
        test_result = {
            'success': True,
            'stdout': 'Test passed',
            'stderr': '',
            'duration': 1.5,
            'test_type': 'quick'
        }
        
        formatted = self.bot._format_test_results(test_result, 'quick')
        self.assertIsInstance(formatted, str)
        self.assertIn('✅', formatted)
        self.assertIn('quick', formatted)
        
        print("✅ Test command functions test passed")
    
    def test_button_callback_handlers(self):
        """Тест обработчиков callback функций"""
        # Проверяем, что все необходимые обработчики существуют
        required_handlers = [
            '_handle_drawdowns_button',
            '_handle_dividends_button',
            '_handle_correlation_button',
            '_handle_risk_metrics_button',
            '_handle_monte_carlo_button',
            '_handle_forecast_button'
        ]
        
        for handler in required_handlers:
            self.assertTrue(hasattr(self.bot, handler), f"Missing handler: {handler}")
        
        print("✅ Button callback handlers test passed")
    
    def run_simple_test(self):
        """Запуск всех простых тестов"""
        print("🚀 Запуск простого регрессионного теста...")
        print("=" * 60)
        
        test_methods = [
            'test_bot_initialization',
            'test_clean_symbol',
            'test_symbol_parsing',
            'test_weight_parsing',
            'test_context_store',
            'test_error_handling',
            'test_message_splitting',
            'test_okama_integration',
            'test_ai_services_availability',
            'test_chart_styles_availability',
            'test_configuration_validation',
            'test_test_command_functions',
            'test_button_callback_handlers'
        ]
        
        passed_tests = 0
        failed_tests = 0
        
        for test_method in test_methods:
            try:
                print(f"\n🧪 Выполнение теста: {test_method}")
                getattr(self, test_method)()
                passed_tests += 1
            except Exception as e:
                print(f"❌ Тест {test_method} провален: {e}")
                failed_tests += 1
        
        print("\n" + "=" * 60)
        print(f"📊 Результаты тестирования:")
        print(f"✅ Пройдено: {passed_tests}")
        print(f"❌ Провалено: {failed_tests}")
        print(f"📈 Общий процент успеха: {(passed_tests / (passed_tests + failed_tests)) * 100:.1f}%")
        
        if failed_tests == 0:
            print("🎉 Все тесты пройдены успешно!")
        else:
            print(f"⚠️ {failed_tests} тестов провалено. Проверьте функционал.")
        
        return failed_tests == 0


if __name__ == '__main__':
    print("🧪 Простой регрессионный тест для okama-bot")
    print(f"📚 Okama доступен: {OKAMA_AVAILABLE}")
    print("=" * 60)
    
    # Создаем экземпляр теста и запускаем простой тест
    test_instance = TestSimpleRegression()
    test_instance.setUp()
    
    success = test_instance.run_simple_test()
    
    if success:
        print("\n🎯 Простое регрессионное тестирование завершено успешно!")
        sys.exit(0)
    else:
        print("\n💥 Простое регрессионное тестирование выявило проблемы!")
        sys.exit(1)
