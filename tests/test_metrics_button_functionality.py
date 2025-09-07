#!/usr/bin/env python3
"""
Test for Metrics button functionality in compare command
Tests the new Metrics button that exports detailed statistics to Excel
"""

import unittest
import sys
import os
import pandas as pd
import io
from unittest.mock import Mock, patch, AsyncMock

# Add the parent directory to the path to import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi

class TestMetricsButtonFunctionality(unittest.TestCase):
    """Test cases for Metrics button functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.bot = ShansAi()
        
        # Create sample data for testing
        self.sample_symbols = ['SPY.US', 'QQQ.US', 'AAPL.US']
        self.sample_currency = 'USD'
        
        # Mock expanded symbols (AssetList items)
        self.mock_expanded_symbols = []
        for symbol in self.sample_symbols:
            mock_asset = Mock()
            mock_asset.close_monthly = pd.Series([100, 105, 110, 108, 115, 120], 
                                               index=pd.date_range('2023-01-01', periods=6, freq='ME'))
            mock_asset.total_return = 0.20
            mock_asset.annual_return = 0.15
            mock_asset.volatility = 0.18
            mock_asset.max_drawdown = -0.12
            mock_asset.sharpe_ratio = 0.72
            mock_asset.sortino_ratio = 1.15
            mock_asset.calmar_ratio = 1.25
            mock_asset.var_95 = -0.08
            mock_asset.cvar_95 = -0.12
            self.mock_expanded_symbols.append(mock_asset)
    
    def test_prepare_comprehensive_metrics(self):
        """Test comprehensive metrics preparation"""
        user_id = 12345
        portfolio_contexts = []
        
        metrics_data = self.bot._prepare_comprehensive_metrics(
            self.sample_symbols, 
            self.sample_currency, 
            self.mock_expanded_symbols, 
            portfolio_contexts, 
            user_id
        )
        
        # Check that metrics data is created
        self.assertIsNotNone(metrics_data)
        self.assertEqual(metrics_data['symbols'], self.sample_symbols)
        self.assertEqual(metrics_data['currency'], self.sample_currency)
        self.assertEqual(metrics_data['asset_count'], len(self.sample_symbols))
        self.assertEqual(metrics_data['analysis_type'], 'metrics_export')
        
        # Check detailed metrics for each symbol
        detailed_metrics = metrics_data.get('detailed_metrics', {})
        self.assertEqual(len(detailed_metrics), len(self.sample_symbols))
        
        for symbol in self.sample_symbols:
            self.assertIn(symbol, detailed_metrics)
            symbol_metrics = detailed_metrics[symbol]
            
            # Check that all required metrics are present
            required_metrics = ['total_return', 'annual_return', 'volatility', 'sharpe_ratio', 'sortino_ratio', 'max_drawdown']
            for metric in required_metrics:
                self.assertIn(metric, symbol_metrics)
                self.assertIsInstance(symbol_metrics[metric], (int, float))
    
    def test_prepare_comprehensive_metrics_with_calculations(self):
        """Test metrics preparation with manual calculations"""
        # Create mock asset without pre-calculated metrics
        mock_asset_no_metrics = Mock()
        mock_asset_no_metrics.close_monthly = pd.Series([100, 105, 110, 108, 115, 120], 
                                                       index=pd.date_range('2023-01-01', periods=6, freq='ME'))
        # Remove pre-calculated metrics
        del mock_asset_no_metrics.total_return
        del mock_asset_no_metrics.annual_return
        del mock_asset_no_metrics.volatility
        del mock_asset_no_metrics.max_drawdown
        del mock_asset_no_metrics.sharpe_ratio
        del mock_asset_no_metrics.sortino_ratio
        
        symbols = ['TEST.US']
        expanded_symbols = [mock_asset_no_metrics]
        
        metrics_data = self.bot._prepare_comprehensive_metrics(
            symbols, 
            self.sample_currency, 
            expanded_symbols, 
            [], 
            12345
        )
        
        # Check that metrics are calculated
        self.assertIsNotNone(metrics_data)
        detailed_metrics = metrics_data.get('detailed_metrics', {})
        self.assertIn('TEST.US', detailed_metrics)
        
        test_metrics = detailed_metrics['TEST.US']
        self.assertIn('total_return', test_metrics)
        self.assertIn('annual_return', test_metrics)
        self.assertIn('volatility', test_metrics)
        self.assertIn('sharpe_ratio', test_metrics)
        self.assertIn('sortino_ratio', test_metrics)
        self.assertIn('max_drawdown', test_metrics)
    
    def test_prepare_comprehensive_metrics_error_handling(self):
        """Test error handling in metrics preparation"""
        # Test with invalid data
        invalid_expanded_symbols = [None, None, None]
        
        metrics_data = self.bot._prepare_comprehensive_metrics(
            self.sample_symbols, 
            self.sample_currency, 
            invalid_expanded_symbols, 
            [], 
            12345
        )
        
        # Should still return data with fallback values
        self.assertIsNotNone(metrics_data)
        detailed_metrics = metrics_data.get('detailed_metrics', {})
        
        for symbol in self.sample_symbols:
            self.assertIn(symbol, detailed_metrics)
            symbol_metrics = detailed_metrics[symbol]
            # All values should be 0.0 for fallback
            self.assertEqual(symbol_metrics['total_return'], 0.0)
            self.assertEqual(symbol_metrics['annual_return'], 0.0)
            self.assertEqual(symbol_metrics['volatility'], 0.0)
            self.assertEqual(symbol_metrics['sharpe_ratio'], 0.0)
            self.assertEqual(symbol_metrics['sortino_ratio'], 0.0)
            self.assertEqual(symbol_metrics['max_drawdown'], 0.0)
    
    @patch('bot.EXCEL_AVAILABLE', True)
    def test_create_metrics_excel_with_openpyxl(self):
        """Test Excel creation with openpyxl available"""
        # Prepare test metrics data
        metrics_data = {
            'symbols': self.sample_symbols,
            'currency': self.sample_currency,
            'detailed_metrics': {
                'SPY.US': {
                    'total_return': 0.20,
                    'annual_return': 0.15,
                    'volatility': 0.18,
                    'sharpe_ratio': 0.72,
                    'sortino_ratio': 1.15,
                    'max_drawdown': -0.12
                },
                'QQQ.US': {
                    'total_return': 0.25,
                    'annual_return': 0.18,
                    'volatility': 0.22,
                    'sharpe_ratio': 0.73,
                    'sortino_ratio': 1.20,
                    'max_drawdown': -0.15
                },
                'AAPL.US': {
                    'total_return': 0.30,
                    'annual_return': 0.20,
                    'volatility': 0.25,
                    'sharpe_ratio': 0.72,
                    'sortino_ratio': 1.18,
                    'max_drawdown': -0.18
                }
            },
            'correlations': [
                [1.0, 0.8, 0.7],
                [0.8, 1.0, 0.6],
                [0.7, 0.6, 1.0]
            ],
            'timestamp': '2025-09-07 21:00:00',
            'period': 'полный доступный период данных'
        }
        
        excel_buffer = self.bot._create_metrics_excel(metrics_data, self.sample_symbols, self.sample_currency)
        
        # Check that Excel buffer is created
        self.assertIsNotNone(excel_buffer)
        self.assertGreater(len(excel_buffer.getvalue()), 0)
        
        # Check that it's a valid Excel file (starts with PK signature)
        excel_bytes = excel_buffer.getvalue()
        self.assertTrue(excel_bytes.startswith(b'PK'))
    
    @patch('bot.EXCEL_AVAILABLE', False)
    def test_create_metrics_excel_fallback_csv(self):
        """Test Excel creation fallback to CSV when openpyxl not available"""
        # Prepare test metrics data
        metrics_data = {
            'symbols': self.sample_symbols,
            'currency': self.sample_currency,
            'detailed_metrics': {
                'SPY.US': {
                    'total_return': 0.20,
                    'annual_return': 0.15,
                    'volatility': 0.18,
                    'sharpe_ratio': 0.72,
                    'sortino_ratio': 1.15,
                    'max_drawdown': -0.12
                }
            },
            'correlations': [],
            'timestamp': '2025-09-07 21:00:00',
            'period': 'полный доступный период данных'
        }
        
        excel_buffer = self.bot._create_metrics_excel(metrics_data, self.sample_symbols, self.sample_currency)
        
        # Check that CSV buffer is created
        self.assertIsNotNone(excel_buffer)
        csv_content = excel_buffer.getvalue().decode('utf-8')
        
        # Check that CSV contains expected content
        self.assertIn('SUMMARY', csv_content)
        self.assertIn('DETAILED METRICS', csv_content)
        self.assertIn('SPY.US', csv_content)
        self.assertIn('Sharpe Ratio', csv_content)
        self.assertIn('Sortino Ratio', csv_content)
    
    def test_create_metrics_excel_error_handling(self):
        """Test error handling in Excel creation"""
        # Test with invalid metrics data
        invalid_metrics_data = None
        
        excel_buffer = self.bot._create_metrics_excel(invalid_metrics_data, self.sample_symbols, self.sample_currency)
        
        # Should return None for invalid data
        self.assertIsNone(excel_buffer)
    
    @patch('bot.EXCEL_AVAILABLE', True)
    def test_excel_content_structure(self):
        """Test Excel file content structure"""
        metrics_data = {
            'symbols': ['SPY.US', 'QQQ.US'],
            'currency': 'USD',
            'detailed_metrics': {
                'SPY.US': {
                    'total_return': 0.20,
                    'annual_return': 0.15,
                    'volatility': 0.18,
                    'sharpe_ratio': 0.72,
                    'sortino_ratio': 1.15,
                    'max_drawdown': -0.12,
                    'calmar_ratio': 1.25,
                    'var_95': -0.08,
                    'cvar_95': -0.12
                },
                'QQQ.US': {
                    'total_return': 0.25,
                    'annual_return': 0.18,
                    'volatility': 0.22,
                    'sharpe_ratio': 0.73,
                    'sortino_ratio': 1.20,
                    'max_drawdown': -0.15,
                    'calmar_ratio': 1.20,
                    'var_95': -0.10,
                    'cvar_95': -0.15
                }
            },
            'correlations': [
                [1.0, 0.8],
                [0.8, 1.0]
            ],
            'timestamp': '2025-09-07 21:00:00',
            'period': 'полный доступный период данных'
        }
        
        excel_buffer = self.bot._create_metrics_excel(metrics_data, ['SPY.US', 'QQQ.US'], 'USD')
        
        # Check that Excel buffer is created
        self.assertIsNotNone(excel_buffer)
        excel_bytes = excel_buffer.getvalue()
        self.assertGreater(len(excel_bytes), 0)
        
        # Verify it's a valid Excel file
        self.assertTrue(excel_bytes.startswith(b'PK'))

if __name__ == '__main__':
    unittest.main()
