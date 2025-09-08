#!/usr/bin/env python3
"""
Simple test for Metrics button fix - Detailed Metrics values
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

class TestMetricsButtonFixSimple(unittest.TestCase):
    """Simple test cases for Metrics button fix"""
    
    def setUp(self):
        """Set up test environment"""
        self.bot = ShansAi()
    
    def test_prepare_comprehensive_metrics_basic(self):
        """Test basic metrics preparation"""
        symbols = ['SPY.US', 'QQQ.US']
        currency = 'USD'
        expanded_symbols = []  # Not used anymore
        portfolio_contexts = [
            {
                'symbol': 'SPY.US',
                'portfolio_symbols': ['SPY.US'],
                'portfolio_weights': [1.0],
                'portfolio_currency': 'USD',
                'portfolio_object': None
            },
            {
                'symbol': 'QQQ.US',
                'portfolio_symbols': ['QQQ.US'],
                'portfolio_weights': [1.0],
                'portfolio_currency': 'USD',
                'portfolio_object': None
            }
        ]
        user_id = 12345
        
        # Mock ok.Asset to return objects with data
        with patch('bot.ok.Asset') as mock_asset_class:
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
            
            mock_qqq = Mock()
            mock_qqq.close_monthly = pd.Series([100, 110, 115, 112, 120, 125], 
                                             index=pd.date_range('2023-01-01', periods=6, freq='ME'))
            mock_qqq.total_return = 0.25
            mock_qqq.annual_return = 0.18
            mock_qqq.volatility = 0.22
            mock_qqq.max_drawdown = -0.15
            mock_qqq.sharpe_ratio = 0.73
            mock_qqq.sortino_ratio = 1.20
            
            # Configure mock to return appropriate Asset objects
            def asset_side_effect(symbol, ccy=None):
                if symbol == 'SPY.US':
                    return mock_spy
                elif symbol == 'QQQ.US':
                    return mock_qqq
                else:
                    return Mock()
            
            mock_asset_class.side_effect = asset_side_effect
            
            metrics_data = self.bot._prepare_comprehensive_metrics(
                symbols, currency, expanded_symbols, portfolio_contexts, user_id
            )
            
            # Check that metrics data is created
            self.assertIsNotNone(metrics_data)
            self.assertEqual(metrics_data['symbols'], symbols)
            self.assertEqual(metrics_data['currency'], currency)
            
            # Check detailed metrics for each symbol
            detailed_metrics = metrics_data.get('detailed_metrics', {})
            self.assertEqual(len(detailed_metrics), len(symbols))
            
            # Check SPY.US metrics
            spy_metrics = detailed_metrics.get('SPY.US', {})
            self.assertIn('total_return', spy_metrics)
            self.assertIn('annual_return', spy_metrics)
            self.assertIn('volatility', spy_metrics)
            self.assertIn('sharpe_ratio', spy_metrics)
            self.assertIn('sortino_ratio', spy_metrics)
            self.assertIn('max_drawdown', spy_metrics)
            
            # Check that values are not zero (should be actual values from mock)
            self.assertEqual(spy_metrics['total_return'], 0.20)
            self.assertEqual(spy_metrics['annual_return'], 0.15)
            self.assertEqual(spy_metrics['volatility'], 0.18)
            self.assertEqual(spy_metrics['sharpe_ratio'], 0.72)
            self.assertEqual(spy_metrics['sortino_ratio'], 1.15)
            self.assertEqual(spy_metrics['max_drawdown'], -0.12)
            
            # Check QQQ.US metrics
            qqq_metrics = detailed_metrics.get('QQQ.US', {})
            self.assertIn('total_return', qqq_metrics)
            self.assertIn('annual_return', qqq_metrics)
            self.assertIn('volatility', qqq_metrics)
            self.assertIn('sharpe_ratio', qqq_metrics)
            self.assertIn('sortino_ratio', qqq_metrics)
            self.assertIn('max_drawdown', qqq_metrics)
            
            # Check that values are not zero (should be actual values from mock)
            self.assertEqual(qqq_metrics['total_return'], 0.25)
            self.assertEqual(qqq_metrics['annual_return'], 0.18)
            self.assertEqual(qqq_metrics['volatility'], 0.22)
            self.assertEqual(qqq_metrics['sharpe_ratio'], 0.73)
            self.assertEqual(qqq_metrics['sortino_ratio'], 1.20)
            self.assertEqual(qqq_metrics['max_drawdown'], -0.15)
    
    def test_prepare_comprehensive_metrics_with_portfolio_object(self):
        """Test metrics preparation with Portfolio object"""
        symbols = ['PORTFOLIO.US']
        currency = 'USD'
        expanded_symbols = []  # Not used anymore
        
        # Create mock Portfolio object
        mock_portfolio = Mock()
        mock_portfolio.wealth_index = pd.Series([100, 105, 110, 108, 115, 120], 
                                               index=pd.date_range('2023-01-01', periods=6, freq='ME'))
        mock_portfolio.total_return = 0.20
        mock_portfolio.annual_return = 0.15
        mock_portfolio.volatility = 0.18
        mock_portfolio.max_drawdown = -0.12
        mock_portfolio.sharpe_ratio = 0.72
        mock_portfolio.sortino_ratio = 1.15
        
        portfolio_contexts = [
            {
                'symbol': 'PORTFOLIO.US',
                'portfolio_symbols': ['SPY.US', 'QQQ.US'],
                'portfolio_weights': [0.6, 0.4],
                'portfolio_currency': 'USD',
                'portfolio_object': mock_portfolio
            }
        ]
        user_id = 12345
        
        metrics_data = self.bot._prepare_comprehensive_metrics(
            symbols, currency, expanded_symbols, portfolio_contexts, user_id
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
        
        # Check that values are not zero (should be actual values from mock)
        self.assertEqual(portfolio_metrics['total_return'], 0.20)
        self.assertEqual(portfolio_metrics['annual_return'], 0.15)
        self.assertEqual(portfolio_metrics['volatility'], 0.18)
        self.assertEqual(portfolio_metrics['sharpe_ratio'], 0.72)
        self.assertEqual(portfolio_metrics['sortino_ratio'], 1.15)
        self.assertEqual(portfolio_metrics['max_drawdown'], -0.12)
    
    def test_prepare_comprehensive_metrics_error_handling(self):
        """Test error handling in metrics preparation"""
        symbols = ['INVALID.US']
        currency = 'USD'
        expanded_symbols = []  # Not used anymore
        portfolio_contexts = [
            {
                'symbol': 'INVALID.US',
                'portfolio_symbols': ['INVALID.US'],
                'portfolio_weights': [1.0],
                'portfolio_currency': 'USD',
                'portfolio_object': None
            }
        ]
        user_id = 12345
        
        # Mock ok.Asset to raise exception
        with patch('bot.ok.Asset', side_effect=Exception("Asset not found")):
            metrics_data = self.bot._prepare_comprehensive_metrics(
                symbols, currency, expanded_symbols, portfolio_contexts, user_id
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

