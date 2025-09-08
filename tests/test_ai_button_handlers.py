#!/usr/bin/env python3
"""
Test for AI button handlers - check what happens when AI analysis buttons are clicked
"""

import unittest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# Add the parent directory to the path to import bot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
import okama as ok

class TestAIButtonHandlers(unittest.TestCase):
    """Test cases for AI button handlers"""
    
    def setUp(self):
        """Set up test environment"""
        self.bot = ShansAi()
        
    def test_gemini_analysis_button_handler(self):
        """Test Gemini analysis button handler"""
        print(f"\n=== Testing Gemini Analysis Button Handler ===")
        
        # Create mock update and context
        mock_update = Mock()
        mock_context = Mock()
        
        # Mock callback query
        mock_callback_query = Mock()
        mock_callback_query.message.chat_id = 12345
        mock_update.callback_query = mock_callback_query
        
        # Mock user context
        symbols = ['AAPL.US', 'SPY.US']
        currency = 'USD'
        
        # Create expanded symbols
        expanded_symbols = []
        for symbol in symbols:
            try:
                asset = ok.Asset(symbol)
                expanded_symbols.append(asset)
                print(f"✅ Created asset: {symbol}")
            except Exception as e:
                print(f"❌ Failed to create asset {symbol}: {e}")
                return
        
        # Mock user context data
        user_context = {
            'current_symbols': symbols,
            'current_currency': currency,
            'expanded_symbols': expanded_symbols,
            'portfolio_contexts': []
        }
        
        # Mock the _get_user_context method
        with patch.object(self.bot, '_get_user_context', return_value=user_context):
            # Mock the _send_ephemeral_message method
            with patch.object(self.bot, '_send_ephemeral_message', new_callable=AsyncMock) as mock_send_ephemeral:
                # Mock the _prepare_data_for_analysis method
                with patch.object(self.bot, '_prepare_data_for_analysis', new_callable=AsyncMock) as mock_prepare_data:
                    # Mock the gemini service analyze_data method
                    with patch.object(self.bot.gemini_service, 'analyze_data') as mock_analyze:
                        # Mock the _send_callback_message method
                        with patch.object(self.bot, '_send_callback_message', new_callable=AsyncMock) as mock_send_callback:
                            
                            # Set up mock data
                            mock_data_info = {
                                'symbols': symbols,
                                'currency': currency,
                                'asset_names': {'AAPL.US': 'Apple Inc', 'SPY.US': 'SPDR S&P 500 ETF Trust'},
                                'performance': {
                                    'AAPL.US': {
                                        'sharpe_ratio': 0.05,
                                        'sortino_ratio': 0.07,
                                        'annual_return': 0.0444
                                    },
                                    'SPY.US': {
                                        'sharpe_ratio': 0.44,
                                        'sortino_ratio': 0.61,
                                        'annual_return': 0.0856
                                    }
                                }
                            }
                            mock_prepare_data.return_value = mock_data_info
                            
                            # Test successful analysis
                            mock_analysis_result = {
                                'success': True,
                                'analysis': 'Это тестовый анализ с правильными данными: Apple Inc (AAPL.US) имеет коэффициент Шарпа 0.05, SPDR S&P 500 ETF Trust (SPY.US) имеет коэффициент Шарпа 0.44.'
                            }
                            mock_analyze.return_value = mock_analysis_result
                            
                            # Run the handler
                            try:
                                asyncio.run(self.bot._handle_data_analysis_compare_button(mock_update, mock_context))
                                
                                # Check that methods were called
                                print(f"✅ Handler executed successfully")
                                print(f"  - _send_ephemeral_message called: {mock_send_ephemeral.called}")
                                print(f"  - _prepare_data_for_analysis called: {mock_prepare_data.called}")
                                print(f"  - gemini_service.analyze_data called: {mock_analyze.called}")
                                print(f"  - _send_callback_message called: {mock_send_callback.called}")
                                
                                # Check the data that was passed to analyze_data
                                if mock_analyze.called:
                                    call_args = mock_analyze.call_args[0][0]  # First argument (data_info)
                                    print(f"\n📊 Data passed to Gemini analysis:")
                                    print(f"  - Symbols: {call_args.get('symbols', [])}")
                                    print(f"  - Asset names: {call_args.get('asset_names', {})}")
                                    print(f"  - Performance keys: {list(call_args.get('performance', {}).keys())}")
                                    
                                    # Check performance data
                                    for symbol in symbols:
                                        if symbol in call_args.get('performance', {}):
                                            metrics = call_args['performance'][symbol]
                                            print(f"  - {symbol} Sharpe: {metrics.get('sharpe_ratio', 'N/A')}")
                                            print(f"  - {symbol} Sortino: {metrics.get('sortino_ratio', 'N/A')}")
                                
                                # Check the final message
                                if mock_send_callback.called:
                                    final_message = mock_send_callback.call_args[0][2]  # Third argument (text)
                                    print(f"\n📄 Final message sent to user:")
                                    print(f"  - Length: {len(final_message)}")
                                    print(f"  - Contains Apple: {'Apple' in final_message}")
                                    print(f"  - Contains SPDR: {'SPDR' in final_message}")
                                    print(f"  - Contains Sharpe: {'Sharpe' in final_message}")
                                    print(f"  - Contains Sortino: {'Sortino' in final_message}")
                                
                            except Exception as e:
                                print(f"❌ Handler execution error: {e}")
                                import traceback
                                traceback.print_exc()

    def test_yandexgpt_analysis_button_handler(self):
        """Test YandexGPT analysis button handler"""
        print(f"\n=== Testing YandexGPT Analysis Button Handler ===")
        
        # Create mock update and context
        mock_update = Mock()
        mock_context = Mock()
        
        # Mock callback query
        mock_callback_query = Mock()
        mock_callback_query.message.chat_id = 12345
        mock_update.callback_query = mock_callback_query
        
        # Mock user context
        symbols = ['AAPL.US', 'SPY.US']
        currency = 'USD'
        
        # Create expanded symbols
        expanded_symbols = []
        for symbol in symbols:
            try:
                asset = ok.Asset(symbol)
                expanded_symbols.append(asset)
                print(f"✅ Created asset: {symbol}")
            except Exception as e:
                print(f"❌ Failed to create asset {symbol}: {e}")
                return
        
        # Mock user context data
        user_context = {
            'current_symbols': symbols,
            'current_currency': currency,
            'expanded_symbols': expanded_symbols,
            'portfolio_contexts': []
        }
        
        # Mock the _get_user_context method
        with patch.object(self.bot, '_get_user_context', return_value=user_context):
            # Mock the _send_ephemeral_message method
            with patch.object(self.bot, '_send_ephemeral_message', new_callable=AsyncMock) as mock_send_ephemeral:
                # Mock the _prepare_data_for_analysis method
                with patch.object(self.bot, '_prepare_data_for_analysis', new_callable=AsyncMock) as mock_prepare_data:
                    # Mock the yandexgpt service analyze_data method
                    with patch.object(self.bot.yandexgpt_service, 'analyze_data') as mock_analyze:
                        # Mock the _send_callback_message method
                        with patch.object(self.bot, '_send_callback_message', new_callable=AsyncMock) as mock_send_callback:
                            
                            # Set up mock data
                            mock_data_info = {
                                'symbols': symbols,
                                'currency': currency,
                                'asset_names': {'AAPL.US': 'Apple Inc', 'SPY.US': 'SPDR S&P 500 ETF Trust'},
                                'performance': {
                                    'AAPL.US': {
                                        'sharpe_ratio': 0.05,
                                        'sortino_ratio': 0.07,
                                        'annual_return': 0.0444
                                    },
                                    'SPY.US': {
                                        'sharpe_ratio': 0.44,
                                        'sortino_ratio': 0.61,
                                        'annual_return': 0.0856
                                    }
                                }
                            }
                            mock_prepare_data.return_value = mock_data_info
                            
                            # Test successful analysis
                            mock_analysis_result = {
                                'success': True,
                                'analysis': 'Это тестовый анализ YandexGPT с правильными данными: Apple Inc (AAPL.US) имеет коэффициент Шарпа 0.05, SPDR S&P 500 ETF Trust (SPY.US) имеет коэффициент Шарпа 0.44.'
                            }
                            mock_analyze.return_value = mock_analysis_result
                            
                            # Run the handler
                            try:
                                asyncio.run(self.bot._handle_yandexgpt_analysis_compare_button(mock_update, mock_context))
                                
                                # Check that methods were called
                                print(f"✅ Handler executed successfully")
                                print(f"  - _send_ephemeral_message called: {mock_send_ephemeral.called}")
                                print(f"  - _prepare_data_for_analysis called: {mock_prepare_data.called}")
                                print(f"  - yandexgpt_service.analyze_data called: {mock_analyze.called}")
                                print(f"  - _send_callback_message called: {mock_send_callback.called}")
                                
                                # Check the data that was passed to analyze_data
                                if mock_analyze.called:
                                    call_args = mock_analyze.call_args[0][0]  # First argument (data_info)
                                    print(f"\n📊 Data passed to YandexGPT analysis:")
                                    print(f"  - Symbols: {call_args.get('symbols', [])}")
                                    print(f"  - Asset names: {call_args.get('asset_names', {})}")
                                    print(f"  - Performance keys: {list(call_args.get('performance', {}).keys())}")
                                    
                                    # Check performance data
                                    for symbol in symbols:
                                        if symbol in call_args.get('performance', {}):
                                            metrics = call_args['performance'][symbol]
                                            print(f"  - {symbol} Sharpe: {metrics.get('sharpe_ratio', 'N/A')}")
                                            print(f"  - {symbol} Sortino: {metrics.get('sortino_ratio', 'N/A')}")
                                
                                # Check the final message
                                if mock_send_callback.called:
                                    final_message = mock_send_callback.call_args[0][2]  # Third argument (text)
                                    print(f"\n📄 Final message sent to user:")
                                    print(f"  - Length: {len(final_message)}")
                                    print(f"  - Contains Apple: {'Apple' in final_message}")
                                    print(f"  - Contains SPDR: {'SPDR' in final_message}")
                                    print(f"  - Contains Sharpe: {'Sharpe' in final_message}")
                                    print(f"  - Contains Sortino: {'Sortino' in final_message}")
                                
                            except Exception as e:
                                print(f"❌ Handler execution error: {e}")
                                import traceback
                                traceback.print_exc()

if __name__ == '__main__':
    print("Testing AI Button Handlers...")
    unittest.main()
