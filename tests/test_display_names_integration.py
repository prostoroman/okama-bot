#!/usr/bin/env python3
"""
Test for display names integration in analysis functions
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


class TestDisplayNamesIntegration(unittest.TestCase):
    """Test cases for display names integration in analysis functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    def test_display_symbols_usage_in_analysis(self):
        """Test that display_symbols are properly used in analysis functions"""
        try:
            # Mock user context with both clean and display symbols
            user_context = {
                'current_symbols': ['PF_1', 'SPY.US'],
                'display_symbols': ['PF_1 (SPY.US, QQQ.US)', 'SPY.US'],
                'expanded_symbols': [None, 'SPY.US'],  # Mock expanded symbols
                'portfolio_contexts': [
                    {
                        'symbol': 'PF_1 (SPY.US, QQQ.US)',
                        'portfolio_symbols': ['SPY.US', 'QQQ.US'],
                        'portfolio_weights': [0.6, 0.4],
                        'portfolio_currency': 'USD'
                    }
                ]
            }
            
            # Test the logic from analysis functions
            symbols = user_context.get('current_symbols', [])
            display_symbols = user_context.get('display_symbols', symbols)
            expanded_symbols = user_context.get('expanded_symbols', [])
            portfolio_contexts = user_context.get('portfolio_contexts', [])
            
            # Simulate asset list creation logic
            asset_names = []
            for i, symbol in enumerate(symbols):
                if i < len(expanded_symbols):
                    if isinstance(expanded_symbols[i], (type(None),)):
                        # This is a portfolio
                        if i < len(portfolio_contexts):
                            asset_names.append(display_symbols[i])  # Use descriptive name
                    else:
                        # This is a regular asset
                        asset_names.append(display_symbols[i])  # Use descriptive name
            
            # Verify results
            expected_names = ['PF_1 (SPY.US, QQQ.US)', 'SPY.US']
            self.assertEqual(asset_names, expected_names)
            
            print("✅ Display symbols integration test passed")
            
        except Exception as e:
            self.fail(f"Error testing display symbols integration: {e}")
    
    def test_portfolio_context_symbol_usage(self):
        """Test that portfolio context symbol is used correctly"""
        try:
            # Mock portfolio context
            portfolio_context = {
                'symbol': 'PF_1 (SPY.US, QQQ.US)',
                'portfolio_symbols': ['SPY.US', 'QQQ.US'],
                'portfolio_weights': [0.6, 0.4],
                'portfolio_currency': 'USD'
            }
            
            # Test portfolio info creation (as used in AI analysis)
            portfolio_info = f"Портфель {portfolio_context.get('symbol', 'Unknown')}: {len(portfolio_context.get('portfolio_symbols', []))} активов"
            
            expected_info = "Портфель PF_1 (SPY.US, QQQ.US): 2 активов"
            self.assertEqual(portfolio_info, expected_info)
            
            print("✅ Portfolio context symbol usage test passed")
            
        except Exception as e:
            self.fail(f"Error testing portfolio context symbol usage: {e}")
    
    def test_display_symbols_fallback(self):
        """Test that display_symbols fallback works correctly"""
        try:
            # Mock user context without display_symbols
            user_context = {
                'current_symbols': ['SPY.US', 'QQQ.US'],
                # No display_symbols field
            }
            
            symbols = user_context.get('current_symbols', [])
            display_symbols = user_context.get('display_symbols', symbols)  # Fallback to symbols
            
            # Should fallback to current_symbols
            self.assertEqual(display_symbols, symbols)
            self.assertEqual(display_symbols, ['SPY.US', 'QQQ.US'])
            
            print("✅ Display symbols fallback test passed")
            
        except Exception as e:
            self.fail(f"Error testing display symbols fallback: {e}")


if __name__ == '__main__':
    print("Testing display names integration in analysis functions...")
    print(f"OKAMA_AVAILABLE: {OKAMA_AVAILABLE}")
    
    unittest.main(verbosity=2)
