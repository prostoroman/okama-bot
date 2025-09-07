#!/usr/bin/env python3
"""
Test for Calmar Ratio, VaR 95%, and CVaR 95% calculation
"""

import unittest
import sys
import os
from unittest.mock import Mock, AsyncMock, patch
import pandas as pd
import numpy as np
import asyncio

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import okama as ok
    OKAMA_AVAILABLE = True
except ImportError:
    OKAMA_AVAILABLE = False
    print("Warning: okama library not available for testing")

from bot import ShansAi


class TestAdditionalMetricsCalculation(unittest.TestCase):
    """Test cases for Calmar Ratio, VaR 95%, and CVaR 95% calculation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    def test_calmar_ratio_calculation(self):
        """Test Calmar Ratio calculation"""
        # Test case 1: Normal values
        annual_return = 0.10  # 10%
        max_drawdown = -0.20  # -20%
        calmar_ratio = annual_return / abs(max_drawdown)
        expected_calmar = 0.5
        
        self.assertEqual(calmar_ratio, expected_calmar)
        print(f"✅ Calmar ratio calculation test passed: {calmar_ratio}")
        
        # Test case 2: Zero max drawdown
        annual_return = 0.10
        max_drawdown = 0.0
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0.0
        expected_calmar = 0.0
        
        self.assertEqual(calmar_ratio, expected_calmar)
        print(f"✅ Calmar ratio zero drawdown test passed: {calmar_ratio}")
    
    def test_var_95_calculation(self):
        """Test VaR 95% calculation"""
        # Create mock returns data
        np.random.seed(42)  # For reproducible results
        returns = pd.Series(np.random.normal(0.001, 0.02, 1000))  # 1000 daily returns
        
        # Calculate VaR 95% (5th percentile)
        var_95 = returns.quantile(0.05)
        
        # Verify VaR is negative (worst 5% of returns)
        self.assertLess(var_95, 0, "VaR 95% should be negative")
        
        # Verify approximately 5% of returns are below VaR
        returns_below_var = returns[returns <= var_95]
        percentage_below = len(returns_below_var) / len(returns)
        
        self.assertAlmostEqual(percentage_below, 0.05, delta=0.02, msg="Approximately 5% of returns should be below VaR")
        
        print(f"✅ VaR 95% calculation test passed: VaR={var_95:.4f}, % below VaR={percentage_below:.2%}")
    
    def test_cvar_95_calculation(self):
        """Test CVaR 95% calculation"""
        # Create mock returns data
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 1000))
        
        # Calculate VaR 95%
        var_95 = returns.quantile(0.05)
        
        # Calculate CVaR 95% (expected value of returns below VaR)
        returns_below_var = returns[returns <= var_95]
        cvar_95 = returns_below_var.mean()
        
        # Verify CVaR is worse than VaR (more negative)
        self.assertLess(cvar_95, var_95, "CVaR should be worse (more negative) than VaR")
        
        print(f"✅ CVaR 95% calculation test passed: VaR={var_95:.4f}, CVaR={cvar_95:.4f}")
    
    def test_additional_metrics_with_mock_data(self):
        """Test additional metrics calculation with mock data"""
        # Create mock asset with price data
        mock_asset = Mock()
        
        # Create realistic price data with some volatility
        dates = pd.date_range('2020-01-01', periods=60, freq='M')
        np.random.seed(42)
        returns = np.random.normal(0.01, 0.05, 60)  # 1% monthly return, 5% volatility
        prices = [100]  # Starting price
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
        
        price_series = pd.Series(prices[1:], index=dates)
        mock_asset.close_monthly = price_series
        
        print(f"\n=== Testing Additional Metrics with Mock Data ===")
        print(f"Price data: {len(price_series)} points")
        print(f"Price range: {price_series.min():.2f} - {price_series.max():.2f}")
        
        # Calculate metrics manually
        returns_calc = price_series.pct_change().dropna()
        
        # Basic metrics
        total_return = (price_series.iloc[-1] / price_series.iloc[0]) - 1
        periods = len(price_series)
        years = periods / 12.0
        annual_return = ((price_series.iloc[-1] / price_series.iloc[0]) ** (1.0 / years)) - 1
        volatility = returns_calc.std() * (12 ** 0.5)
        
        # Max drawdown
        cumulative = (1 + returns_calc).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Additional metrics
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0.0
        var_95 = returns_calc.quantile(0.05)
        returns_below_var = returns_calc[returns_calc <= var_95]
        cvar_95 = returns_below_var.mean() if len(returns_below_var) > 0 else var_95
        
        print(f"Calculated metrics:")
        print(f"  total_return: {total_return:.4f}")
        print(f"  annual_return: {annual_return:.4f}")
        print(f"  volatility: {volatility:.4f}")
        print(f"  max_drawdown: {max_drawdown:.4f}")
        print(f"  calmar_ratio: {calmar_ratio:.4f}")
        print(f"  var_95: {var_95:.4f}")
        print(f"  cvar_95: {cvar_95:.4f}")
        
        # Verify calculations
        self.assertNotEqual(calmar_ratio, 0, "Calmar ratio should not be zero")
        self.assertLess(var_95, 0, "VaR 95% should be negative")
        self.assertLessEqual(cvar_95, var_95, "CVaR should be <= VaR")
        
        print("✅ Additional metrics mock data test passed")
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_prepare_data_for_analysis_with_additional_metrics(self):
        """Test _prepare_data_for_analysis with additional metrics"""
        try:
            # Create real assets
            symbols = ['SPY.US']
            assets = [ok.Asset(symbol) for symbol in symbols]
            
            print(f"\n=== Testing Additional Metrics with Real Assets ===")
            
            # Test the enhanced prepare_data_for_analysis function
            import asyncio
            
            async def test_prepare_data():
                result = await self.bot._prepare_data_for_analysis(
                    symbols=symbols,
                    currency='USD',
                    expanded_symbols=assets,
                    portfolio_contexts=[],
                    user_id=12345
                )
                return result
            
            result = asyncio.run(test_prepare_data())
            
            if 'performance' in result:
                for symbol in symbols:
                    if symbol in result['performance']:
                        perf = result['performance'][symbol]
                        print(f"\n{symbol} performance metrics:")
                        print(f"  total_return: {perf.get('total_return', 'N/A')}")
                        print(f"  annual_return: {perf.get('annual_return', 'N/A')}")
                        print(f"  volatility: {perf.get('volatility', 'N/A')}")
                        print(f"  sharpe_ratio: {perf.get('sharpe_ratio', 'N/A')}")
                        print(f"  sortino_ratio: {perf.get('sortino_ratio', 'N/A')}")
                        print(f"  max_drawdown: {perf.get('max_drawdown', 'N/A')}")
                        print(f"  calmar_ratio: {perf.get('calmar_ratio', 'N/A')}")
                        print(f"  var_95: {perf.get('var_95', 'N/A')}")
                        print(f"  cvar_95: {perf.get('cvar_95', 'N/A')}")
                        
                        # Verify additional metrics are calculated
                        self.assertNotEqual(perf.get('calmar_ratio', 0), 0, f"{symbol} Calmar ratio should not be zero")
                        self.assertNotEqual(perf.get('var_95', 0), 0, f"{symbol} VaR 95% should not be zero")
                        self.assertNotEqual(perf.get('cvar_95', 0), 0, f"{symbol} CVaR 95% should not be zero")
            
            print("✅ Additional metrics real asset test passed")
            
        except Exception as e:
            self.fail(f"Error testing additional metrics with real assets: {e}")


if __name__ == '__main__':
    print("Testing additional metrics calculation...")
    print(f"OKAMA_AVAILABLE: {OKAMA_AVAILABLE}")
    
    unittest.main(verbosity=2)
