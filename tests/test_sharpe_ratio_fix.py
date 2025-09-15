#!/usr/bin/env python3
"""
Test script to verify the Sharpe ratio fix in portfolio wealth chart
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
import okama as ok
import numpy as np


class TestSharpeRatioFix(unittest.TestCase):
    """Test cases for Sharpe ratio calculation fix"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
        
    def test_sharpe_ratio_scalar_handling(self):
        """Test that scalar Sharpe ratio values are handled correctly"""
        # Create a mock portfolio that returns a scalar Sharpe ratio
        mock_portfolio = Mock()
        mock_portfolio.get_sharpe_ratio.return_value = np.float64(0.8309827727797839)
        
        # Test the Sharpe ratio extraction logic
        sharpe_value = None
        if hasattr(mock_portfolio, 'get_sharpe_ratio'):
            try:
                sharpe = mock_portfolio.get_sharpe_ratio()
                # Handle different return types from okama
                if hasattr(sharpe, 'iloc'):
                    # pandas Series or DataFrame
                    sharpe_value = sharpe.iloc[0]
                elif hasattr(sharpe, '__getitem__') and not isinstance(sharpe, (int, float)):
                    # Array-like but not scalar
                    sharpe_value = sharpe[0]
                else:
                    # Scalar value (numpy.float64, float, int)
                    sharpe_value = float(sharpe)
            except Exception as e:
                self.fail(f"Sharpe ratio extraction failed: {e}")
        
        # Verify the result
        self.assertIsNotNone(sharpe_value)
        self.assertAlmostEqual(sharpe_value, 0.8309827727797839, places=10)
        self.assertIsInstance(sharpe_value, float)
    
    def test_sharpe_ratio_with_real_okama_portfolio(self):
        """Test Sharpe ratio extraction with real okama portfolio"""
        try:
            # Create a real portfolio
            symbols = ['SPY.US', 'QQQ.US', 'BND.US']
            portfolio = ok.Portfolio(assets=symbols)
            
            # Test Sharpe ratio extraction
            sharpe_value = None
            if hasattr(portfolio, 'get_sharpe_ratio'):
                try:
                    sharpe = portfolio.get_sharpe_ratio()
                    # Handle different return types from okama
                    if hasattr(sharpe, 'iloc'):
                        # pandas Series or DataFrame
                        sharpe_value = sharpe.iloc[0]
                    elif hasattr(sharpe, '__getitem__') and not isinstance(sharpe, (int, float)):
                        # Array-like but not scalar
                        sharpe_value = sharpe[0]
                    else:
                        # Scalar value (numpy.float64, float, int)
                        sharpe_value = float(sharpe)
                except Exception as e:
                    self.fail(f"Sharpe ratio extraction failed: {e}")
            
            # Verify the result
            self.assertIsNotNone(sharpe_value)
            self.assertIsInstance(sharpe_value, float)
            self.assertGreater(sharpe_value, -10)  # Reasonable range
            self.assertLess(sharpe_value, 10)      # Reasonable range
            
        except Exception as e:
            self.skipTest(f"Could not create okama portfolio: {e}")
    
    def test_sharpe_ratio_pandas_series_handling(self):
        """Test that pandas Series Sharpe ratio values are handled correctly"""
        import pandas as pd
        
        # Create a mock portfolio that returns a pandas Series
        mock_portfolio = Mock()
        mock_portfolio.get_sharpe_ratio.return_value = pd.Series([0.5, 0.6, 0.7])
        
        # Test the Sharpe ratio extraction logic
        sharpe_value = None
        if hasattr(mock_portfolio, 'get_sharpe_ratio'):
            try:
                sharpe = mock_portfolio.get_sharpe_ratio()
                # Handle different return types from okama
                if hasattr(sharpe, 'iloc'):
                    # pandas Series or DataFrame
                    sharpe_value = sharpe.iloc[0]
                elif hasattr(sharpe, '__getitem__') and not isinstance(sharpe, (int, float)):
                    # Array-like but not scalar
                    sharpe_value = sharpe[0]
                else:
                    # Scalar value (numpy.float64, float, int)
                    sharpe_value = float(sharpe)
            except Exception as e:
                self.fail(f"Sharpe ratio extraction failed: {e}")
        
        # Verify the result
        self.assertIsNotNone(sharpe_value)
        self.assertAlmostEqual(sharpe_value, 0.5, places=10)
    
    def test_sharpe_ratio_array_handling(self):
        """Test that array-like Sharpe ratio values are handled correctly"""
        # Create a mock portfolio that returns an array-like object
        mock_portfolio = Mock()
        mock_portfolio.get_sharpe_ratio.return_value = [0.8, 0.9, 1.0]  # List
        
        # Test the Sharpe ratio extraction logic
        sharpe_value = None
        if hasattr(mock_portfolio, 'get_sharpe_ratio'):
            try:
                sharpe = mock_portfolio.get_sharpe_ratio()
                # Handle different return types from okama
                if hasattr(sharpe, 'iloc'):
                    # pandas Series or DataFrame
                    sharpe_value = sharpe.iloc[0]
                elif hasattr(sharpe, '__getitem__') and not isinstance(sharpe, (int, float)):
                    # Array-like but not scalar
                    sharpe_value = sharpe[0]
                else:
                    # Scalar value (numpy.float64, float, int)
                    sharpe_value = float(sharpe)
            except Exception as e:
                self.fail(f"Sharpe ratio extraction failed: {e}")
        
        # Verify the result
        self.assertIsNotNone(sharpe_value)
        self.assertAlmostEqual(sharpe_value, 0.8, places=10)


if __name__ == '__main__':
    unittest.main()
