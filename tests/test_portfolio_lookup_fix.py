"""
Test file for the portfolio lookup fix.
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the parent directory to the path so we can import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestPortfolioLookupFix(unittest.TestCase):
    """Test the portfolio lookup fix functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.bot = ShansAi()
        
        # Mock saved portfolios with different key formats
        self.mock_saved_portfolios = {
            'MSFT.US,BND.US,GC.COMM': {
                'symbols': ['MSFT.US', 'BND.US', 'GC.COMM'],
                'weights': [0.6, 0.3, 0.1],
                'currency': 'USD',
                'created_at': '2025-09-13T10:00:00',
                'description': 'Портфель: MSFT.US, BND.US, GC.COMM'
            },
            'SPY.US,QQQ.US': {
                'symbols': ['SPY.US', 'QQQ.US'],
                'weights': [0.7, 0.3],
                'currency': 'USD',
                'created_at': '2025-09-13T11:00:00',
                'description': 'Портфель: SPY.US, QQQ.US'
            },
            'Портфель TSLA + AAPL': {
                'symbols': ['TSLA.US', 'AAPL.US'],
                'weights': [0.5, 0.5],
                'currency': 'USD',
                'created_at': '2025-09-13T12:00:00',
                'description': 'Портфель: TSLA.US, AAPL.US'
            }
        }
    
    def test_exact_match_found(self):
        """Test exact portfolio symbol match."""
        portfolio_symbol = 'MSFT.US,BND.US,GC.COMM'
        result = self.bot._find_portfolio_by_symbol(
            portfolio_symbol, 
            self.mock_saved_portfolios,
            user_id=123
        )
        
        self.assertEqual(result, 'MSFT.US,BND.US,GC.COMM')
    
    def test_assets_match_different_order(self):
        """Test portfolio found by assets match with different order."""
        # Request with different order
        portfolio_symbol = 'BND.US,GC.COMM,MSFT.US'
        result = self.bot._find_portfolio_by_symbol(
            portfolio_symbol, 
            self.mock_saved_portfolios,
            user_id=123
        )
        
        self.assertEqual(result, 'MSFT.US,BND.US,GC.COMM')
    
    def test_case_insensitive_match(self):
        """Test case-insensitive portfolio matching."""
        portfolio_symbol = 'msft.us,bnd.us,gc.comm'
        result = self.bot._find_portfolio_by_symbol(
            portfolio_symbol, 
            self.mock_saved_portfolios,
            user_id=123
        )
        
        self.assertEqual(result, 'MSFT.US,BND.US,GC.COMM')
    
    def test_portfolio_not_found(self):
        """Test portfolio not found scenario."""
        portfolio_symbol = 'NONEXISTENT.US,FAKE.US'
        result = self.bot._find_portfolio_by_symbol(
            portfolio_symbol, 
            self.mock_saved_portfolios,
            user_id=123
        )
        
        self.assertIsNone(result)
    
    def test_named_portfolio_exact_match(self):
        """Test named portfolio exact match."""
        portfolio_symbol = 'Портфель TSLA + AAPL'
        result = self.bot._find_portfolio_by_symbol(
            portfolio_symbol, 
            self.mock_saved_portfolios,
            user_id=123
        )
        
        self.assertEqual(result, 'Портфель TSLA + AAPL')
    
    def test_assets_match_for_named_portfolio(self):
        """Test finding named portfolio by assets."""
        # Request by asset symbols instead of name
        portfolio_symbol = 'TSLA.US,AAPL.US'
        result = self.bot._find_portfolio_by_symbol(
            portfolio_symbol, 
            self.mock_saved_portfolios,
            user_id=123
        )
        
        self.assertEqual(result, 'Портфель TSLA + AAPL')
    
    def test_empty_portfolios_dict(self):
        """Test behavior with empty portfolios dictionary."""
        result = self.bot._find_portfolio_by_symbol(
            'MSFT.US,BND.US', 
            {},
            user_id=123
        )
        
        self.assertIsNone(result)
    
    def test_malformed_portfolio_symbol(self):
        """Test behavior with malformed portfolio symbol."""
        result = self.bot._find_portfolio_by_symbol(
            '', 
            self.mock_saved_portfolios,
            user_id=123
        )
        
        self.assertIsNone(result)


class TestPortfolioHandlerIntegration(unittest.TestCase):
    """Test integration of portfolio lookup fix with actual handlers."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.bot = ShansAi()
        
        # Mock the necessary methods
        self.bot._get_user_context = Mock()
        self.bot._send_callback_message = AsyncMock()
        self.bot._create_portfolio_wealth_chart = AsyncMock()
        self.bot.logger = Mock()
        
        # Mock update and context
        self.mock_update = Mock()
        self.mock_update.effective_user.id = 123
        self.mock_context = Mock()
        
        # Mock saved portfolios
        self.mock_saved_portfolios = {
            'MSFT.US,BND.US,GC.COMM': {
                'symbols': ['MSFT.US', 'BND.US', 'GC.COMM'],
                'weights': [0.6, 0.3, 0.1],
                'currency': 'USD'
            }
        }
        
        self.bot._get_user_context.return_value = {
            'saved_portfolios': self.mock_saved_portfolios
        }
    
    @patch('bot.ok')  # Mock okama
    async def test_wealth_chart_handler_with_fix(self, mock_okama):
        """Test wealth chart handler with portfolio lookup fix."""
        
        # Request portfolio in different order
        portfolio_symbol = 'BND.US,GC.COMM,MSFT.US'
        
        await self.bot._handle_portfolio_wealth_chart_by_symbol(
            self.mock_update, 
            self.mock_context, 
            portfolio_symbol
        )
        
        # Verify that the wealth chart creation was called (portfolio was found)
        self.bot._create_portfolio_wealth_chart.assert_called_once()
        
        # Verify that no error message was sent
        self.bot._send_callback_message.assert_not_called()
    
    async def test_wealth_chart_handler_portfolio_not_found(self):
        """Test wealth chart handler when portfolio is not found."""
        
        # Request non-existent portfolio
        portfolio_symbol = 'NONEXISTENT.US,FAKE.US'
        
        await self.bot._handle_portfolio_wealth_chart_by_symbol(
            self.mock_update, 
            self.mock_context, 
            portfolio_symbol
        )
        
        # Verify that error message was sent
        self.bot._send_callback_message.assert_called_once()
        error_call_args = self.bot._send_callback_message.call_args[0]
        self.assertIn("не найден", error_call_args[2])
        
        # Verify that wealth chart creation was not called
        self.bot._create_portfolio_wealth_chart.assert_not_called()


if __name__ == '__main__':
    unittest.main()
