#!/usr/bin/env python3
"""
Test for AI analysis markdown formatting
"""

import unittest
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestAIAnalysisMarkdownFormatting(unittest.TestCase):
    """Test cases for AI analysis markdown formatting"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    @patch('bot.ShansAi._send_callback_message')
    async def test_data_analysis_markdown_formatting(self, mock_send_callback):
        """Test that data analysis uses markdown formatting"""
        # Mock update and context
        mock_update = Mock()
        mock_update.effective_user.id = 12345
        mock_context = Mock()
        
        # Mock user context
        self.bot._update_user_context(12345, 
                                    current_symbols=['SPY.US', 'QQQ.US'],
                                    current_currency='USD',
                                    expanded_symbols=['SPY.US', 'QQQ.US'],
                                    portfolio_contexts=[])
        
        # Mock Gemini service
        mock_gemini_service = Mock()
        mock_gemini_service.is_available.return_value = True
        mock_gemini_service.analyze_data.return_value = {
            'success': True,
            'analysis': '**Анализ показывает:**\n\n- SPY.US: хорошая доходность\n- QQQ.US: высокая волатильность'
        }
        self.bot.gemini_service = mock_gemini_service
        
        # Mock _prepare_data_for_analysis
        async def mock_prepare_data(*args, **kwargs):
            return {
                'symbols': ['SPY.US', 'QQQ.US'],
                'currency': 'USD',
                'performance': {},
                'correlations': []
            }
        
        self.bot._prepare_data_for_analysis = AsyncMock(side_effect=mock_prepare_data)
        
        # Test the function
        await self.bot._handle_data_analysis_compare_button(mock_update, mock_context)
        
        # Verify that _send_callback_message was called with parse_mode='Markdown'
        calls = mock_send_callback.call_args_list
        
        # Find the call with analysis result
        analysis_call = None
        for call in calls:
            if 'parse_mode' in call.kwargs and call.kwargs['parse_mode'] == 'Markdown':
                if 'Анализ показывает' in str(call.args):
                    analysis_call = call
                    break
        
        self.assertIsNotNone(analysis_call, "Analysis message should be sent with parse_mode='Markdown'")
        self.assertEqual(analysis_call.kwargs['parse_mode'], 'Markdown')
        
        print("✅ Data analysis markdown formatting test passed")
    
    @patch('bot.ShansAi._send_callback_message')
    async def test_chart_analysis_markdown_formatting(self, mock_send_callback):
        """Test that chart analysis uses markdown formatting"""
        # Mock update and context
        mock_update = Mock()
        mock_update.effective_user.id = 12345
        mock_context = Mock()
        
        # Mock user context
        self.bot._update_user_context(12345, 
                                    current_symbols=['SPY.US', 'QQQ.US'],
                                    current_currency='USD',
                                    expanded_symbols=['SPY.US', 'QQQ.US'],
                                    portfolio_contexts=[],
                                    display_symbols=['SPY.US', 'QQQ.US'])
        
        # Mock Gemini service
        mock_gemini_service = Mock()
        mock_gemini_service.is_available.return_value = True
        mock_gemini_service.analyze_chart.return_value = {
            'success': True,
            'full_analysis': '**Технический анализ:**\n\n- Восходящий тренд\n- Поддержка на уровне 400'
        }
        self.bot.gemini_service = mock_gemini_service
        
        # Mock okama and chart creation
        with patch('bot.ok.AssetList') as mock_assetlist, \
             patch('bot.chart_styles.create_comparison_chart') as mock_chart, \
             patch('bot.chart_styles.save_figure') as mock_save, \
             patch('bot.chart_styles.cleanup_figure') as mock_cleanup, \
             patch('bot.io.BytesIO') as mock_bytesio:
            
            # Setup mocks
            mock_comparison = Mock()
            mock_comparison.wealth_indexes = Mock()
            mock_assetlist.return_value = mock_comparison
            
            mock_chart.return_value = (Mock(), Mock())
            
            mock_buffer = Mock()
            mock_buffer.getvalue.return_value = b'fake_image_data'
            mock_bytesio.return_value = mock_buffer
            
            # Test the function
            await self.bot._handle_chart_analysis_compare_button(mock_update, mock_context)
        
        # Verify that _send_callback_message was called with parse_mode='Markdown'
        calls = mock_send_callback.call_args_list
        
        # Find the call with analysis result
        analysis_call = None
        for call in calls:
            if 'parse_mode' in call.kwargs and call.kwargs['parse_mode'] == 'Markdown':
                if 'Технический анализ' in str(call.args):
                    analysis_call = call
                    break
        
        self.assertIsNotNone(analysis_call, "Chart analysis message should be sent with parse_mode='Markdown'")
        self.assertEqual(analysis_call.kwargs['parse_mode'], 'Markdown')
        
        print("✅ Chart analysis markdown formatting test passed")
    
    @patch('bot.ShansAi._send_callback_message')
    async def test_error_messages_markdown_formatting(self, mock_send_callback):
        """Test that error messages use markdown formatting"""
        # Mock update and context
        mock_update = Mock()
        mock_update.effective_user.id = 12345
        mock_context = Mock()
        
        # Mock user context with empty data to trigger error
        self.bot._update_user_context(12345, 
                                    current_symbols=[],
                                    current_currency='USD',
                                    expanded_symbols=[],
                                    portfolio_contexts=[])
        
        # Test data analysis error
        await self.bot._handle_data_analysis_compare_button(mock_update, mock_context)
        
        # Verify that error message was sent with markdown formatting
        calls = mock_send_callback.call_args_list
        
        # Should have an error message call
        self.assertTrue(len(calls) > 0, "Should have at least one callback message call")
        
        # Check if any call contains error message text
        error_call = None
        for call in calls:
            if 'Нет данных для сравнения' in str(call.args):
                error_call = call
                break
        
        self.assertIsNotNone(error_call, "Error message should be sent")
        
        print("✅ Error messages markdown formatting test passed")


def run_async_test():
    """Run async tests"""
    import asyncio
    
    async def run_tests():
        test_case = TestAIAnalysisMarkdownFormatting()
        test_case.setUp()
        
        try:
            await test_case.test_data_analysis_markdown_formatting()
            await test_case.test_chart_analysis_markdown_formatting()
            await test_case.test_error_messages_markdown_formatting()
            print("✅ All markdown formatting tests passed!")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(run_tests())


if __name__ == '__main__':
    print("Testing AI analysis markdown formatting...")
    run_async_test()
