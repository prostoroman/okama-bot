#!/usr/bin/env python3
"""
Test for AI data analysis with describe table integration
"""

import unittest
import sys
import os

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import okama as ok
    OKAMA_AVAILABLE = True
except ImportError:
    OKAMA_AVAILABLE = False
    print("Warning: okama library not available for testing")

from bot import ShansAi


class TestAIDataAnalysisIntegration(unittest.TestCase):
    """Test cases for AI data analysis with describe table integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_prepare_data_for_analysis_with_describe_table(self):
        """Test that prepare_data_for_analysis includes describe table"""
        try:
            # Create a simple asset list for testing
            symbols = ['SPY.US', 'QQQ.US']
            asset_list = ok.AssetList(symbols)
            
            # Mock user context with describe table
            user_id = 12345
            describe_table = self.bot._format_describe_table(asset_list)
            
            # Mock user context
            self.bot._update_user_context(user_id, describe_table=describe_table)
            
            # Test the prepare_data_for_analysis function
            import asyncio
            result = asyncio.run(self.bot._prepare_data_for_analysis(
                symbols=symbols,
                currency='USD',
                expanded_symbols=symbols,
                portfolio_contexts=[],
                user_id=user_id
            ))
            
            # Check that result contains describe table
            self.assertIn('describe_table', result)
            self.assertIsInstance(result['describe_table'], str)
            self.assertIn('📊', result['describe_table'])
            self.assertIn('Статистика активов', result['describe_table'])
            
            print(f"Data info keys: {list(result.keys())}")
            print(f"Describe table length: {len(result['describe_table'])}")
            
        except Exception as e:
            self.fail(f"Error testing prepare_data_for_analysis: {e}")
    
    def test_prepare_data_for_analysis_without_describe_table(self):
        """Test prepare_data_for_analysis when describe table is not available"""
        try:
            import asyncio
            result = asyncio.run(self.bot._prepare_data_for_analysis(
                symbols=['SPY.US'],
                currency='USD',
                expanded_symbols=['SPY.US'],
                portfolio_contexts=[],
                user_id=99999  # Non-existent user
            ))
            
            # Check that result still contains describe_table field
            self.assertIn('describe_table', result)
            self.assertEqual(result['describe_table'], '')
            
        except Exception as e:
            self.fail(f"Error testing prepare_data_for_analysis without describe table: {e}")


if __name__ == '__main__':
    print("Testing AI data analysis with describe table integration...")
    print(f"OKAMA_AVAILABLE: {OKAMA_AVAILABLE}")
    
    unittest.main(verbosity=2)
