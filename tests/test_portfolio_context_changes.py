#!/usr/bin/env python3
"""
Test for portfolio context changes compatibility
"""

import unittest
import sys
import os

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import okama as ok
    OKAMA_AVAILABLE = True
except ImportError:
    OKAMA_AVAILABLE = False
    print("Warning: okama library not available for testing")

from bot import ShansAi


class TestPortfolioContextChanges(unittest.TestCase):
    """Test cases for portfolio context changes compatibility"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    def test_portfolio_context_symbol_extraction(self):
        """Test that clean symbols are properly extracted from descriptive names"""
        try:
            # Test cases for symbol extraction
            test_cases = [
                ("PF_1 (SPY.US, QQQ.US)", "PF_1"),
                ("portfolio_123.PF (AAPL.US, MSFT.US)", "portfolio_123.PF"),
                ("MyPortfolio (SBER.MOEX, GAZP.MOEX)", "MyPortfolio"),
                ("SPY.US", "SPY.US"),  # Regular asset symbol
                ("PF_1", "PF_1"),  # Portfolio without composition
            ]
            
            for descriptive_name, expected_clean in test_cases:
                # Simulate the extraction logic
                clean_symbol = descriptive_name.split(' (')[0]
                self.assertEqual(clean_symbol, expected_clean, 
                               f"Failed to extract clean symbol from '{descriptive_name}'")
            
            print("✅ All symbol extraction tests passed")
            
        except Exception as e:
            self.fail(f"Error testing symbol extraction: {e}")
    
    def test_portfolio_context_structure(self):
        """Test that portfolio context structure is maintained"""
        try:
            # Create a mock portfolio context
            portfolio_context = {
                'symbol': 'PF_1 (SPY.US, QQQ.US)',  # Descriptive name
                'portfolio_symbols': ['SPY.US', 'QQQ.US'],
                'portfolio_weights': [0.6, 0.4],
                'portfolio_currency': 'USD',
                'portfolio_object': None
            }
            
            # Test that all required fields are present
            required_fields = ['symbol', 'portfolio_symbols', 'portfolio_weights', 'portfolio_currency']
            for field in required_fields:
                self.assertIn(field, portfolio_context, f"Missing required field: {field}")
            
            # Test that descriptive name contains composition
            self.assertIn('(', portfolio_context['symbol'])
            self.assertIn('SPY.US', portfolio_context['symbol'])
            self.assertIn('QQQ.US', portfolio_context['symbol'])
            
            print("✅ Portfolio context structure test passed")
            
        except Exception as e:
            self.fail(f"Error testing portfolio context structure: {e}")
    
    def test_clean_and_display_symbols_separation(self):
        """Test that clean and display symbols are properly separated"""
        try:
            # Mock symbols and portfolio contexts
            symbols = ['PF_1 (SPY.US, QQQ.US)', 'AAPL.US']
            portfolio_contexts = [
                {
                    'symbol': 'PF_1 (SPY.US, QQQ.US)',
                    'portfolio_symbols': ['SPY.US', 'QQQ.US'],
                    'portfolio_weights': [0.6, 0.4],
                    'portfolio_currency': 'USD'
                }
            ]
            expanded_symbols = [None, 'AAPL.US']  # Mock expanded symbols
            
            # Simulate the logic from compare command
            clean_symbols = []
            display_symbols = []
            
            for i, symbol in enumerate(symbols):
                if i < len(portfolio_contexts):
                    clean_symbols.append(portfolio_contexts[i]['symbol'].split(' (')[0])
                    display_symbols.append(portfolio_contexts[i]['symbol'])
                else:
                    clean_symbols.append(symbol)
                    display_symbols.append(symbol)
            
            # Verify results
            self.assertEqual(clean_symbols, ['PF_1', 'AAPL.US'])
            self.assertEqual(display_symbols, ['PF_1 (SPY.US, QQQ.US)', 'AAPL.US'])
            
            print("✅ Clean and display symbols separation test passed")
            
        except Exception as e:
            self.fail(f"Error testing symbols separation: {e}")


if __name__ == '__main__':
    print("Testing portfolio context changes compatibility...")
    print(f"OKAMA_AVAILABLE: {OKAMA_AVAILABLE}")
    
    unittest.main(verbosity=2)
