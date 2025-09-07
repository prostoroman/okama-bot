#!/usr/bin/env python3
"""
Test for compare command describe table functionality
"""

import unittest
import sys
import os
import pandas as pd

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import okama as ok
    OKAMA_AVAILABLE = True
except ImportError:
    OKAMA_AVAILABLE = False
    print("Warning: okama library not available for testing")

try:
    import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False
    print("Warning: tabulate library not available for testing")

from bot import ShansAi


class TestCompareDescribeTable(unittest.TestCase):
    """Test cases for compare command describe table functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_format_describe_table_with_tabulate(self):
        """Test formatting describe table with tabulate library"""
        if not TABULATE_AVAILABLE:
            self.skipTest("tabulate library not available")
        
        try:
            # Create a simple asset list for testing
            symbols = ['SPY.US', 'QQQ.US']
            asset_list = ok.AssetList(symbols)
            
            # Test the formatting function
            result = self.bot._format_describe_table(asset_list)
            
            # Check that result is a string
            self.assertIsInstance(result, str)
            
            # Check that result contains expected elements
            self.assertIn("📊", result)
            self.assertIn("Статистика активов", result)
            
            # Check that result contains markdown table formatting
            self.assertIn("```", result)
            
            print(f"Formatted table result:\n{result}")
            
        except Exception as e:
            self.fail(f"Error testing describe table formatting: {e}")
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_format_describe_table_simple_fallback(self):
        """Test simple text formatting fallback"""
        try:
            # Create a simple asset list for testing
            symbols = ['SPY.US', 'QQQ.US']
            asset_list = ok.AssetList(symbols)
            
            # Test the simple formatting function
            result = self.bot._format_describe_table_simple(asset_list)
            
            # Check that result is a string
            self.assertIsInstance(result, str)
            
            # Check that result contains expected elements
            self.assertIn("📊", result)
            self.assertIn("Статистика активов", result)
            
            print(f"Simple formatted table result:\n{result}")
            
        except Exception as e:
            self.fail(f"Error testing simple describe table formatting: {e}")
    
    def test_format_describe_table_error_handling(self):
        """Test error handling in describe table formatting"""
        # Test with None input
        result = self.bot._format_describe_table(None)
        self.assertIn("Ошибка", result)
        
        # Test with invalid input
        result = self.bot._format_describe_table("invalid_input")
        self.assertIn("Ошибка", result)
    
    def test_format_describe_table_simple_error_handling(self):
        """Test error handling in simple describe table formatting"""
        # Test with None input
        result = self.bot._format_describe_table_simple(None)
        self.assertIn("Ошибка", result)
        
        # Test with invalid input
        result = self.bot._format_describe_table_simple("invalid_input")
        self.assertIn("Ошибка", result)


if __name__ == '__main__':
    print("Testing compare command describe table functionality...")
    print(f"OKAMA_AVAILABLE: {OKAMA_AVAILABLE}")
    print(f"TABULATE_AVAILABLE: {TABULATE_AVAILABLE}")
    
    unittest.main(verbosity=2)
