#!/usr/bin/env python3
"""
Test for compare command table display fix
Tests the improved table formatting in /compare command
"""

import unittest
import sys
import os
import pandas as pd
from unittest.mock import Mock, patch

# Add the parent directory to the path to import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi

class TestCompareTableFix(unittest.TestCase):
    """Test cases for compare command table display improvements"""
    
    def setUp(self):
        """Set up test environment"""
        self.bot = ShansAi()
        
        # Mock asset list with describe data
        self.mock_asset_list = Mock()
        
        # Create sample describe data
        self.sample_data = {
            'SPY.US': [0.08, 0.16, 0.14, 0.09, 0.01, 0.17, -0.51],
            'QQQ.US': [0.11, 0.21, 0.18, 0.13, 0.00, 0.27, -0.81],
            'inflation': [0.02, 0.03, 0.03, 0.03, None, None, None]
        }
        
        self.sample_index = [
            'Compound return',
            'CAGR',
            'CAGR',
            'Annualized mean return',
            'Dividend yield',
            'Risk',
            'Max drawdowns'
        ]
        
        self.describe_df = pd.DataFrame(self.sample_data, index=self.sample_index)
        self.mock_asset_list.describe.return_value = self.describe_df
    
    def test_format_describe_table_with_tabulate(self):
        """Test main formatting function with tabulate available"""
        with patch('bot.TABULATE_AVAILABLE', True):
            with patch('bot.tabulate') as mock_tabulate:
                # Mock tabulate.tabulate to return a formatted table
                mock_tabulate.tabulate.return_value = """| property               | period             | SPY.US | QQQ.US | inflation |
|---:|:-----------------------|:-------------------|:-------|:-------|:----------|
|  0 | Compound return        | YTD                | 0.08   | 0.11    | 0.02      |
|  1 | CAGR                   | 1 years            | 0.16   | 0.21    | 0.03      |"""
                
                result = self.bot._format_describe_table(self.mock_asset_list)
                
                # Check that tabulate was called with correct parameters
                mock_tabulate.tabulate.assert_called_once_with(
                    self.describe_df,
                    headers='keys',
                    tablefmt='pipe',
                    floatfmt='.2f'
                )
                
                # Check that result contains expected formatting
                self.assertIn("📊 **Статистика активов:**", result)
                self.assertIn("```", result)
                self.assertIn("| property", result)
    
    def test_format_describe_table_simple_fallback(self):
        """Test simple formatting fallback when tabulate is not available"""
        with patch('bot.TABULATE_AVAILABLE', False):
            result = self.bot._format_describe_table_simple(self.mock_asset_list)
            
            # Check that result contains expected elements
            self.assertIn("📊 **Статистика активов:**", result)
            self.assertIn("```", result)
            self.assertIn("| Метрика |", result)
            self.assertIn("SPY.US", result)
            self.assertIn("QQQ.US", result)
            self.assertIn("inflation", result)
            
            # Check that it's properly formatted as markdown table
            self.assertIn("| --- |", result)
            self.assertIn("Compound return", result)
            self.assertIn("0.08", result)
            self.assertIn("0.11", result)
    
    def test_format_describe_table_error_handling(self):
        """Test error handling in main formatting function"""
        with patch('bot.TABULATE_AVAILABLE', True):
            # Mock asset list to raise an exception
            self.mock_asset_list.describe.side_effect = Exception("Test error")
            
            result = self.bot._format_describe_table(self.mock_asset_list)
            
            # Should return error message
            self.assertEqual(result, "📊 Ошибка при формировании таблицы статистики")
    
    def test_format_describe_table_simple_error_handling(self):
        """Test error handling in simple formatting function"""
        # Mock asset list to raise an exception
        self.mock_asset_list.describe.side_effect = Exception("Test error")
        
        result = self.bot._format_describe_table_simple(self.mock_asset_list)
        
        # Should return error message
        self.assertEqual(result, "📊 Ошибка при формировании таблицы статистики")
    
    def test_format_describe_table_empty_data(self):
        """Test handling of empty describe data"""
        with patch('bot.TABULATE_AVAILABLE', True):
            # Mock empty DataFrame
            empty_df = pd.DataFrame()
            self.mock_asset_list.describe.return_value = empty_df
            
            result = self.bot._format_describe_table(self.mock_asset_list)
            
            # Should return no data message
            self.assertEqual(result, "📊 Данные для сравнения недоступны")
    
    def test_format_describe_table_none_data(self):
        """Test handling of None describe data"""
        with patch('bot.TABULATE_AVAILABLE', True):
            # Mock None return
            self.mock_asset_list.describe.return_value = None
            
            result = self.bot._format_describe_table(self.mock_asset_list)
            
            # Should return no data message
            self.assertEqual(result, "📊 Данные для сравнения недоступны")
    
    def test_simple_formatting_with_nan_values(self):
        """Test simple formatting handles NaN values correctly"""
        with patch('bot.TABULATE_AVAILABLE', False):
            # Create data with NaN values
            data_with_nan = {
                'SPY.US': [0.08, 0.16, float('nan'), 0.09],
                'QQQ.US': [0.11, 0.21, 0.18, float('nan')]
            }
            index_with_nan = ['Compound return', 'CAGR', 'CAGR', 'Annualized mean return']
            df_with_nan = pd.DataFrame(data_with_nan, index=index_with_nan)
            self.mock_asset_list.describe.return_value = df_with_nan
            
            result = self.bot._format_describe_table_simple(self.mock_asset_list)
            
            # Check that NaN values are handled as "N/A"
            self.assertIn("N/A", result)
            self.assertIn("0.08", result)
            self.assertIn("0.11", result)

if __name__ == '__main__':
    unittest.main()
