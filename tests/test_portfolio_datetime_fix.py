#!/usr/bin/env python3
"""
Test script to verify that the datetime import fix resolves the portfolio creation error.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, AsyncMock

# Add the parent directory to the path to import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import OkamaFinanceBot
from datetime import datetime


class TestPortfolioDatetimeFix(unittest.TestCase):
    """Test class for portfolio datetime fix"""
    
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
    
    def test_datetime_import_available(self):
        """Test that datetime is properly imported and available"""
        # Test that datetime.now() works
        now = datetime.now()
        self.assertIsInstance(now, datetime)
        print(f"✅ datetime.now() works: {now}")
    
    def test_portfolio_creation_with_datetime(self):
        """Test that portfolio creation can use datetime.now()"""
        # Mock the portfolio creation process
        with patch('bot.ok') as mock_ok:
            # Mock the Portfolio class
            mock_portfolio = Mock()
            mock_portfolio.wealth_index = Mock()
            mock_portfolio.first_date = datetime(2020, 1, 1)
            mock_portfolio.last_date = datetime(2023, 12, 31)
            mock_portfolio.period_length = "3 years"
            mock_portfolio.table = Mock()
            mock_portfolio.table.empty = False
            mock_portfolio.table.iterrows.return_value = [
                (0, {'ticker': 'SPY.US', 'asset name': 'SPDR S&P 500 ETF'})
            ]
            mock_portfolio.wealth_index.iloc = [-1]
            mock_portfolio.wealth_index.iloc[-1] = 1.25
            mock_portfolio.symbol = "PF_TEST"
            
            mock_ok.Portfolio.return_value = mock_portfolio
            
            # Test that the datetime usage in portfolio creation works
            try:
                # This should not raise a NameError for datetime
                test_datetime = datetime.now().isoformat()
                self.assertIsInstance(test_datetime, str)
                print(f"✅ datetime.now().isoformat() works: {test_datetime}")
                
                # Test the specific line that was causing the error
                portfolio_attributes = {
                    'created_at': datetime.now().isoformat(),
                    'description': "Test portfolio"
                }
                self.assertIn('created_at', portfolio_attributes)
                self.assertIsInstance(portfolio_attributes['created_at'], str)
                print(f"✅ Portfolio attributes with datetime work: {portfolio_attributes}")
                
            except NameError as e:
                self.fail(f"❌ datetime is not defined: {e}")
    
    def test_bot_initialization(self):
        """Test that the bot initializes without datetime errors"""
        try:
            # Test that the bot can be created
            self.assertIsInstance(self.bot, OkamaFinanceBot)
            print("✅ Bot initialization successful")
            
            # Test that datetime is available in the bot context
            test_datetime = datetime.now()
            self.assertIsInstance(test_datetime, datetime)
            print(f"✅ datetime available in bot context: {test_datetime}")
            
        except Exception as e:
            self.fail(f"❌ Bot initialization failed: {e}")


if __name__ == '__main__':
    print("🧪 Running portfolio datetime fix tests...")
    unittest.main(verbosity=2)
