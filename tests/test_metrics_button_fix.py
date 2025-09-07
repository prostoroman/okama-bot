#!/usr/bin/env python3
"""
Test for Metrics button fix - Detailed Metrics values
Tests that the Metrics button now returns actual values instead of zeros
"""

import unittest
import sys
import os
import pandas as pd
import io
from unittest.mock import Mock, patch

# Add the parent directory to the path to import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi

class TestMetricsButtonFix(unittest.TestCase):
    """Test cases for Metrics button fix - ensuring actual values are returned"""
    
    def setUp(self):
        """Set up test environment"""
        self.bot = ShansAi()
        
        # Create sample data for testing
        self.sample_symbols = ['SPY.US', 'QQQ.US']
        self.sample_currency = 'USD'
        
        # Create portfolio contexts that simulate real data
        self.portfolio_contexts = [
            {
                'symbol': 'SPY.US',
                'portfolio_symbols': ['SPY.US'],
                'portfolio_weights': [1.0],
                'portfolio_currency': 'USD',
                'portfolio_object': None  # Will be created in test
            },
            {
                'symbol': 'QQQ.US',
                'portfolio_symbols': ['QQQ.US'],
                'portfolio_weights': [1.0],
                'portfolio_currency': 'USD',
                'portfolio_object': None  # Will be created in test
            }
        ]
    
    @patch('bot.ok.Asset')
    def test_prepare_comprehensive_metrics_with_real_assets(self, mock_asset_class):
        """Test metrics preparation with real Asset objects"""
        # Create mock Asset objects with real data
        mock_spy = Mock()
        mock_spy.close_monthly = pd.Series([100, 105, 110, 108, 115, 120], 
                                         index=pd.date_range('2023-01-01', periods=6, freq='ME'))
        mock_spy.total_return = 0.20
        mock_spy.annual_return = 0.15
        mock_spy.volatility = 0.18
        mock_spy.max_drawdown = -0.12
        mock_spy.sharpe_ratio = 0.72
        mock_spy.sortino_ratio = 1.15
        mock_spy.calmar_ratio = 1.25
        mock_spy.var_95 = -0.08
        mock_spy.cvar_95 = -0.12
        
        mock_qqq = Mock()
        mock_qqq.close_monthly = pd.Series([100, 110, 115, 112, 120, 125], 
                                         index=pd.date_range('2023-01-01', periods=6, freq='ME'))
        mock_qqq.total_return = 0.25
        mock_qqq.annual_return = 0.18
        mock_qqq.volatility = 0.22
        mock_qqq.max_drawdown = -0.15
        mock_qqq.sharpe_ratio = 0.73
        mock_qqq.sortino_ratio = 1.20
        mock_qqq.calmar_ratio = 1.20
        mock_qqq.var_95 = -0.10
        mock_qqq.cvar_95 = -0.15
        
        # Configure mock to return appropriate Asset objects
        def asset_side_effect(symbol, ccy=None):
            if symbol == 'SPY.US':
                return mock_spy
            elif symbol == 'QQQ.US':
                return mock_qqq
            else:
                return Mock()
        
        mock_asset_class.side_effect = asset_side_effect
        
        # Update portfolio contexts with mock objects
        self.portfolio_contexts[0]['portfolio_object'] = mock_spy
        self.portfolio_contexts[1]['portfolio_object'] = mock_qqq
        
        user_id = 12345
        
        metrics_data = self.bot._prepare_comprehensive_metrics(
            self.sample_symbols, 
            self.sample_currency, 
            [],  # expanded_symbols not used anymore
            self.portfolio_contexts, 
            user_id
        )
        
        # Check that metrics data is created
        self.assertIsNotNone(metrics_data)
        self.assertEqual(metrics_data['symbols'], self.sample_symbols)
        self.assertEqual(metrics_data['currency'], self.sample_currency)
        
        # Check detailed metrics for each symbol
        detailed_metrics = metrics_data.get('detailed_metrics', {})
        self.assertEqual(len(detailed_metrics), len(self.sample_symbols))
        
        # Check SPY.US metrics
        spy_metrics = detailed_metrics.get('SPY.US', {})
        self.assertIn('total_return', spy_metrics)
        self.assertIn('annual_return', spy_metrics)
        self.assertIn('volatility', spy_metrics)
        self.assertIn('sharpe_ratio', spy_metrics)
        self.assertIn('sortino_ratio', spy_metrics)
        self.assertIn('max_drawdown', spy_metrics)
        
        # Check that values are not zero (should be actual values)
        self.assertNotEqual(spy_metrics['total_return'], 0.0)
        self.assertNotEqual(spy_metrics['annual_return'], 0.0)
        self.assertNotEqual(spy_metrics['volatility'], 0.0)
        self.assertNotEqual(spy_metrics['sharpe_ratio'], 0.0)
        self.assertNotEqual(spy_metrics['sortino_ratio'], 0.0)
        self.assertNotEqual(spy_metrics['max_drawdown'], 0.0)
        
        # Check QQQ.US metrics
        qqq_metrics = detailed_metrics.get('QQQ.US', {})
        self.assertIn('total_return', qqq_metrics)
        self.assertIn('annual_return', qqq_metrics)
        self.assertIn('volatility', qqq_metrics)
        self.assertIn('sharpe_ratio', qqq_metrics)
        self.assertIn('sortino_ratio', qqq_metrics)
        self.assertIn('max_drawdown', qqq_metrics)
        
        # Check that values are not zero (should be actual values)
        self.assertNotEqual(qqq_metrics['total_return'], 0.0)
        self.assertNotEqual(qqq_metrics['annual_return'], 0.0)
        self.assertNotEqual(qqq_metrics['volatility'], 0.0)
        self.assertNotEqual(qqq_metrics['sharpe_ratio'], 0.0)
        self.assertNotEqual(qqq_metrics['sortino_ratio'], 0.0)
        self.assertNotEqual(qqq_metrics['max_drawdown'], 0.0)
    
    @patch('bot.ok.Asset')
    def test_prepare_comprehensive_metrics_with_portfolio_objects(self, mock_asset_class):
        """Test metrics preparation with Portfolio objects"""
        # Create mock Portfolio objects
        mock_portfolio = Mock()
        mock_portfolio.wealth_index = pd.Series([100, 105, 110, 108, 115, 120], 
                                               index=pd.date_range('2023-01-01', periods=6, freq='ME'))
        mock_portfolio.total_return = 0.20
        mock_portfolio.annual_return = 0.15
        mock_portfolio.volatility = 0.18
        mock_portfolio.max_drawdown = -0.12
        mock_portfolio.sharpe_ratio = 0.72
        mock_portfolio.sortino_ratio = 1.15
        mock_portfolio.calmar_ratio = 1.25
        mock_portfolio.var_95 = -0.08
        mock_portfolio.cvar_95 = -0.12
        
        # Configure mock to return Portfolio object
        mock_asset_class.return_value = mock_portfolio
        
        # Update portfolio contexts with portfolio object
        portfolio_contexts = [
            {
                'symbol': 'PORTFOLIO.US',
                'portfolio_symbols': ['SPY.US', 'QQQ.US'],
                'portfolio_weights': [0.6, 0.4],
                'portfolio_currency': 'USD',
                'portfolio_object': mock_portfolio
            }
        ]
        
        symbols = ['PORTFOLIO.US']
        user_id = 12345
        
        metrics_data = self.bot._prepare_comprehensive_metrics(
            symbols, 
            self.sample_currency, 
            [],  # expanded_symbols not used anymore
            portfolio_contexts, 
            user_id
        )
        
        # Check that metrics data is created
        self.assertIsNotNone(metrics_data)
        
        # Check detailed metrics
        detailed_metrics = metrics_data.get('detailed_metrics', {})
        self.assertEqual(len(detailed_metrics), len(symbols))
        
        # Check portfolio metrics
        portfolio_metrics = detailed_metrics.get('PORTFOLIO.US', {})
        self.assertIn('total_return', portfolio_metrics)
        self.assertIn('annual_return', portfolio_metrics)
        self.assertIn('volatility', portfolio_metrics)
        self.assertIn('sharpe_ratio', portfolio_metrics)
        self.assertIn('sortino_ratio', portfolio_metrics)
        self.assertIn('max_drawdown', portfolio_metrics)
        
        # Check that values are not zero (should be actual values)
        self.assertNotEqual(portfolio_metrics['total_return'], 0.0)
        self.assertNotEqual(portfolio_metrics['annual_return'], 0.0)
        self.assertNotEqual(portfolio_metrics['volatility'], 0.0)
        self.assertNotEqual(portfolio_metrics['sharpe_ratio'], 0.0)
        self.assertNotEqual(portfolio_metrics['sortino_ratio'], 0.0)
        self.assertNotEqual(portfolio_metrics['max_drawdown'], 0.0)
    
    @patch('bot.ok.Asset')
    @patch('bot.ok.AssetList')
    def test_correlation_matrix_calculation(self, mock_asset_list_class, mock_asset_class):
        """Test correlation matrix calculation"""
        # Create mock AssetList for correlation calculation
        mock_asset_list = Mock()
        mock_correlation_matrix = pd.DataFrame([
            [1.0, 0.8],
            [0.8, 1.0]
        ], index=['SPY.US', 'QQQ.US'], columns=['SPY.US', 'QQQ.US'])
        mock_asset_list.correlation_matrix = mock_correlation_matrix
        mock_asset_list_class.return_value = mock_asset_list
        
        # Create mock Asset objects
        mock_spy = Mock()
        mock_spy.close_monthly = pd.Series([100, 105, 110, 108, 115, 120], 
                                         index=pd.date_range('2023-01-01', periods=6, freq='ME'))
        mock_qqq = Mock()
        mock_qqq.close_monthly = pd.Series([100, 110, 115, 112, 120, 125], 
                                         index=pd.date_range('2023-01-01', periods=6, freq='ME'))
        
        def asset_side_effect(symbol, ccy=None):
            if symbol == 'SPY.US':
                return mock_spy
            elif symbol == 'QQQ.US':
                return mock_qqq
            else:
                return Mock()
        
        mock_asset_class.side_effect = asset_side_effect
        
        # Update portfolio contexts
        self.portfolio_contexts[0]['portfolio_object'] = mock_spy
        self.portfolio_contexts[1]['portfolio_object'] = mock_qqq
        
        user_id = 12345
        
        metrics_data = self.bot._prepare_comprehensive_metrics(
            self.sample_symbols, 
            self.sample_currency, 
            [],  # expanded_symbols not used anymore
            self.portfolio_contexts, 
            user_id
        )
        
        # Check that correlation matrix is calculated
        self.assertIsNotNone(metrics_data)
        correlations = metrics_data.get('correlations', [])
        self.assertIsInstance(correlations, list)
        self.assertEqual(len(correlations), len(self.sample_symbols))
        
        # Check that correlation matrix has proper values
        for i, row in enumerate(correlations):
            self.assertEqual(len(row), len(self.sample_symbols))
            for j, value in enumerate(row):
                if i == j:
                    self.assertEqual(value, 1.0)  # Diagonal should be 1.0
                else:
                    self.assertIsInstance(value, (int, float))
                    self.assertGreaterEqual(value, -1.0)
                    self.assertLessEqual(value, 1.0)
    
    def test_prepare_comprehensive_metrics_error_handling(self):
        """Test error handling in metrics preparation"""
        # Test with invalid portfolio contexts
        invalid_portfolio_contexts = [
            {
                'symbol': 'INVALID.US',
                'portfolio_symbols': ['INVALID.US'],
                'portfolio_weights': [1.0],
                'portfolio_currency': 'USD',
                'portfolio_object': None
            }
        ]
        
        symbols = ['INVALID.US']
        user_id = 12345
        
        metrics_data = self.bot._prepare_comprehensive_metrics(
            symbols, 
            self.sample_currency, 
            [],  # expanded_symbols not used anymore
            invalid_portfolio_contexts, 
            user_id
        )
        
        # Should still return data with fallback values
        self.assertIsNotNone(metrics_data)
        detailed_metrics = metrics_data.get('detailed_metrics', {})
        
        for symbol in symbols:
            self.assertIn(symbol, detailed_metrics)
            symbol_metrics = detailed_metrics[symbol]
            # All values should be 0.0 for fallback
            self.assertEqual(symbol_metrics['total_return'], 0.0)
            self.assertEqual(symbol_metrics['annual_return'], 0.0)
            self.assertEqual(symbol_metrics['volatility'], 0.0)
            self.assertEqual(symbol_metrics['sharpe_ratio'], 0.0)
            self.assertEqual(symbol_metrics['sortino_ratio'], 0.0)
            self.assertEqual(symbol_metrics['max_drawdown'], 0.0)

if __name__ == '__main__':
    unittest.main()
