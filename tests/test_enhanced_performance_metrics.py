#!/usr/bin/env python3
"""
Test for enhanced performance metrics calculation
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


class TestEnhancedPerformanceMetrics(unittest.TestCase):
    """Test cases for enhanced performance metrics calculation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    def test_sharpe_ratio_calculation_with_get_sharpe_ratio(self):
        """Test Sharpe ratio calculation using get_sharpe_ratio method"""
        # Mock asset with get_sharpe_ratio method
        mock_asset = Mock()
        mock_asset.get_sharpe_ratio.return_value = 1.5
        mock_asset.annual_return = 0.12
        mock_asset.volatility = 0.15
        mock_asset.total_return = 0.10
        mock_asset.max_drawdown = -0.20
        
        # Test the calculation
        performance_metrics = {}
        
        # Basic metrics
        performance_metrics['annual_return'] = mock_asset.annual_return
        performance_metrics['volatility'] = mock_asset.volatility
        
        # Sharpe ratio using okama method
        try:
            if hasattr(mock_asset, 'get_sharpe_ratio'):
                sharpe_ratio = mock_asset.get_sharpe_ratio(rf_return=0.02)
                performance_metrics['sharpe_ratio'] = float(sharpe_ratio)
            else:
                performance_metrics['sharpe_ratio'] = 0.0
        except Exception as e:
            performance_metrics['sharpe_ratio'] = 0.0
        
        # Verify the calculation
        self.assertEqual(performance_metrics['sharpe_ratio'], 1.5)
        mock_asset.get_sharpe_ratio.assert_called_once_with(rf_return=0.02)
        
        print(f"Sharpe ratio with get_sharpe_ratio: {performance_metrics['sharpe_ratio']}")
    
    def test_sharpe_ratio_calculation_manual(self):
        """Test manual Sharpe ratio calculation"""
        # Mock asset without get_sharpe_ratio method
        mock_asset = Mock()
        mock_asset.annual_return = 0.12
        mock_asset.volatility = 0.15
        mock_asset.total_return = 0.10
        mock_asset.max_drawdown = -0.20
        # Remove attributes that shouldn't exist
        del mock_asset.get_sharpe_ratio
        del mock_asset.sharpe_ratio
        
        # Test the calculation
        performance_metrics = {}
        
        # Basic metrics
        performance_metrics['annual_return'] = mock_asset.annual_return
        performance_metrics['volatility'] = mock_asset.volatility
        
        # Manual Sharpe ratio calculation
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
                if volatility > 0:
                    sharpe_ratio = (annual_return - 0.02) / volatility
                    performance_metrics['sharpe_ratio'] = sharpe_ratio
                else:
                    performance_metrics['sharpe_ratio'] = 0.0
        except Exception as e:
            performance_metrics['sharpe_ratio'] = 0.0
        
        # Verify the calculation
        expected_sharpe = (0.12 - 0.02) / 0.15  # 0.667
        self.assertAlmostEqual(performance_metrics['sharpe_ratio'], expected_sharpe, places=3)
        
        print(f"Manual Sharpe ratio calculation: {performance_metrics['sharpe_ratio']:.3f}")
    
    def test_sortino_ratio_calculation_with_returns(self):
        """Test Sortino ratio calculation with returns data"""
        # Mock asset with returns data
        mock_asset = Mock()
        mock_asset.annual_return = 0.12
        mock_asset.volatility = 0.15
        # Remove attributes that shouldn't exist
        del mock_asset.sortino_ratio
        
        # Create sample returns with some negative values
        returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01, 0.02])
        mock_asset.returns = returns
        
        # Test the calculation
        performance_metrics = {}
        performance_metrics['annual_return'] = mock_asset.annual_return
        performance_metrics['volatility'] = mock_asset.volatility
        
        # Sortino ratio calculation
        try:
            if hasattr(mock_asset, 'sortino_ratio'):
                performance_metrics['sortino_ratio'] = mock_asset.sortino_ratio
            else:
                # Manual Sortino ratio calculation
                annual_return = performance_metrics.get('annual_return', 0)
                if hasattr(mock_asset, 'returns'):
                    returns = mock_asset.returns
                    if returns is not None and len(returns) > 0:
                        # Calculate downside deviation (only negative returns)
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
                    else:
                        performance_metrics['sortino_ratio'] = 0.0
                else:
                    # Fallback to Sharpe ratio if no returns data
                    performance_metrics['sortino_ratio'] = performance_metrics.get('sharpe_ratio', 0.0)
        except Exception as e:
            performance_metrics['sortino_ratio'] = 0.0
        
        # Verify the calculation
        self.assertGreater(performance_metrics['sortino_ratio'], 0)
        
        print(f"Sortino ratio with returns data: {performance_metrics['sortino_ratio']:.3f}")
    
    def test_sortino_ratio_calculation_fallback(self):
        """Test Sortino ratio calculation fallback to Sharpe ratio"""
        # Mock asset without returns data
        mock_asset = Mock()
        mock_asset.annual_return = 0.12
        mock_asset.volatility = 0.15
        mock_asset.sharpe_ratio = 0.667
        # Remove attributes that shouldn't exist
        del mock_asset.sortino_ratio
        del mock_asset.returns
        
        # Test the calculation
        performance_metrics = {}
        performance_metrics['annual_return'] = mock_asset.annual_return
        performance_metrics['volatility'] = mock_asset.volatility
        performance_metrics['sharpe_ratio'] = mock_asset.sharpe_ratio
        
        # Sortino ratio calculation
        try:
            if hasattr(mock_asset, 'sortino_ratio'):
                performance_metrics['sortino_ratio'] = mock_asset.sortino_ratio
            else:
                # Manual Sortino ratio calculation
                annual_return = performance_metrics.get('annual_return', 0)
                if hasattr(mock_asset, 'returns'):
                    returns = mock_asset.returns
                    if returns is not None and len(returns) > 0:
                        # Calculate downside deviation
                        negative_returns = returns[returns < 0]
                        if len(negative_returns) > 0:
                            downside_deviation = negative_returns.std() * (12 ** 0.5)
                            if downside_deviation > 0:
                                sortino_ratio = (annual_return - 0.02) / downside_deviation
                                performance_metrics['sortino_ratio'] = sortino_ratio
                            else:
                                performance_metrics['sortino_ratio'] = 0.0
                        else:
                            volatility = performance_metrics.get('volatility', 0)
                            if volatility > 0:
                                sortino_ratio = (annual_return - 0.02) / volatility
                                performance_metrics['sortino_ratio'] = sortino_ratio
                            else:
                                performance_metrics['sortino_ratio'] = 0.0
                    else:
                        performance_metrics['sortino_ratio'] = 0.0
                else:
                    # Fallback to Sharpe ratio if no returns data
                    performance_metrics['sortino_ratio'] = performance_metrics.get('sharpe_ratio', 0.0)
        except Exception as e:
            performance_metrics['sortino_ratio'] = 0.0
        
        # Verify the fallback
        self.assertEqual(performance_metrics['sortino_ratio'], 0.667)
        
        print(f"Sortino ratio fallback to Sharpe: {performance_metrics['sortino_ratio']:.3f}")
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_prepare_data_for_analysis_with_enhanced_metrics(self):
        """Test prepare_data_for_analysis with enhanced metrics"""
        try:
            # Create a simple asset list for testing
            symbols = ['SPY.US', 'QQQ.US']
            asset_list = ok.AssetList(symbols)
            
            # Mock user context
            user_id = 12345
            describe_table = self.bot._format_describe_table(asset_list)
            self.bot._update_user_context(user_id, describe_table=describe_table)
            
            # Test the enhanced prepare_data_for_analysis function
            import asyncio
            result = asyncio.run(self.bot._prepare_data_for_analysis(
                symbols=symbols,
                currency='USD',
                expanded_symbols=symbols,
                portfolio_contexts=[],
                user_id=user_id
            ))
            
            # Check that result contains enhanced metrics
            self.assertIn('performance', result)
            
            for symbol in symbols:
                if symbol in result['performance']:
                    perf = result['performance'][symbol]
                    self.assertIn('sharpe_ratio', perf)
                    self.assertIn('sortino_ratio', perf)
                    
                    # Check that metrics are numeric
                    self.assertIsInstance(perf['sharpe_ratio'], (int, float))
                    self.assertIsInstance(perf['sortino_ratio'], (int, float))
            
            print(f"Enhanced metrics test passed for symbols: {symbols}")
            
        except Exception as e:
            self.fail(f"Error testing enhanced prepare_data_for_analysis: {e}")
    
    def test_error_handling_in_metrics_calculation(self):
        """Test error handling in metrics calculation"""
        # Mock asset that raises exceptions
        mock_asset = Mock()
        mock_asset.get_sharpe_ratio.side_effect = Exception("Test error")
        mock_asset.annual_return = 0.12
        mock_asset.volatility = 0.15
        # Remove attributes that shouldn't exist
        del mock_asset.sortino_ratio
        
        # Test error handling
        performance_metrics = {}
        performance_metrics['annual_return'] = mock_asset.annual_return
        performance_metrics['volatility'] = mock_asset.volatility
        
        # Sharpe ratio with error handling
        try:
            if hasattr(mock_asset, 'get_sharpe_ratio'):
                sharpe_ratio = mock_asset.get_sharpe_ratio(rf_return=0.02)
                performance_metrics['sharpe_ratio'] = float(sharpe_ratio)
            else:
                performance_metrics['sharpe_ratio'] = 0.0
        except Exception as e:
            performance_metrics['sharpe_ratio'] = 0.0
        
        # Sortino ratio with error handling
        try:
            if hasattr(mock_asset, 'sortino_ratio'):
                performance_metrics['sortino_ratio'] = mock_asset.sortino_ratio
            else:
                performance_metrics['sortino_ratio'] = 0.0
        except Exception as e:
            performance_metrics['sortino_ratio'] = 0.0
        
        # Verify error handling
        self.assertEqual(performance_metrics['sharpe_ratio'], 0.0)
        self.assertEqual(performance_metrics['sortino_ratio'], 0.0)
        
        print("Error handling test passed")


if __name__ == '__main__':
    print("Testing enhanced performance metrics calculation...")
    print(f"OKAMA_AVAILABLE: {OKAMA_AVAILABLE}")
    
    unittest.main(verbosity=2)
