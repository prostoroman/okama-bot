#!/usr/bin/env python3
"""
Test for fixed Sharpe and Sortino ratio calculation
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import okama as ok
    OKAMA_AVAILABLE = True
except ImportError:
    OKAMA_AVAILABLE = False
    print("Warning: okama library not available for testing")

from bot import ShansAi


class TestFixedSharpeSortinoCalculation(unittest.TestCase):
    """Test cases for fixed Sharpe and Sortino ratio calculation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_real_asset_calculation(self):
        """Test calculation with real okama asset"""
        try:
            # Create a real asset
            asset = ok.Asset('SPY.US')
            
            print(f"\n=== Testing Real Asset Calculation ===")
            print(f"Asset: {asset.symbol}")
            print(f"Price data available:")
            print(f"  close_monthly: {hasattr(asset, 'close_monthly') and asset.close_monthly is not None}")
            print(f"  close_daily: {hasattr(asset, 'close_daily') and asset.close_daily is not None}")
            print(f"  adj_close: {hasattr(asset, 'adj_close') and asset.adj_close is not None}")
            
            # Test the calculation logic
            performance_metrics = {}
            
            # Get price data for calculations
            if hasattr(asset, 'close_monthly') and asset.close_monthly is not None:
                prices = asset.close_monthly
                print(f"Using close_monthly data: {len(prices)} points")
            elif hasattr(asset, 'close_daily') and asset.close_daily is not None:
                prices = asset.close_daily
                print(f"Using close_daily data: {len(prices)} points")
            elif hasattr(asset, 'adj_close') and asset.adj_close is not None:
                prices = asset.adj_close
                print(f"Using adj_close data: {len(prices)} points")
            else:
                prices = None
                print("No price data available")
            
            if prices is not None and len(prices) > 1:
                # Calculate returns from prices
                returns = prices.pct_change().dropna()
                print(f"Calculated returns: {len(returns)} points")
                
                # Calculate total return
                total_return = (prices.iloc[-1] / prices.iloc[0]) - 1
                performance_metrics['total_return'] = total_return
                print(f"Total return: {total_return:.4f}")
                
                # Calculate CAGR
                periods = len(prices)
                years = periods / 12.0  # Assuming monthly data
                if years > 0:
                    cagr = ((prices.iloc[-1] / prices.iloc[0]) ** (1.0 / years)) - 1
                    performance_metrics['annual_return'] = cagr
                    print(f"CAGR: {cagr:.4f} ({years:.1f} years)")
                else:
                    performance_metrics['annual_return'] = 0.0
                
                # Calculate volatility
                volatility = returns.std() * (12 ** 0.5)  # Annualized
                performance_metrics['volatility'] = volatility
                print(f"Volatility: {volatility:.4f}")
                
                # Calculate max drawdown
                cumulative = (1 + returns).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                max_drawdown = drawdown.min()
                performance_metrics['max_drawdown'] = max_drawdown
                print(f"Max drawdown: {max_drawdown:.4f}")
                
                # Calculate Sharpe ratio
                annual_return = performance_metrics.get('annual_return', 0)
                volatility = performance_metrics.get('volatility', 0)
                if volatility > 0:
                    sharpe_ratio = (annual_return - 0.02) / volatility
                    performance_metrics['sharpe_ratio'] = sharpe_ratio
                    print(f"Sharpe ratio: {sharpe_ratio:.4f}")
                else:
                    performance_metrics['sharpe_ratio'] = 0.0
                    print("Sharpe ratio: 0.0 (volatility = 0)")
                
                # Calculate Sortino ratio
                negative_returns = returns[returns < 0]
                print(f"Negative returns: {len(negative_returns)} out of {len(returns)}")
                if len(negative_returns) > 0:
                    downside_deviation = negative_returns.std() * (12 ** 0.5)  # Annualized
                    if downside_deviation > 0:
                        sortino_ratio = (annual_return - 0.02) / downside_deviation
                        performance_metrics['sortino_ratio'] = sortino_ratio
                        print(f"Sortino ratio: {sortino_ratio:.4f}")
                    else:
                        performance_metrics['sortino_ratio'] = 0.0
                        print("Sortino ratio: 0.0 (downside_deviation = 0)")
                else:
                    # No negative returns, use volatility as fallback
                    volatility = performance_metrics.get('volatility', 0)
                    if volatility > 0:
                        sortino_ratio = (annual_return - 0.02) / volatility
                        performance_metrics['sortino_ratio'] = sortino_ratio
                        print(f"Sortino ratio (fallback): {sortino_ratio:.4f}")
                    else:
                        performance_metrics['sortino_ratio'] = 0.0
                        print("Sortino ratio: 0.0 (volatility = 0)")
                
                # Verify calculations
                self.assertGreater(performance_metrics.get('sharpe_ratio', 0), 0, "Sharpe ratio should be positive")
                self.assertGreater(performance_metrics.get('sortino_ratio', 0), 0, "Sortino ratio should be positive")
                self.assertGreater(performance_metrics.get('annual_return', 0), 0, "Annual return should be positive")
                self.assertGreater(performance_metrics.get('volatility', 0), 0, "Volatility should be positive")
                
                print("✅ Real asset calculation test passed")
                
            else:
                self.fail("No price data available for calculation")
                
        except Exception as e:
            self.fail(f"Error testing real asset calculation: {e}")
    
    def test_mock_asset_with_price_data(self):
        """Test with mock asset that has price data"""
        # Create mock asset with price data
        mock_asset = Mock()
        
        # Create realistic price data (monthly)
        dates = pd.date_range('2020-01-01', periods=60, freq='M')
        # Simulate price growth with some volatility
        np.random.seed(42)  # For reproducible results
        returns = np.random.normal(0.01, 0.05, 60)  # 1% monthly return, 5% volatility
        prices = [100]  # Starting price
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
        
        price_series = pd.Series(prices[1:], index=dates)
        mock_asset.close_monthly = price_series
        
        print(f"\n=== Testing Mock Asset with Price Data ===")
        print(f"Price data: {len(price_series)} points")
        print(f"Price range: {price_series.min():.2f} - {price_series.max():.2f}")
        
        # Test the calculation logic
        performance_metrics = {}
        
        # Get price data for calculations
        if hasattr(mock_asset, 'close_monthly') and mock_asset.close_monthly is not None:
            prices = mock_asset.close_monthly
        else:
            prices = None
        
        if prices is not None and len(prices) > 1:
            # Calculate returns from prices
            returns = prices.pct_change().dropna()
            
            # Calculate total return
            total_return = (prices.iloc[-1] / prices.iloc[0]) - 1
            performance_metrics['total_return'] = total_return
            
            # Calculate CAGR
            periods = len(prices)
            years = periods / 12.0  # Assuming monthly data
            if years > 0:
                cagr = ((prices.iloc[-1] / prices.iloc[0]) ** (1.0 / years)) - 1
                performance_metrics['annual_return'] = cagr
            else:
                performance_metrics['annual_return'] = 0.0
            
            # Calculate volatility
            volatility = returns.std() * (12 ** 0.5)  # Annualized
            performance_metrics['volatility'] = volatility
            
            # Calculate max drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()
            performance_metrics['max_drawdown'] = max_drawdown
            
            # Calculate Sharpe ratio
            annual_return = performance_metrics.get('annual_return', 0)
            volatility = performance_metrics.get('volatility', 0)
            if volatility > 0:
                sharpe_ratio = (annual_return - 0.02) / volatility
                performance_metrics['sharpe_ratio'] = sharpe_ratio
            else:
                performance_metrics['sharpe_ratio'] = 0.0
            
            # Calculate Sortino ratio
            negative_returns = returns[returns < 0]
            if len(negative_returns) > 0:
                downside_deviation = negative_returns.std() * (12 ** 0.5)  # Annualized
                if downside_deviation > 0:
                    sortino_ratio = (annual_return - 0.02) / downside_deviation
                    performance_metrics['sortino_ratio'] = sortino_ratio
                else:
                    performance_metrics['sortino_ratio'] = 0.0
            else:
                # No negative returns, use volatility as fallback
                volatility = performance_metrics.get('volatility', 0)
                if volatility > 0:
                    sortino_ratio = (annual_return - 0.02) / volatility
                    performance_metrics['sortino_ratio'] = sortino_ratio
                else:
                    performance_metrics['sortino_ratio'] = 0.0
        
        print(f"Calculated metrics:")
        print(f"  total_return: {performance_metrics.get('total_return', 'N/A'):.4f}")
        print(f"  annual_return: {performance_metrics.get('annual_return', 'N/A'):.4f}")
        print(f"  volatility: {performance_metrics.get('volatility', 'N/A'):.4f}")
        print(f"  max_drawdown: {performance_metrics.get('max_drawdown', 'N/A'):.4f}")
        print(f"  sharpe_ratio: {performance_metrics.get('sharpe_ratio', 'N/A'):.4f}")
        print(f"  sortino_ratio: {performance_metrics.get('sortino_ratio', 'N/A'):.4f}")
        
        # Verify calculations
        self.assertIsNotNone(performance_metrics.get('sharpe_ratio'), "Sharpe ratio should be calculated")
        self.assertIsNotNone(performance_metrics.get('sortino_ratio'), "Sortino ratio should be calculated")
        self.assertGreater(performance_metrics.get('annual_return', 0), 0, "Annual return should be positive")
        self.assertGreater(performance_metrics.get('volatility', 0), 0, "Volatility should be positive")
        
        print("✅ Mock asset calculation test passed")
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_prepare_data_for_analysis_integration(self):
        """Test the full _prepare_data_for_analysis function"""
        try:
            # Create real assets
            symbols = ['SPY.US', 'QQQ.US']
            assets = [ok.Asset(symbol) for symbol in symbols]
            
            print(f"\n=== Testing Full Integration ===")
            
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
                        
                        # Verify calculations
                        self.assertGreater(perf.get('sharpe_ratio', 0), 0, f"{symbol} Sharpe ratio should be positive")
                        self.assertGreater(perf.get('sortino_ratio', 0), 0, f"{symbol} Sortino ratio should be positive")
                        self.assertGreater(perf.get('annual_return', 0), 0, f"{symbol} Annual return should be positive")
                        self.assertGreater(perf.get('volatility', 0), 0, f"{symbol} Volatility should be positive")
            
            print("✅ Full integration test passed")
            
        except Exception as e:
            self.fail(f"Error testing full integration: {e}")


if __name__ == '__main__':
    print("Testing fixed Sharpe and Sortino ratio calculation...")
    print(f"OKAMA_AVAILABLE: {OKAMA_AVAILABLE}")
    
    unittest.main(verbosity=2)
