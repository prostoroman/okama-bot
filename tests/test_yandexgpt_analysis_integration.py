#!/usr/bin/env python3
"""
Test for YandexGPT analysis integration
"""

import unittest
import sys
import os
from unittest.mock import Mock, AsyncMock, patch
import asyncio

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestYandexGPTAnalysisIntegration(unittest.TestCase):
    """Test cases for YandexGPT analysis integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    def test_yandexgpt_service_initialization(self):
        """Test that YandexGPT service is properly initialized"""
        self.assertIsNotNone(self.bot.yandexgpt_service)
        self.assertTrue(hasattr(self.bot.yandexgpt_service, 'analyze_data'))
        self.assertTrue(hasattr(self.bot.yandexgpt_service, 'analyze_chart'))
        self.assertTrue(hasattr(self.bot.yandexgpt_service, 'is_available'))
        print("✅ YandexGPT service initialization test passed")
    
    def test_yandexgpt_analyze_data_method(self):
        """Test YandexGPT analyze_data method"""
        # Mock data info
        data_info = {
            'symbols': ['SPY.US', 'QQQ.US'],
            'currency': 'USD',
            'period': 'полный доступный период данных',
            'performance': {
                'SPY.US': {
                    'total_return': 0.15,
                    'annual_return': 0.08,
                    'volatility': 0.12,
                    'sharpe_ratio': 0.5,
                    'sortino_ratio': 0.7,
                    'max_drawdown': -0.2
                },
                'QQQ.US': {
                    'total_return': 0.20,
                    'annual_return': 0.10,
                    'volatility': 0.18,
                    'sharpe_ratio': 0.44,
                    'sortino_ratio': 0.56,
                    'max_drawdown': -0.25
                }
            },
            'correlations': [[1.0, 0.8], [0.8, 1.0]],
            'describe_table': 'Detailed statistics table',
            'additional_info': 'Additional analysis info'
        }
        
        # Test the method
        result = self.bot.yandexgpt_service.analyze_data(data_info)
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('analysis', result)
        self.assertIn('analysis_type', result)
        
        print("✅ YandexGPT analyze_data method test passed")
    
    def test_yandexgpt_prepare_data_description(self):
        """Test YandexGPT _prepare_data_description method"""
        # Mock data info
        data_info = {
            'symbols': ['SPY.US', 'QQQ.US'],
            'currency': 'USD',
            'period': 'полный доступный период данных',
            'performance': {
                'SPY.US': {
                    'total_return': 0.15,
                    'annual_return': 0.08,
                    'volatility': 0.12,
                    'sharpe_ratio': 0.5,
                    'sortino_ratio': 0.7,
                    'max_drawdown': -0.2
                }
            },
            'correlations': [[1.0, 0.8], [0.8, 1.0]],
            'describe_table': 'Detailed statistics table',
            'additional_info': 'Additional analysis info'
        }
        
        # Test the method
        description = self.bot.yandexgpt_service._prepare_data_description(data_info)
        
        # Verify description content
        self.assertIsInstance(description, str)
        self.assertIn('SPY.US', description)
        self.assertIn('QQQ.US', description)
        self.assertIn('USD', description)
        self.assertIn('МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ', description)
        self.assertIn('КОРРЕЛЯЦИОННАЯ МАТРИЦА', description)
        
        print("✅ YandexGPT _prepare_data_description method test passed")
    
    def test_yandexgpt_is_available_method(self):
        """Test YandexGPT is_available method"""
        # Test the method
        is_available = self.bot.yandexgpt_service.is_available()
        
        # Verify result
        self.assertIsInstance(is_available, bool)
        
        print(f"✅ YandexGPT is_available method test passed (available: {is_available})")
    
    @patch('bot.ShansAi._send_callback_message')
    @patch('bot.ShansAi._prepare_data_for_analysis')
    def test_handle_yandexgpt_analysis_compare_button(self, mock_prepare_data, mock_send_callback):
        """Test _handle_yandexgpt_analysis_compare_button function"""
        # Mock data
        mock_prepare_data.return_value = {
            'symbols': ['SPY.US', 'QQQ.US'],
            'currency': 'USD',
            'performance': {
                'SPY.US': {'annual_return': 0.08, 'volatility': 0.12},
                'QQQ.US': {'annual_return': 0.10, 'volatility': 0.18}
            }
        }
        
        # Mock YandexGPT service
        mock_yandexgpt_service = Mock()
        mock_yandexgpt_service.is_available.return_value = True
        mock_yandexgpt_service.analyze_data.return_value = {
            'success': True,
            'analysis': 'YandexGPT analysis result',
            'analysis_type': 'data'
        }
        self.bot.yandexgpt_service = mock_yandexgpt_service
        
        # Mock update and context
        mock_update = Mock()
        mock_update.effective_user.id = 12345
        mock_context = Mock()
        
        # Mock user context
        with patch.object(self.bot, '_get_user_context') as mock_get_context:
            mock_get_context.return_value = {
                'current_symbols': ['SPY.US', 'QQQ.US'],
                'current_currency': 'USD',
                'expanded_symbols': [Mock(), Mock()],
                'portfolio_contexts': []
            }
            
            # Test the function
            asyncio.run(self.bot._handle_yandexgpt_analysis_compare_button(mock_update, mock_context))
        
        # Verify calls
        mock_prepare_data.assert_called_once()
        mock_yandexgpt_service.analyze_data.assert_called_once()
        mock_send_callback.assert_called()
        
        # Verify that the analysis result was sent with markdown formatting
        calls = mock_send_callback.call_args_list
        analysis_call = None
        for call in calls:
            if len(call[0]) >= 3 and call[0][2] == 'Markdown':
                analysis_call = call
                break
        
        self.assertIsNotNone(analysis_call, "Analysis result should be sent with Markdown formatting")
        
        print("✅ _handle_yandexgpt_analysis_compare_button test passed")
    
    @patch('bot.ShansAi._send_callback_message')
    def test_handle_yandexgpt_analysis_no_data(self, mock_send_callback):
        """Test _handle_yandexgpt_analysis_compare_button with no data"""
        # Mock update and context
        mock_update = Mock()
        mock_update.effective_user.id = 12345
        mock_context = Mock()
        
        # Mock user context with no expanded_symbols
        with patch.object(self.bot, '_get_user_context') as mock_get_context:
            mock_get_context.return_value = {
                'current_symbols': ['SPY.US', 'QQQ.US'],
                'current_currency': 'USD',
                'expanded_symbols': [],  # No data
                'portfolio_contexts': []
            }
            
            # Test the function
            asyncio.run(self.bot._handle_yandexgpt_analysis_compare_button(mock_update, mock_context))
        
        # Verify error message was sent
        mock_send_callback.assert_called()
        calls = mock_send_callback.call_args_list
        error_call = calls[0]
        self.assertIn("Нет данных для сравнения", error_call[0][2])
        
        print("✅ _handle_yandexgpt_analysis_compare_button no data test passed")
    
    @patch('bot.ShansAi._send_callback_message')
    def test_handle_yandexgpt_analysis_service_unavailable(self, mock_send_callback):
        """Test _handle_yandexgpt_analysis_compare_button with unavailable service"""
        # Mock YandexGPT service as unavailable
        mock_yandexgpt_service = Mock()
        mock_yandexgpt_service.is_available.return_value = False
        self.bot.yandexgpt_service = mock_yandexgpt_service
        
        # Mock update and context
        mock_update = Mock()
        mock_update.effective_user.id = 12345
        mock_context = Mock()
        
        # Mock user context
        with patch.object(self.bot, '_get_user_context') as mock_get_context:
            mock_get_context.return_value = {
                'current_symbols': ['SPY.US', 'QQQ.US'],
                'current_currency': 'USD',
                'expanded_symbols': [Mock(), Mock()],
                'portfolio_contexts': []
            }
            
            # Test the function
            asyncio.run(self.bot._handle_yandexgpt_analysis_compare_button(mock_update, mock_context))
        
        # Verify error message was sent
        mock_send_callback.assert_called()
        calls = mock_send_callback.call_args_list
        error_call = calls[0]
        self.assertIn("YandexGPT недоступен", error_call[0][2])
        
        print("✅ _handle_yandexgpt_analysis_compare_button service unavailable test passed")


if __name__ == '__main__':
    print("Testing YandexGPT analysis integration...")
    
    unittest.main(verbosity=2)
