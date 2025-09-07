#!/usr/bin/env python3
"""
Test for debugging Sharpe and Sortino ratio calculation issues
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


class TestSharpeSortinoDebugging(unittest.TestCase):
    """Test cases for debugging Sharpe and Sortino ratio issues"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_real_asset_data_structure(self):
        """Test the actual structure of okama asset data"""
        try:
            # Create a real asset to see its structure
            asset = ok.Asset('SPY.US')
            
            print(f"\n=== Asset Structure Analysis ===")
            print(f"Asset type: {type(asset)}")
            print(f"Asset attributes: {dir(asset)}")
            
            # Check basic metrics
            print(f"\n=== Basic Metrics ===")
            if hasattr(asset, 'annual_return'):
                print(f"annual_return: {asset.annual_return} (type: {type(asset.annual_return)})")
            if hasattr(asset, 'volatility'):
                print(f"volatility: {asset.volatility} (type: {type(asset.volatility)})")
            if hasattr(asset, 'total_return'):
                print(f"total_return: {asset.total_return} (type: {type(asset.total_return)})")
            if hasattr(asset, 'max_drawdown'):
                print(f"max_drawdown: {asset.max_drawdown} (type: {type(asset.max_drawdown)})")
            
            # Check Sharpe ratio methods
            print(f"\n=== Sharpe Ratio Methods ===")
            if hasattr(asset, 'get_sharpe_ratio'):
                print(f"get_sharpe_ratio exists: {callable(asset.get_sharpe_ratio)}")
                try:
                    sharpe = asset.get_sharpe_ratio(rf_return=0.02)
                    print(f"get_sharpe_ratio(0.02): {sharpe} (type: {type(sharpe)})")
                except Exception as e:
                    print(f"get_sharpe_ratio error: {e}")
            
            if hasattr(asset, 'sharpe_ratio'):
                print(f"sharpe_ratio: {asset.sharpe_ratio} (type: {type(asset.sharpe_ratio)})")
            
            # Check Sortino ratio methods
            print(f"\n=== Sortino Ratio Methods ===")
            if hasattr(asset, 'sortino_ratio'):
                print(f"sortino_ratio: {asset.sortino_ratio} (type: {type(asset.sortino_ratio)})")
            
            if hasattr(asset, 'returns'):
                returns = asset.returns
                print(f"returns: {type(returns)}")
                if returns is not None:
                    print(f"returns length: {len(returns)}")
                    print(f"returns sample: {returns.head()}")
                    print(f"returns negative count: {len(returns[returns < 0])}")
            
            # Test manual calculation
            print(f"\n=== Manual Calculation Test ===")
            annual_return = getattr(asset, 'annual_return', 0)
            volatility = getattr(asset, 'volatility', 0)
            
            print(f"Manual annual_return: {annual_return}")
            print(f"Manual volatility: {volatility}")
            
            if volatility > 0:
                manual_sharpe = (annual_return - 0.02) / volatility
                print(f"Manual Sharpe ratio: {manual_sharpe}")
            else:
                print("Manual Sharpe ratio: Cannot calculate (volatility = 0)")
            
            # Test the actual function
            print(f"\n=== Testing _prepare_data_for_analysis ===")
            import asyncio
            
            async def test_prepare_data():
                result = await self.bot._prepare_data_for_analysis(
                    symbols=['SPY.US'],
                    currency='USD',
                    expanded_symbols=[asset],
                    portfolio_contexts=[],
                    user_id=12345
                )
                return result
            
            result = asyncio.run(test_prepare_data())
            
            if 'SPY.US' in result['performance']:
                perf = result['performance']['SPY.US']
                print(f"Performance metrics from function:")
                print(f"  annual_return: {perf.get('annual_return', 'N/A')}")
                print(f"  volatility: {perf.get('volatility', 'N/A')}")
                print(f"  sharpe_ratio: {perf.get('sharpe_ratio', 'N/A')}")
                print(f"  sortino_ratio: {perf.get('sortino_ratio', 'N/A')}")
            
        except Exception as e:
            self.fail(f"Error testing real asset data: {e}")
    
    def test_mock_asset_with_real_values(self):
        """Test with mock asset that has realistic values"""
        # Create mock asset with realistic financial data
        mock_asset = Mock()
        mock_asset.annual_return = 0.12  # 12% annual return
        mock_asset.volatility = 0.15     # 15% volatility
        mock_asset.total_return = 0.10   # 10% total return
        mock_asset.max_drawdown = -0.20  # -20% max drawdown
        
        # Mock returns data with some negative returns
        returns_data = pd.Series([
            0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01, 0.02,
            0.015, -0.01, 0.025, -0.005, 0.02, -0.02, 0.01, 0.03
        ])
        mock_asset.returns = returns_data
        
        # Test the calculation logic
        performance_metrics = {}
        
        # Basic metrics
        performance_metrics['annual_return'] = mock_asset.annual_return
        performance_metrics['volatility'] = mock_asset.volatility
        
        print(f"\n=== Mock Asset Test ===")
        print(f"annual_return: {performance_metrics['annual_return']}")
        print(f"volatility: {performance_metrics['volatility']}")
        
        # Sharpe ratio calculation
        try:
            if hasattr(mock_asset, 'get_sharpe_ratio'):
                sharpe_ratio = mock_asset.get_sharpe_ratio(rf_return=0.02)
                performance_metrics['sharpe_ratio'] = float(sharpe_ratio)
            elif hasattr(mock_asset, 'sharpe_ratio'):
                performance_metrics['sharpe_ratio'] = mock_asset.sharpe_ratio
            else:
                # Manual Sharpe ratio calculation
                annual_return = performance_metrics.get('annual_return', 0)
                volatility = performance_metrics.get('volatility', 0)
                print(f"Manual Sharpe calculation: annual_return={annual_return}, volatility={volatility}")
                if volatility > 0:
                    sharpe_ratio = (annual_return - 0.02) / volatility
                    performance_metrics['sharpe_ratio'] = sharpe_ratio
                    print(f"Manual Sharpe ratio: {sharpe_ratio}")
                else:
                    performance_metrics['sharpe_ratio'] = 0.0
                    print("Manual Sharpe ratio: 0.0 (volatility = 0)")
        except Exception as e:
            print(f"Sharpe ratio error: {e}")
            performance_metrics['sharpe_ratio'] = 0.0
        
        # Sortino ratio calculation
        try:
            if hasattr(mock_asset, 'sortino_ratio'):
                performance_metrics['sortino_ratio'] = mock_asset.sortino_ratio
            else:
                # Manual Sortino ratio calculation
                annual_return = performance_metrics.get('annual_return', 0)
                if hasattr(mock_asset, 'returns'):
                    returns = mock_asset.returns
                    print(f"Returns data: {len(returns)} values")
                    if returns is not None and len(returns) > 0:
                        # Calculate downside deviation (only negative returns)
                        negative_returns = returns[returns < 0]
                        print(f"Negative returns: {len(negative_returns)} values")
                        if len(negative_returns) > 0:
                            downside_deviation = negative_returns.std() * (12 ** 0.5)  # Annualized
                            print(f"Downside deviation: {downside_deviation}")
                            if downside_deviation > 0:
                                sortino_ratio = (annual_return - 0.02) / downside_deviation
                                performance_metrics['sortino_ratio'] = sortino_ratio
                                print(f"Manual Sortino ratio: {sortino_ratio}")
                            else:
                                performance_metrics['sortino_ratio'] = 0.0
                                print("Manual Sortino ratio: 0.0 (downside_deviation = 0)")
                        else:
                            # No negative returns, use volatility as fallback
                            volatility = performance_metrics.get('volatility', 0)
                            if volatility > 0:
                                sortino_ratio = (annual_return - 0.02) / volatility
                                performance_metrics['sortino_ratio'] = sortino_ratio
                                print(f"Sortino fallback to Sharpe: {sortino_ratio}")
                            else:
                                performance_metrics['sortino_ratio'] = 0.0
                                print("Sortino fallback: 0.0 (volatility = 0)")
                    else:
                        performance_metrics['sortino_ratio'] = 0.0
                        print("Sortino ratio: 0.0 (no returns data)")
                else:
                    # Fallback to Sharpe ratio if no returns data
                    performance_metrics['sortino_ratio'] = performance_metrics.get('sharpe_ratio', 0.0)
                    print(f"Sortino fallback to Sharpe: {performance_metrics['sortino_ratio']}")
        except Exception as e:
            print(f"Sortino ratio error: {e}")
            performance_metrics['sortino_ratio'] = 0.0
        
        print(f"\nFinal performance metrics:")
        print(f"  annual_return: {performance_metrics.get('annual_return', 'N/A')}")
        print(f"  volatility: {performance_metrics.get('volatility', 'N/A')}")
        print(f"  sharpe_ratio: {performance_metrics.get('sharpe_ratio', 'N/A')}")
        print(f"  sortino_ratio: {performance_metrics.get('sortino_ratio', 'N/A')}")
        
        # Verify calculations
        self.assertGreater(performance_metrics.get('sharpe_ratio', 0), 0, "Sharpe ratio should be positive")
        self.assertGreater(performance_metrics.get('sortino_ratio', 0), 0, "Sortino ratio should be positive")
        
        print("✅ Mock asset test passed")
    
    def test_zero_values_debugging(self):
        """Test debugging zero values issue"""
        print(f"\n=== Zero Values Debugging ===")
        
        # Test case 1: Zero annual_return
        annual_return = 0.0
        volatility = 0.15
        sharpe = (annual_return - 0.02) / volatility if volatility > 0 else 0.0
        print(f"Case 1 - Zero annual_return: sharpe = {sharpe}")
        
        # Test case 2: Zero volatility
        annual_return = 0.12
        volatility = 0.0
        sharpe = (annual_return - 0.02) / volatility if volatility > 0 else 0.0
        print(f"Case 2 - Zero volatility: sharpe = {sharpe}")
        
        # Test case 3: Both zero
        annual_return = 0.0
        volatility = 0.0
        sharpe = (annual_return - 0.02) / volatility if volatility > 0 else 0.0
        print(f"Case 3 - Both zero: sharpe = {sharpe}")
        
        # Test case 4: Normal values
        annual_return = 0.12
        volatility = 0.15
        sharpe = (annual_return - 0.02) / volatility if volatility > 0 else 0.0
        print(f"Case 4 - Normal values: sharpe = {sharpe}")
        
        # Test case 5: Negative annual_return
        annual_return = -0.05
        volatility = 0.15
        sharpe = (annual_return - 0.02) / volatility if volatility > 0 else 0.0
        print(f"Case 5 - Negative annual_return: sharpe = {sharpe}")


if __name__ == '__main__':
    print("Testing Sharpe and Sortino ratio debugging...")
    print(f"OKAMA_AVAILABLE: {OKAMA_AVAILABLE}")
    
    unittest.main(verbosity=2)
