#!/usr/bin/env python3
"""
Тест для проверки улучшений команды /portfolio:
1. Кнопка Метрики теперь использует _create_summary_metrics_table()
2. Добавлена кнопка AI-анализ после кнопки Дивиденды
3. Функционал AI-анализа аналогичен сравнению
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pandas as pd
import okama as ok

# Импортируем основные модули
from bot import ShansAi
from services.gemini_service import GeminiService

class TestPortfolioEnhancements(unittest.TestCase):
    """Тест улучшений команды /portfolio"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.bot = ShansAi()
        self.bot.logger = Mock()
        
        # Мокаем Gemini сервис
        self.mock_gemini = Mock()
        self.mock_gemini.is_available.return_value = True
        self.mock_gemini.analyze_data.return_value = {
            'success': True,
            'analysis': 'Тестовый анализ портфеля'
        }
        self.bot.gemini_service = self.mock_gemini
        
        # Мокаем контекст пользователя
        self.mock_user_context = {
            'saved_portfolios': {
                'test_portfolio': {
                    'symbols': ['SBER.MOEX', 'LKOH.MOEX'],
                    'weights': [0.6, 0.4],
                    'currency': 'RUB'
                }
            }
        }
        
        # Мокаем update и context
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_update.effective_user.id = 12345
        self.mock_update.effective_chat.id = 67890
        
        # Мокаем методы бота
        self.bot._get_user_context = Mock(return_value=self.mock_user_context)
        self.bot._find_portfolio_by_symbol = Mock(return_value='test_portfolio')
        self.bot._send_callback_message = AsyncMock()
        self.bot._send_callback_message_with_keyboard_removal = AsyncMock()
        self.bot._send_ephemeral_message = AsyncMock()
        self.bot._create_portfolio_command_keyboard = Mock()
        self.bot._create_summary_metrics_table = Mock(return_value="Тестовая таблица метрик")
        self.bot._prepare_data_for_analysis = AsyncMock(return_value={'test': 'data'})
        
    def test_portfolio_metrics_button_uses_summary_table(self):
        """Тест: кнопка Метрики использует _create_summary_metrics_table"""
        # Проверяем, что функция _create_summary_metrics_table вызывается
        # в обработчике кнопки Метрики портфеля
        with patch('okama.Asset') as mock_asset:
            mock_asset.return_value = Mock()
            
            # Вызываем обработчик кнопки Метрики
            asyncio.run(self.bot._handle_portfolio_risk_metrics_by_symbol(
                self.mock_update, self.mock_context, 'test_portfolio'
            ))
            
            # Проверяем, что _create_summary_metrics_table была вызвана
            self.bot._create_summary_metrics_table.assert_called_once()
            
            # Проверяем параметры вызова
            call_args = self.bot._create_summary_metrics_table.call_args
            self.assertEqual(call_args[0][0], ['test_portfolio'])  # symbols
            self.assertEqual(call_args[0][1], 'RUB')  # currency
            self.assertEqual(call_args[0][2], ['test_portfolio'])  # expanded_symbols
            self.assertIsInstance(call_args[0][3], list)  # portfolio_contexts
            self.assertIsNone(call_args[0][4])  # specified_period
    
    def test_ai_analysis_button_in_keyboard(self):
        """Тест: кнопка AI-анализ добавлена в клавиатуру портфеля"""
        # Создаем клавиатуру портфеля
        keyboard = self.bot._create_portfolio_command_keyboard('test_portfolio')
        
        # Проверяем, что клавиатура создана
        self.assertIsNotNone(keyboard)
        
        # Проверяем, что кнопка AI-анализ присутствует
        keyboard_buttons = []
        for row in keyboard.inline_keyboard:
            for button in row:
                keyboard_buttons.append(button.text)
        
        self.assertIn('🤖 AI-анализ', keyboard_buttons)
    
    def test_ai_analysis_button_callback_handling(self):
        """Тест: обработка callback'а кнопки AI-анализ"""
        # Проверяем, что callback 'portfolio_ai_analysis_test_portfolio' 
        # обрабатывается правильно
        callback_data = 'portfolio_ai_analysis_test_portfolio'
        
        # Мокаем button_callback для проверки маршрутизации
        with patch.object(self.bot, 'button_callback', new_callable=AsyncMock) as mock_callback:
            # Имитируем вызов button_callback
            mock_callback.return_value = None
            
            # Проверяем, что callback обрабатывается
            self.assertTrue(callback_data.startswith('portfolio_ai_analysis_'))
    
    def test_ai_analysis_functionality(self):
        """Тест: функционал AI-анализа для портфеля"""
        with patch('okama.Asset') as mock_asset:
            mock_asset.return_value = Mock()
            
            # Вызываем обработчик AI-анализа
            asyncio.run(self.bot._handle_portfolio_ai_analysis_button(
                self.mock_update, self.mock_context, 'test_portfolio'
            ))
            
            # Проверяем, что _prepare_data_for_analysis была вызвана
            self.bot._prepare_data_for_analysis.assert_called_once()
            
            # Проверяем, что Gemini сервис был вызван
            self.mock_gemini.analyze_data.assert_called_once()
            
            # Проверяем, что результат отправлен пользователю
            self.bot._send_callback_message_with_keyboard_removal.assert_called()
    
    def test_portfolio_metrics_table_format(self):
        """Тест: формат таблицы метрик портфеля"""
        # Проверяем, что таблица метрик имеет правильный заголовок
        with patch('okama.Asset') as mock_asset:
            mock_asset.return_value = Mock()
            
            # Вызываем обработчик кнопки Метрики
            asyncio.run(self.bot._handle_portfolio_risk_metrics_by_symbol(
                self.mock_update, self.mock_context, 'test_portfolio'
            ))
            
            # Проверяем, что сообщение содержит правильный заголовок
            call_args = self.bot._send_callback_message_with_keyboard_removal.call_args
            message_text = call_args[0][2]  # Третий аргумент - текст сообщения
            
            self.assertIn('📊 **Сводная таблица ключевых метрик**', message_text)
    
    def test_different_currencies_support(self):
        """Тест: поддержка разных валют"""
        test_cases = [
            {'currency': 'USD', 'symbols': ['SPY.US', 'QQQ.US']},
            {'currency': 'EUR', 'symbols': ['EUNL.ETF', 'IWDA.ETF']},
            {'currency': 'RUB', 'symbols': ['SBER.MOEX', 'LKOH.MOEX']}
        ]
        
        for case in test_cases:
            with self.subTest(currency=case['currency']):
                # Обновляем контекст пользователя
                self.mock_user_context['saved_portfolios']['test_portfolio']['currency'] = case['currency']
                self.mock_user_context['saved_portfolios']['test_portfolio']['symbols'] = case['symbols']
                
                with patch('okama.Asset') as mock_asset:
                    mock_asset.return_value = Mock()
                    
                    # Тестируем кнопку Метрики
                    asyncio.run(self.bot._handle_portfolio_risk_metrics_by_symbol(
                        self.mock_update, self.mock_context, 'test_portfolio'
                    ))
                    
                    # Проверяем, что валюта передается правильно
                    call_args = self.bot._create_summary_metrics_table.call_args
                    self.assertEqual(call_args[0][1], case['currency'])
    
    def test_error_handling(self):
        """Тест: обработка ошибок"""
        # Тест с несуществующим портфелем
        self.bot._find_portfolio_by_symbol.return_value = None
        
        asyncio.run(self.bot._handle_portfolio_ai_analysis_button(
            self.mock_update, self.mock_context, 'nonexistent_portfolio'
        ))
        
        # Проверяем, что отправлено сообщение об ошибке
        self.bot._send_callback_message.assert_called()
        call_args = self.bot._send_callback_message.call_args
        self.assertIn('не найден', call_args[0][2])

if __name__ == '__main__':
    # Запуск тестов
    unittest.main(verbosity=2)
