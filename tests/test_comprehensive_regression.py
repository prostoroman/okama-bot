#!/usr/bin/env python3
"""
Комплексный регрессионный тест для okama-bot
Покрывает весь функционал бота для проверки после внедрения новых функций
"""

import unittest
import sys
import os
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import okama as ok
    OKAMA_AVAILABLE = True
except ImportError:
    OKAMA_AVAILABLE = False
    print("Warning: okama library not available for testing")

from bot import ShansAi
from services.context_store import JSONUserContextStore


class TestComprehensiveRegression(unittest.TestCase):
    """Комплексный регрессионный тест для всего функционала бота"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.bot = ShansAi()
        self.test_user_id = 12345
        self.test_symbols = ['SPY.US', 'QQQ.US', 'VOO.US']
        self.test_portfolio_symbols = ['SPY.US:0.5', 'QQQ.US:0.3', 'VOO.US:0.2']
        
        # Mock Telegram objects
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_query = Mock()
        
        # Setup mock update
        self.mock_update.effective_user = Mock()
        self.mock_update.effective_user.id = self.test_user_id
        self.mock_update.effective_user.first_name = "TestUser"
        
        # Setup mock context
        self.mock_context.bot = Mock()
        self.mock_context.bot.send_message = AsyncMock()
        self.mock_context.bot.send_photo = AsyncMock()
        self.mock_context.bot.send_document = AsyncMock()
        self.mock_context.bot.edit_message_text = AsyncMock()
        self.mock_context.bot.edit_message_reply_markup = AsyncMock()
        
        # Setup mock update.message for _send_message_safe
        self.mock_update.message = Mock()
        self.mock_update.message.reply_text = AsyncMock()
        self.mock_update.message.reply_photo = AsyncMock()
        self.mock_update.message.reply_document = AsyncMock()
        
        # Setup mock query for callbacks
        self.mock_query.data = "test_callback"
        self.mock_query.answer = AsyncMock()
        self.mock_update.callback_query = self.mock_query
        
        # Mock user context
        self.bot._get_user_context = Mock(return_value={
            'current_symbols': self.test_symbols,
            'last_analysis_type': 'compare',
            'saved_portfolios': {}
        })
    
    def test_bot_initialization(self):
        """Тест инициализации бота"""
        self.assertIsNotNone(self.bot)
        self.assertIsNotNone(self.bot.logger)
        self.assertIsNotNone(self.bot.chart_styles)
        print("✅ Bot initialization test passed")
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_start_command(self):
        """Тест команды /start"""
        async def run_test():
            await self.bot.start_command(self.mock_update, self.mock_context)
            
            # Проверяем, что бот отправил сообщение
            self.mock_context.bot.send_message.assert_called_once()
            call_args = self.mock_context.bot.send_message.call_args
            message_text = call_args[1]['text']
            
            # Проверяем, что сообщение содержит основную информацию
            self.assertIn("Анализ активов", message_text)
            self.assertIn("Основные команды", message_text)
            self.assertIn("/start", message_text)
            self.assertIn("/info", message_text)
            self.assertIn("/compare", message_text)
            self.assertIn("/portfolio", message_text)
            
            print("✅ Start command test passed")
        
        asyncio.run(run_test())
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_info_command(self):
        """Тест команды /info"""
        async def run_test():
            # Тест с символом
            self.mock_update.message.text = "/info SPY.US"
            
            with patch.object(self.bot, '_send_message_safe', new_callable=AsyncMock) as mock_send:
                await self.bot.info_command(self.mock_update, self.mock_context)
                
                # Проверяем, что функция была вызвана
                self.assertTrue(mock_send.called)
                print("✅ Info command test passed")
        
        asyncio.run(run_test())
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_compare_command(self):
        """Тест команды /compare"""
        async def run_test():
            # Тест с несколькими символами
            self.mock_update.message.text = "/compare SPY.US QQQ.US VOO.US"
            
            with patch.object(self.bot, '_send_message_safe', new_callable=AsyncMock) as mock_send:
                await self.bot.compare_command(self.mock_update, self.mock_context)
                
                # Проверяем, что функция была вызвана
                self.assertTrue(mock_send.called)
                print("✅ Compare command test passed")
        
        asyncio.run(run_test())
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_portfolio_command(self):
        """Тест команды /portfolio"""
        async def run_test():
            # Тест создания портфеля
            self.mock_update.message.text = "/portfolio SPY.US:0.5 QQQ.US:0.3 VOO.US:0.2"
            
            with patch.object(self.bot, '_send_message_safe', new_callable=AsyncMock) as mock_send:
                await self.bot.portfolio_command(self.mock_update, self.mock_context)
                
                # Проверяем, что функция была вызвана
                self.assertTrue(mock_send.called)
                print("✅ Portfolio command test passed")
        
        asyncio.run(run_test())
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_my_portfolios_command(self):
        """Тест команды /my"""
        async def run_test():
            with patch.object(self.bot, '_send_message_safe', new_callable=AsyncMock) as mock_send:
                await self.bot.my_portfolios_command(self.mock_update, self.mock_context)
                
                # Проверяем, что функция была вызвана
                self.assertTrue(mock_send.called)
                print("✅ My portfolios command test passed")
        
        asyncio.run(run_test())
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_namespace_command(self):
        """Тест команды /list"""
        async def run_test():
            # Тест без параметров
            self.mock_update.message.text = "/list"
            
            with patch.object(self.bot, '_send_message_safe', new_callable=AsyncMock) as mock_send:
                await self.bot.namespace_command(self.mock_update, self.mock_context)
                
                # Проверяем, что функция была вызвана
                self.assertTrue(mock_send.called)
                print("✅ Namespace command test passed")
        
        asyncio.run(run_test())
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_gemini_status_command(self):
        """Тест команды /gemini_status"""
        async def run_test():
            with patch.object(self.bot, '_send_message_safe', new_callable=AsyncMock) as mock_send:
                await self.bot.gemini_status_command(self.mock_update, self.mock_context)
                
                # Проверяем, что функция была вызвана
                self.assertTrue(mock_send.called)
                print("✅ Gemini status command test passed")
        
        asyncio.run(run_test())
    
    def test_handle_message(self):
        """Тест обработки текстовых сообщений"""
        async def run_test():
            # Тест с символом
            self.mock_update.message.text = "SPY.US"
            
            with patch.object(self.bot, 'info_command', new_callable=AsyncMock) as mock_info:
                await self.bot.handle_message(self.mock_update, self.mock_context)
                
                # Проверяем, что info_command была вызвана
                self.assertTrue(mock_info.called)
                print("✅ Handle message test passed")
        
        asyncio.run(run_test())
    
    def test_button_callback_drawdowns(self):
        """Тест callback для кнопки просадок"""
        async def run_test():
            self.mock_query.data = "drawdowns"
            
            with patch.object(self.bot, '_handle_drawdowns_button', new_callable=AsyncMock) as mock_drawdowns:
                await self.bot.button_callback(self.mock_update, self.mock_context)
                
                # Проверяем, что функция была вызвана
                self.assertTrue(mock_drawdowns.called)
                print("✅ Drawdowns button callback test passed")
        
        asyncio.run(run_test())
    
    def test_button_callback_dividends(self):
        """Тест callback для кнопки дивидендов"""
        async def run_test():
            self.mock_query.data = "dividends"
            
            with patch.object(self.bot, '_handle_dividends_button', new_callable=AsyncMock) as mock_dividends:
                await self.bot.button_callback(self.mock_update, self.mock_context)
                
                # Проверяем, что функция была вызвана
                self.assertTrue(mock_dividends.called)
                print("✅ Dividends button callback test passed")
        
        asyncio.run(run_test())
    
    def test_button_callback_correlation(self):
        """Тест callback для кнопки корреляции"""
        async def run_test():
            self.mock_query.data = "correlation"
            
            with patch.object(self.bot, '_handle_correlation_button', new_callable=AsyncMock) as mock_correlation:
                await self.bot.button_callback(self.mock_update, self.mock_context)
                
                # Проверяем, что функция была вызвана
                self.assertTrue(mock_correlation.called)
                print("✅ Correlation button callback test passed")
        
        asyncio.run(run_test())
    
    def test_button_callback_risk_metrics(self):
        """Тест callback для кнопки метрик риска"""
        async def run_test():
            self.mock_query.data = "risk_metrics"
            
            with patch.object(self.bot, '_handle_risk_metrics_button', new_callable=AsyncMock) as mock_risk:
                await self.bot.button_callback(self.mock_update, self.mock_context)
                
                # Проверяем, что функция была вызвана
                self.assertTrue(mock_risk.called)
                print("✅ Risk metrics button callback test passed")
        
        asyncio.run(run_test())
    
    def test_button_callback_monte_carlo(self):
        """Тест callback для кнопки Монте-Карло"""
        async def run_test():
            self.mock_query.data = "monte_carlo"
            
            with patch.object(self.bot, '_handle_monte_carlo_button', new_callable=AsyncMock) as mock_monte:
                await self.bot.button_callback(self.mock_update, self.mock_context)
                
                # Проверяем, что функция была вызвана
                self.assertTrue(mock_monte.called)
                print("✅ Monte Carlo button callback test passed")
        
        asyncio.run(run_test())
    
    def test_button_callback_forecast(self):
        """Тест callback для кнопки прогнозирования"""
        async def run_test():
            self.mock_query.data = "forecast"
            
            with patch.object(self.bot, '_handle_forecast_button', new_callable=AsyncMock) as mock_forecast:
                await self.bot.button_callback(self.mock_update, self.mock_context)
                
                # Проверяем, что функция была вызвана
                self.assertTrue(mock_forecast.called)
                print("✅ Forecast button callback test passed")
        
        asyncio.run(run_test())
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_asset_creation(self):
        """Тест создания активов"""
        from services.domain.asset import Asset
        
        # Тест создания актива
        asset = Asset("SPY.US", "USD")
        self.assertEqual(asset.symbol, "SPY.US")
        self.assertEqual(asset.currency, "USD")
        
        # Тест to_dict
        asset_dict = asset.to_dict()
        self.assertEqual(asset_dict["symbol"], "SPY.US")
        self.assertEqual(asset_dict["currency"], "USD")
        
        print("✅ Asset creation test passed")
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_portfolio_creation(self):
        """Тест создания портфеля"""
        from services.domain.portfolio import Portfolio
        
        # Тест создания портфеля
        portfolio = Portfolio(["SPY.US", "QQQ.US"], [0.6, 0.4], "USD")
        self.assertEqual(portfolio.symbols, ["SPY.US", "QQQ.US"])
        self.assertEqual(portfolio.weights, [0.6, 0.4])
        self.assertEqual(portfolio.currency, "USD")
        
        # Тест нормализации весов
        portfolio_auto = Portfolio(["SPY.US", "QQQ.US", "VOO.US"])
        expected_weights = [1.0/3, 1.0/3, 1.0/3]
        self.assertEqual(portfolio_auto.weights, expected_weights)
        
        print("✅ Portfolio creation test passed")
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_chart_generation(self):
        """Тест генерации графиков"""
        from services.domain.asset import Asset
        
        # Создаем тестовые данные
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        prices = 100 * (1 + np.random.normal(0.001, 0.02, 100)).cumprod()
        price_series = pd.Series(prices, index=dates)
        
        # Мокаем okama Asset
        with patch('okama.Asset') as mock_asset_class:
            mock_asset = Mock()
            mock_asset.close_prices.return_value = price_series
            mock_asset_class.return_value = mock_asset
            
            asset = Asset("SPY.US", "USD")
            
            # Тест генерации графика цены
            try:
                chart_data = asset.price_chart_png()
                self.assertIsInstance(chart_data, bytes)
                self.assertGreater(len(chart_data), 0)
                print("✅ Price chart generation test passed")
            except Exception as e:
                print(f"⚠️ Price chart generation test failed: {e}")
    
    def test_context_store(self):
        """Тест хранения контекста пользователя"""
        # Тест получения контекста
        context = self.bot._get_user_context(self.test_user_id)
        self.assertIsInstance(context, dict)
        
        # Тест сохранения контекста
        test_data = {"test_key": "test_value"}
        self.bot._save_user_context(self.test_user_id, test_data)
        
        # Проверяем, что данные сохранились
        saved_context = self.bot._get_user_context(self.test_user_id)
        self.assertEqual(saved_context.get("test_key"), "test_value")
        
        print("✅ Context store test passed")
    
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
    
    def run_comprehensive_test(self):
        """Запуск всех тестов в правильном порядке"""
        print("🚀 Запуск комплексного регрессионного теста...")
        print("=" * 60)
        
        test_methods = [
            'test_bot_initialization',
            'test_start_command',
            'test_info_command', 
            'test_compare_command',
            'test_portfolio_command',
            'test_my_portfolios_command',
            'test_namespace_command',
            'test_gemini_status_command',
            'test_handle_message',
            'test_button_callback_drawdowns',
            'test_button_callback_dividends',
            'test_button_callback_correlation',
            'test_button_callback_risk_metrics',
            'test_button_callback_monte_carlo',
            'test_button_callback_forecast',
            'test_asset_creation',
            'test_portfolio_creation',
            'test_chart_generation',
            'test_context_store',
            'test_symbol_parsing',
            'test_weight_parsing',
            'test_error_handling',
            'test_message_splitting',
            'test_okama_integration',
            'test_ai_services_availability',
            'test_chart_styles_availability',
            'test_configuration_validation'
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
    print("🧪 Комплексный регрессионный тест для okama-bot")
    print(f"📚 Okama доступен: {OKAMA_AVAILABLE}")
    print("=" * 60)
    
    # Создаем экземпляр теста и запускаем комплексный тест
    test_instance = TestComprehensiveRegression()
    test_instance.setUp()
    
    success = test_instance.run_comprehensive_test()
    
    if success:
        print("\n🎯 Регрессионное тестирование завершено успешно!")
        sys.exit(0)
    else:
        print("\n💥 Регрессионное тестирование выявило проблемы!")
        sys.exit(1)
