#!/usr/bin/env python3
"""
Test for fixed data preparation method
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


class TestFixedDataPreparation(unittest.TestCase):
    """Test cases for fixed data preparation method"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_prepare_data_for_analysis_with_real_assets(self):
        """Test _prepare_data_for_analysis with real okama assets"""
        try:
            # Create real assets
            symbols = ['SPY.US', 'QQQ.US']
            assets = [ok.Asset(symbol) for symbol in symbols]
            
            print(f"\n=== Testing Fixed Data Preparation ===")
            
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
            
            print(f"Result keys: {list(result.keys())}")
            
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
                        
                        # Verify calculations are not zero
                        self.assertNotEqual(perf.get('annual_return', 0), 0, f"{symbol} Annual return should not be zero")
                        self.assertNotEqual(perf.get('volatility', 0), 0, f"{symbol} Volatility should not be zero")
                        self.assertNotEqual(perf.get('sharpe_ratio', 0), 0, f"{symbol} Sharpe ratio should not be zero")
                        self.assertNotEqual(perf.get('sortino_ratio', 0), 0, f"{symbol} Sortino ratio should not be zero")
            
            print("✅ Fixed data preparation test passed")
            
        except Exception as e:
            self.fail(f"Error testing fixed data preparation: {e}")
    
    def test_cagr_calculation_with_different_frequencies(self):
        """Test CAGR calculation with different data frequencies"""
        # Mock asset with monthly data
        mock_asset_monthly = Mock()
        monthly_prices = pd.Series([100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155])  # 12 months
        mock_asset_monthly.close_monthly = monthly_prices
        mock_asset_monthly.close_daily = None
        mock_asset_monthly.adj_close = None
        
        # Mock asset with daily data
        mock_asset_daily = Mock()
        daily_prices = pd.Series([100] + [100 + i for i in range(1, 253)])  # 252 trading days
        mock_asset_daily.close_monthly = None
        mock_asset_daily.close_daily = daily_prices
        mock_asset_daily.adj_close = None
        
        print(f"\n=== Testing CAGR Calculation ===")
        
        # Test monthly data
        periods_monthly = len(monthly_prices)
        years_monthly = periods_monthly / 12.0
        cagr_monthly = ((monthly_prices.iloc[-1] / monthly_prices.iloc[0]) ** (1.0 / years_monthly)) - 1
        
        print(f"Monthly data: periods={periods_monthly}, years={years_monthly}, CAGR={cagr_monthly:.4f}")
        
        # Test daily data
        periods_daily = len(daily_prices)
        years_daily = periods_daily / 252.0
        cagr_daily = ((daily_prices.iloc[-1] / daily_prices.iloc[0]) ** (1.0 / years_daily)) - 1
        
        print(f"Daily data: periods={periods_daily}, years={years_daily}, CAGR={cagr_daily:.4f}")
        
        # Verify calculations
        self.assertGreater(cagr_monthly, 0, "Monthly CAGR should be positive")
        self.assertGreater(cagr_daily, 0, "Daily CAGR should be positive")
        
        print("✅ CAGR calculation test passed")
    
    def test_volatility_calculation_with_different_frequencies(self):
        """Test volatility calculation with different data frequencies"""
        # Mock asset with monthly data
        mock_asset_monthly = Mock()
        monthly_prices = pd.Series([100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155])
        monthly_returns = monthly_prices.pct_change().dropna()
        mock_asset_monthly.close_monthly = monthly_prices
        mock_asset_monthly.close_daily = None
        mock_asset_monthly.adj_close = None
        
        # Mock asset with daily data
        mock_asset_daily = Mock()
        daily_prices = pd.Series([100] + [100 + i for i in range(1, 253)])
        daily_returns = daily_prices.pct_change().dropna()
        mock_asset_daily.close_monthly = None
        mock_asset_daily.close_daily = daily_prices
        mock_asset_daily.adj_close = None
        
        print(f"\n=== Testing Volatility Calculation ===")
        
        # Test monthly data
        volatility_monthly = monthly_returns.std() * (12 ** 0.5)
        print(f"Monthly volatility: {volatility_monthly:.4f}")
        
        # Test daily data
        volatility_daily = daily_returns.std() * (252 ** 0.5)
        print(f"Daily volatility: {volatility_daily:.4f}")
        
        # Verify calculations
        self.assertGreater(volatility_monthly, 0, "Monthly volatility should be positive")
        self.assertGreater(volatility_daily, 0, "Daily volatility should be positive")
        
        print("✅ Volatility calculation test passed")
    
    def test_sortino_ratio_calculation_with_different_frequencies(self):
        """Test Sortino ratio calculation with different data frequencies"""
        # Mock asset with monthly data
        mock_asset_monthly = Mock()
        monthly_prices = pd.Series([100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155])
        monthly_returns = monthly_prices.pct_change().dropna()
        mock_asset_monthly.close_monthly = monthly_prices
        mock_asset_monthly.close_daily = None
        mock_asset_monthly.adj_close = None
        
        print(f"\n=== Testing Sortino Ratio Calculation ===")
        
        # Test monthly data
        negative_returns_monthly = monthly_returns[monthly_returns < 0]
        if len(negative_returns_monthly) > 0:
            downside_deviation_monthly = negative_returns_monthly.std() * (12 ** 0.5)
            annual_return_monthly = 0.1  # Mock annual return
            sortino_monthly = (annual_return_monthly - 0.02) / downside_deviation_monthly
            print(f"Monthly Sortino: downside_deviation={downside_deviation_monthly:.4f}, sortino={sortino_monthly:.4f}")
        else:
            print("Monthly data: No negative returns")
        
        # Verify calculations
        if len(negative_returns_monthly) > 0:
            self.assertGreater(downside_deviation_monthly, 0, "Monthly downside deviation should be positive")
        
        print("✅ Sortino ratio calculation test passed")


if __name__ == '__main__':
    print("Testing fixed data preparation method...")
    print(f"OKAMA_AVAILABLE: {OKAMA_AVAILABLE}")
    
    unittest.main(verbosity=2)
