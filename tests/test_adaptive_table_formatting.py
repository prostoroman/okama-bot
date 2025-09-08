#!/usr/bin/env python3
"""
Test for adaptive table formatting in compare command
Tests the improved adaptive table formatting for different numbers of assets
"""

import unittest
import sys
import os
import pandas as pd
from unittest.mock import Mock, patch

# Add the parent directory to the path to import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi

class TestAdaptiveTableFormatting(unittest.TestCase):
    """Test cases for adaptive table formatting based on number of assets"""
    
    def setUp(self):
        """Set up test environment"""
        self.bot = ShansAi()
        
        # Create sample data for different scenarios
        self.create_test_data()
    
    def create_test_data(self):
        """Create test data for different scenarios"""
        
        # Scenario 1: 2 assets (should use pipe format)
        self.data_2_assets = {
            'SPY.US': [0.08, 0.16, 0.14, 0.09, 0.01, 0.17, -0.51],
            'QQQ.US': [0.11, 0.21, 0.18, 0.13, 0.00, 0.27, -0.81]
        }
        
        # Scenario 2: 4 assets (should use simple format)
        self.data_4_assets = {
            'SPY.US': [0.08, 0.16, 0.14, 0.09, 0.01, 0.17, -0.51],
            'QQQ.US': [0.11, 0.21, 0.18, 0.13, 0.00, 0.27, -0.81],
            'AAPL.US': [0.12, 0.22, 0.19, 0.14, 0.01, 0.25, -0.45],
            'MSFT.US': [0.10, 0.20, 0.17, 0.12, 0.01, 0.23, -0.40]
        }
        
        # Scenario 3: 6 assets (should use vertical format)
        self.data_6_assets = {
            'SPY.US': [0.08, 0.16, 0.14, 0.09, 0.01, 0.17, -0.51],
            'QQQ.US': [0.11, 0.21, 0.18, 0.13, 0.00, 0.27, -0.81],
            'AAPL.US': [0.12, 0.22, 0.19, 0.14, 0.01, 0.25, -0.45],
            'MSFT.US': [0.10, 0.20, 0.17, 0.12, 0.01, 0.23, -0.40],
            'GOOGL.US': [0.13, 0.23, 0.20, 0.15, 0.00, 0.26, -0.50],
            'AMZN.US': [0.09, 0.19, 0.16, 0.11, 0.00, 0.24, -0.35]
        }
        
        self.index = [
            'Compound return',
            'CAGR (1Y)',
            'CAGR (5Y)', 
            'Annualized mean return',
            'Dividend yield',
            'Risk',
            'Max drawdowns'
        ]
    
    def test_2_assets_pipe_format(self):
        """Test pipe format for 2 assets"""
        with patch('bot.TABULATE_AVAILABLE', True):
            with patch('bot.tabulate') as mock_tabulate:
                # Mock asset list
                mock_asset_list = Mock()
                df_2 = pd.DataFrame(self.data_2_assets, index=self.index)
                mock_asset_list.describe.return_value = df_2
                
                # Mock tabulate.tabulate to return a formatted table
                mock_tabulate.tabulate.return_value = """|                        |   SPY.US |   QQQ.US |
|:-----------------------|---------:|---------:|
| Compound return        |     0.08 |     0.11 |"""
                
                result = self.bot._format_describe_table(mock_asset_list)
                
                # Check that tabulate was called with pipe format
                mock_tabulate.tabulate.assert_called_once_with(
                    df_2,
                    headers='keys',
                    tablefmt='pipe',
                    floatfmt='.2f'
                )
                
                # Check that result contains expected formatting
                self.assertIn("📊 **Статистика активов:**", result)
                self.assertIn("```", result)
                self.assertIn("|   SPY.US |", result)
    
    def test_4_assets_simple_format(self):
        """Test simple format for 4 assets"""
        with patch('bot.TABULATE_AVAILABLE', True):
            with patch('bot.tabulate') as mock_tabulate:
                # Mock asset list
                mock_asset_list = Mock()
                df_4 = pd.DataFrame(self.data_4_assets, index=self.index)
                mock_asset_list.describe.return_value = df_4
                
                # Mock tabulate.tabulate to return a formatted table
                mock_tabulate.tabulate.return_value = """                          SPY.US    QQQ.US    AAPL.US    MSFT.US
----------------------  --------  --------  ---------  ---------
Compound return             0.08      0.11       0.12       0.10"""
                
                result = self.bot._format_describe_table(mock_asset_list)
                
                # Check that tabulate was called with simple format
                mock_tabulate.tabulate.assert_called_once_with(
                    df_4,
                    headers='keys',
                    tablefmt='simple',
                    floatfmt='.2f'
                )
                
                # Check that result contains expected formatting
                self.assertIn("📊 **Статистика активов:**", result)
                self.assertIn("```", result)
                self.assertIn("SPY.US", result)
    
    def test_6_assets_vertical_format(self):
        """Test vertical format for 6 assets"""
        with patch('bot.TABULATE_AVAILABLE', True):
            # Mock asset list
            mock_asset_list = Mock()
            df_6 = pd.DataFrame(self.data_6_assets, index=self.index)
            mock_asset_list.describe.return_value = df_6
            
            result = self.bot._format_describe_table(mock_asset_list)
            
            # Check that result contains vertical format elements
            self.assertIn("📊 **Статистика активов:**", result)
            self.assertIn("📊 **Compound return:**", result)
            self.assertIn("📊 **CAGR (1Y):**", result)
            self.assertIn("• `SPY.US`: 0.08", result)
            self.assertIn("• `QQQ.US`: 0.11", result)
            self.assertIn("• `AAPL.US`: 0.12", result)
            self.assertIn("• `MSFT.US`: 0.10", result)
            self.assertIn("• `GOOGL.US`: 0.13", result)
            self.assertIn("• `AMZN.US`: 0.09", result)
    
    def test_fallback_simple_formatting(self):
        """Test fallback simple formatting with adaptive behavior"""
        with patch('bot.TABULATE_AVAILABLE', False):
            # Test with 2 assets
            mock_asset_list_2 = Mock()
            df_2 = pd.DataFrame(self.data_2_assets, index=self.index)
            mock_asset_list_2.describe.return_value = df_2
            
            result_2 = self.bot._format_describe_table_simple(mock_asset_list_2)
            
            # Should use simple table format
            self.assertIn("📊 **Статистика активов:**", result_2)
            self.assertIn("```", result_2)
            self.assertIn("| Метрика |", result_2)
            self.assertIn("`SPY.US`", result_2)
            self.assertIn("`QQQ.US`", result_2)
            
            # Test with 4 assets
            mock_asset_list_4 = Mock()
            df_4 = pd.DataFrame(self.data_4_assets, index=self.index)
            mock_asset_list_4.describe.return_value = df_4
            
            result_4 = self.bot._format_describe_table_simple(mock_asset_list_4)
            
            # Should use compact table format
            self.assertIn("📊 **Статистика активов:**", result_4)
            self.assertIn("```", result_4)
            self.assertIn("Metric", result_4)
            self.assertIn("SPY.US", result_4)
            
            # Test with 6 assets
            mock_asset_list_6 = Mock()
            df_6 = pd.DataFrame(self.data_6_assets, index=self.index)
            mock_asset_list_6.describe.return_value = df_6
            
            result_6 = self.bot._format_describe_table_simple(mock_asset_list_6)
            
            # Should use vertical format
            self.assertIn("📊 **Статистика активов:**", result_6)
            self.assertIn("📊 **Compound return:**", result_6)
            self.assertIn("• `SPY.US`: 0.08", result_6)
    
    def test_vertical_format_with_nan_values(self):
        """Test vertical format handles NaN values correctly"""
        with patch('bot.TABULATE_AVAILABLE', True):
            # Create data with NaN values
            data_with_nan = {
                'SPY.US': [0.08, 0.16, float('nan'), 0.09],
                'QQQ.US': [0.11, 0.21, 0.18, float('nan')],
                'AAPL.US': [0.12, 0.22, 0.19, 0.14],
                'MSFT.US': [0.10, 0.20, 0.17, 0.12],
                'GOOGL.US': [0.13, 0.23, 0.20, 0.15],
                'AMZN.US': [0.09, 0.19, 0.16, 0.11]
            }
            index_with_nan = ['Compound return', 'CAGR (1Y)', 'CAGR (5Y)', 'Annualized mean return']
            df_with_nan = pd.DataFrame(data_with_nan, index=index_with_nan)
            
            mock_asset_list = Mock()
            mock_asset_list.describe.return_value = df_with_nan
            
            result = self.bot._format_describe_table(mock_asset_list)
            
            # Check that NaN values are handled as "N/A"
            self.assertIn("N/A", result)
            self.assertIn("• `SPY.US`: 0.08", result)
            self.assertIn("• `QQQ.US`: 0.11", result)
    
    def test_error_handling(self):
        """Test error handling in adaptive formatting"""
        with patch('bot.TABULATE_AVAILABLE', True):
            # Mock asset list to raise an exception
            mock_asset_list = Mock()
            mock_asset_list.describe.side_effect = Exception("Test error")
            
            result = self.bot._format_describe_table(mock_asset_list)
            
            # Should return error message
            self.assertEqual(result, "📊 Ошибка при формировании таблицы статистики")
    
    def test_empty_data_handling(self):
        """Test handling of empty describe data"""
        with patch('bot.TABULATE_AVAILABLE', True):
            # Mock empty DataFrame
            empty_df = pd.DataFrame()
            mock_asset_list = Mock()
            mock_asset_list.describe.return_value = empty_df
            
            result = self.bot._format_describe_table(mock_asset_list)
            
            # Should return no data message
            self.assertEqual(result, "📊 Данные для сравнения недоступны")

if __name__ == '__main__':
    unittest.main()
