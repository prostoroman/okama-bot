#!/usr/bin/env python3
"""
Test for portfolio index out of range fix
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path to import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestPortfolioIndexFix(unittest.TestCase):
    """Test cases for portfolio index out of range fix"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
        
    def test_prepare_comprehensive_metrics_empty_portfolio_symbols(self):
        """Test that _prepare_comprehensive_metrics handles empty portfolio_symbols correctly"""
        # Test data with empty portfolio_symbols
        symbols = ['AAPL.US']
        currency = 'USD'
        expanded_symbols = ['AAPL.US']
        portfolio_contexts = [
            {
                'portfolio_symbols': [],  # Empty list that would cause index error
                'portfolio_weights': [],
                'symbol': 'AAPL.US'
            }
        ]
        user_id = 12345
        
        # Mock the _get_user_context method
        with patch.object(self.bot, '_get_user_context', return_value={'describe_table': ''}):
            # Mock ok.Asset to avoid actual API calls
            with patch('okama.Asset') as mock_asset:
                mock_asset_instance = Mock()
                mock_asset.return_value = mock_asset_instance
                
                # This should not raise an IndexError
                result = self.bot._prepare_comprehensive_metrics(
                    symbols, currency, expanded_symbols, portfolio_contexts, user_id
                )
                
                # Verify the result structure
                self.assertIsInstance(result, dict)
                self.assertIn('symbols', result)
                self.assertIn('currency', result)
                self.assertIn('performance', result)
                
                # Verify that ok.Asset was called with the fallback symbol
                mock_asset.assert_called_with('AAPL.US')
    
    def test_prepare_comprehensive_metrics_none_portfolio_symbols(self):
        """Test that _prepare_comprehensive_metrics handles None portfolio_symbols correctly"""
        # Test data with None portfolio_symbols
        symbols = ['AAPL.US']
        currency = 'USD'
        expanded_symbols = ['AAPL.US']
        portfolio_contexts = [
            {
                'portfolio_symbols': None,  # None that would cause index error
                'portfolio_weights': [],
                'symbol': 'AAPL.US'
            }
        ]
        user_id = 12345
        
        # Mock the _get_user_context method
        with patch.object(self.bot, '_get_user_context', return_value={'describe_table': ''}):
            # Mock ok.Asset to avoid actual API calls
            with patch('okama.Asset') as mock_asset:
                mock_asset_instance = Mock()
                mock_asset.return_value = mock_asset_instance
                
                # This should not raise an IndexError
                result = self.bot._prepare_comprehensive_metrics(
                    symbols, currency, expanded_symbols, portfolio_contexts, user_id
                )
                
                # Verify the result structure
                self.assertIsInstance(result, dict)
                self.assertIn('symbols', result)
                self.assertIn('currency', result)
                self.assertIn('performance', result)
                
                # Verify that ok.Asset was called with the fallback symbol
                mock_asset.assert_called_with('AAPL.US')
    
    def test_prepare_comprehensive_metrics_valid_portfolio_symbols(self):
        """Test that _prepare_comprehensive_metrics works correctly with valid portfolio_symbols"""
        # Test data with valid portfolio_symbols
        symbols = ['AAPL.US']
        currency = 'USD'
        expanded_symbols = ['AAPL.US']
        portfolio_contexts = [
            {
                'portfolio_symbols': ['AAPL.US'],  # Valid list
                'portfolio_weights': [1.0],
                'symbol': 'AAPL.US'
            }
        ]
        user_id = 12345
        
        # Mock the _get_user_context method
        with patch.object(self.bot, '_get_user_context', return_value={'describe_table': ''}):
            # Mock ok.Asset to avoid actual API calls
            with patch('okama.Asset') as mock_asset:
                mock_asset_instance = Mock()
                mock_asset.return_value = mock_asset_instance
                
                # This should work correctly
                result = self.bot._prepare_comprehensive_metrics(
                    symbols, currency, expanded_symbols, portfolio_contexts, user_id
                )
                
                # Verify the result structure
                self.assertIsInstance(result, dict)
                self.assertIn('symbols', result)
                self.assertIn('currency', result)
                self.assertIn('performance', result)
                
                # Verify that ok.Asset was called with the first symbol from portfolio_symbols
                mock_asset.assert_called_with('AAPL.US')


if __name__ == '__main__':
    unittest.main()
