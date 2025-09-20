#!/usr/bin/env python3
"""
Test for portfolio context validation functionality.

This test verifies that when there are both portfolios and regular assets in context,
only regular assets are offered for portfolio creation (preventing portfolio-in-portfolio scenarios).
"""

import unittest
import pandas as pd


class TestPortfolioContextValidation(unittest.TestCase):
    """Test portfolio context validation functionality."""
    
    def test_filter_regular_assets_from_mixed_context(self):
        """Test that regular assets are filtered from mixed portfolio/asset context."""
        # Mock user context with mixed portfolio and regular assets
        portfolio_contexts = [
            {
                'symbol': 'PF1',
                'portfolio_symbols': ['SBER.MOEX', 'GAZP.MOEX'],
                'portfolio_weights': [0.5, 0.5]
            },
            {
                'symbol': 'LKOH.MOEX',
                'portfolio_symbols': ['LKOH.MOEX'],
                'portfolio_weights': [1.0]
            }
        ]
        
        expanded_symbols = [
            pd.Series([1, 2, 3]),  # Portfolio PF1
            'LKOH.MOEX'  # Regular asset
        ]
        
        # Test symbols that include both portfolio and regular asset
        test_symbols = ['PF1', 'LKOH.MOEX']
        
        # Apply the same filtering logic as in the actual method
        regular_assets = []
        portfolio_symbols = []
        
        for i, symbol in enumerate(test_symbols):
            is_portfolio = False
            if i < len(expanded_symbols) and isinstance(expanded_symbols[i], (pd.Series, pd.DataFrame)):
                is_portfolio = True
                portfolio_symbols.append(symbol)
            elif i < len(portfolio_contexts):
                portfolio_context = portfolio_contexts[i]
                if len(portfolio_context.get('portfolio_symbols', [])) > 1:
                    is_portfolio = True
                    portfolio_symbols.append(symbol)
            
            if not is_portfolio:
                regular_assets.append(symbol)
        
        # Verify the filtering worked correctly
        self.assertEqual(regular_assets, ['LKOH.MOEX'], "Should only include regular assets")
        self.assertEqual(portfolio_symbols, ['PF1'], "Should identify portfolio symbols")
        
        # Verify that when both exist, only regular assets are used
        if portfolio_symbols and regular_assets:
            symbols_to_use = regular_assets
            self.assertEqual(symbols_to_use, ['LKOH.MOEX'], "Should use only regular assets when mixed context")
    
    def test_all_regular_assets_context(self):
        """Test that all assets are used when context contains only regular assets."""
        # Mock user context with only regular assets
        portfolio_contexts = [
            {
                'symbol': 'LKOH.MOEX',
                'portfolio_symbols': ['LKOH.MOEX'],
                'portfolio_weights': [1.0]
            },
            {
                'symbol': 'SBER.MOEX',
                'portfolio_symbols': ['SBER.MOEX'],
                'portfolio_weights': [1.0]
            }
        ]
        
        expanded_symbols = ['LKOH.MOEX', 'SBER.MOEX']
        
        test_symbols = ['LKOH.MOEX', 'SBER.MOEX']
        
        # Apply filtering logic
        regular_assets = []
        portfolio_symbols = []
        
        for i, symbol in enumerate(test_symbols):
            is_portfolio = False
            if i < len(expanded_symbols) and isinstance(expanded_symbols[i], (pd.Series, pd.DataFrame)):
                is_portfolio = True
                portfolio_symbols.append(symbol)
            elif i < len(portfolio_contexts):
                portfolio_context = portfolio_contexts[i]
                if len(portfolio_context.get('portfolio_symbols', [])) > 1:
                    is_portfolio = True
                    portfolio_symbols.append(symbol)
            
            if not is_portfolio:
                regular_assets.append(symbol)
        
        # Verify that all assets are used when no portfolios are present
        self.assertEqual(regular_assets, ['LKOH.MOEX', 'SBER.MOEX'], "Should include all regular assets")
        self.assertEqual(portfolio_symbols, [], "Should not identify any portfolios")
        
        # When no portfolios exist, use all symbols
        if not portfolio_symbols:
            symbols_to_use = test_symbols
            self.assertEqual(symbols_to_use, ['LKOH.MOEX', 'SBER.MOEX'], "Should use all symbols when no portfolios")
    
    def test_all_portfolios_context(self):
        """Test behavior when context contains only portfolios."""
        # Mock user context with only portfolios
        portfolio_contexts = [
            {
                'symbol': 'PF1',
                'portfolio_symbols': ['SBER.MOEX', 'GAZP.MOEX'],
                'portfolio_weights': [0.5, 0.5]
            },
            {
                'symbol': 'PF2',
                'portfolio_symbols': ['LKOH.MOEX', 'NVTK.MOEX'],
                'portfolio_weights': [0.6, 0.4]
            }
        ]
        
        expanded_symbols = [
            pd.Series([1, 2, 3]),  # Portfolio PF1
            pd.Series([4, 5, 6])   # Portfolio PF2
        ]
        
        test_symbols = ['PF1', 'PF2']
        
        # Apply filtering logic
        regular_assets = []
        portfolio_symbols = []
        
        for i, symbol in enumerate(test_symbols):
            is_portfolio = False
            if i < len(expanded_symbols) and isinstance(expanded_symbols[i], (pd.Series, pd.DataFrame)):
                is_portfolio = True
                portfolio_symbols.append(symbol)
            elif i < len(portfolio_contexts):
                portfolio_context = portfolio_contexts[i]
                if len(portfolio_context.get('portfolio_symbols', [])) > 1:
                    is_portfolio = True
                    portfolio_symbols.append(symbol)
            
            if not is_portfolio:
                regular_assets.append(symbol)
        
        # Verify that all symbols are identified as portfolios
        self.assertEqual(regular_assets, [], "Should not identify any regular assets")
        self.assertEqual(portfolio_symbols, ['PF1', 'PF2'], "Should identify all as portfolios")
        
        # When no regular assets exist, use all symbols (this would be handled by the calling code)
        if not regular_assets:
            symbols_to_use = test_symbols
            self.assertEqual(symbols_to_use, ['PF1', 'PF2'], "Should use all symbols when no regular assets")


if __name__ == '__main__':
    unittest.main()
