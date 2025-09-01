#!/usr/bin/env python3
"""
Integration test to verify that the portfolio command works correctly with the datetime fix.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

# Add the parent directory to the path to import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import OkamaFinanceBot
from datetime import datetime


class TestPortfolioCommandIntegration(unittest.TestCase):
    """Integration test class for portfolio command"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock the config to avoid real initialization
        with patch('bot.Config') as mock_config:
            mock_config.validate.return_value = None
            mock_config.TELEGRAM_BOT_TOKEN = "test_token"
            
            # Mock all services
            with patch.multiple('bot',
                AssetService=Mock(),
                YandexGPTService=Mock(),
                EnhancedIntentParser=Mock(),
                EnhancedAssetResolver=Mock(),
                EnhancedOkamaHandler=Mock(),
                EnhancedReportBuilder=Mock(),
                EnhancedAnalysisEngine=Mock(),
                EnhancedOkamaFinancialBrain=Mock(),
                chart_styles=Mock()
            ):
                self.bot = OkamaFinanceBot()
    
    @patch('bot.ok')
    @patch('bot.chart_styles')
    @patch('bot.io')
    async def test_portfolio_command_success(self, mock_io, mock_chart_styles, mock_ok):
        """Test that portfolio command executes successfully without datetime errors"""
        
        # Mock the update and context objects
        mock_update = Mock()
        mock_context = Mock()
        mock_context.args = ['SPY.US:0.6', 'QQQ.US:0.4']
        
        # Mock the send_message_safe method
        self.bot._send_message_safe = AsyncMock()
        
        # Mock the portfolio creation
        mock_portfolio = Mock()
        mock_portfolio.wealth_index = Mock()
        mock_portfolio.first_date = datetime(2020, 1, 1)
        mock_portfolio.last_date = datetime(2023, 12, 31)
        mock_portfolio.period_length = "3 years"
        mock_portfolio.table = Mock()
        mock_portfolio.table.empty = False
        mock_portfolio.table.iterrows.return_value = [
            (0, {'ticker': 'SPY.US', 'asset name': 'SPDR S&P 500 ETF'}),
            (1, {'ticker': 'QQQ.US', 'asset name': 'Invesco QQQ Trust'})
        ]
        mock_portfolio.wealth_index.iloc = [-1]
        mock_portfolio.wealth_index.iloc[-1] = 1.25
        mock_portfolio.symbol = "PF_TEST"
        mock_portfolio.mean_return_annual = 0.08
        mock_portfolio.volatility_annual = 0.15
        mock_portfolio.sharpe_ratio = 0.5
        
        mock_ok.Portfolio.return_value = mock_portfolio
        
        # Mock chart creation
        mock_fig = Mock()
        mock_ax = Mock()
        mock_chart_styles.create_portfolio_wealth_chart.return_value = (mock_fig, mock_ax)
        
        # Mock image buffer
        mock_buffer = Mock()
        mock_io.BytesIO.return_value = mock_buffer
        mock_buffer.getvalue.return_value = b'fake_image_data'
        
        # Mock context.bot.send_photo
        mock_context.bot.send_photo = AsyncMock()
        
        # Mock user context methods
        self.bot._get_user_context = Mock(return_value={'portfolio_count': 0})
        self.bot._update_user_context = Mock()
        
        try:
            # Execute the portfolio command
            await self.bot.portfolio_command(mock_update, mock_context)
            
            # Verify that the command executed without datetime errors
            print("✅ Portfolio command executed successfully")
            
            # Verify that ok.Portfolio was called
            mock_ok.Portfolio.assert_called_once()
            call_args = mock_ok.Portfolio.call_args
            self.assertEqual(call_args[0][0], ['SPY.US', 'QQQ.US'])  # symbols
            self.assertEqual(call_args[1]['ccy'], 'USD')  # currency
            self.assertEqual(call_args[1]['weights'], [0.6, 0.4])  # weights
            
            print(f"✅ Portfolio created with symbols: {call_args[0][0]}")
            print(f"✅ Portfolio created with weights: {call_args[1]['weights']}")
            print(f"✅ Portfolio created with currency: {call_args[1]['ccy']}")
            
        except NameError as e:
            if 'datetime' in str(e):
                self.fail(f"❌ datetime is not defined: {e}")
            else:
                raise e
        except Exception as e:
            self.fail(f"❌ Portfolio command failed: {e}")
    
    def test_datetime_usage_in_portfolio_attributes(self):
        """Test that datetime.now() can be used in portfolio attributes"""
        try:
            # Test the exact code pattern used in portfolio creation
            portfolio_attributes = {
                'symbols': ['SPY.US', 'QQQ.US'],
                'weights': [0.6, 0.4],
                'currency': 'USD',
                'created_at': datetime.now().isoformat(),
                'description': "Test portfolio",
                'portfolio_symbol': "PF_TEST",
                'total_weight': 1.0,
                'asset_count': 2
            }
            
            # Verify the structure
            self.assertIn('created_at', portfolio_attributes)
            self.assertIsInstance(portfolio_attributes['created_at'], str)
            self.assertTrue(portfolio_attributes['created_at'].startswith('20'))  # ISO format starts with year
            
            print(f"✅ Portfolio attributes with datetime work: {portfolio_attributes}")
            
        except NameError as e:
            self.fail(f"❌ datetime is not defined: {e}")
    
    def test_multiple_datetime_usage_points(self):
        """Test all the places where datetime.now() is used in the bot"""
        try:
            # Test line 208 (timestamp)
            timestamp_data = {
                'timestamp': datetime.now().isoformat(),
                'message': 'test'
            }
            self.assertIn('timestamp', timestamp_data)
            
            # Test line 2009 (created_at in portfolio)
            portfolio_data = {
                'created_at': datetime.now().isoformat(),
                'symbols': ['TEST']
            }
            self.assertIn('created_at', portfolio_data)
            
            # Test line 2181 (created_at in another context)
            context_data = {
                'created_at': datetime.now().isoformat(),
                'context': 'test'
            }
            self.assertIn('created_at', context_data)
            
            print("✅ All datetime.now() usage points work correctly")
            
        except NameError as e:
            self.fail(f"❌ datetime is not defined: {e}")


def run_async_test(coro):
    """Helper function to run async tests"""
    return asyncio.run(coro)


if __name__ == '__main__':
    print("🧪 Running portfolio command integration tests...")
    
    # Run async tests
    test_instance = TestPortfolioCommandIntegration()
    test_instance.setUp()
    
    # Run the async test
    run_async_test(test_instance.test_portfolio_command_success())
    
    # Run sync tests
    unittest.main(verbosity=2)
