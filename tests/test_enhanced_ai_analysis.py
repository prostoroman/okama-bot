#!/usr/bin/env python3
"""
Test for enhanced AI data analysis functionality
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import okama as ok
    OKAMA_AVAILABLE = True
except ImportError:
    OKAMA_AVAILABLE = False
    print("Warning: okama library not available for testing")

from bot import ShansAi
from services.gemini_service import GeminiService


class TestEnhancedAIAnalysis(unittest.TestCase):
    """Test cases for enhanced AI data analysis functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
        self.gemini_service = GeminiService()
    
    def test_prepare_data_description_with_describe_table(self):
        """Test that prepare_data_description includes describe table prominently"""
        # Mock data info with describe table
        data_info = {
            'symbols': ['SPY.US', 'QQQ.US'],
            'currency': 'USD',
            'period': 'полный доступный период данных',
            'asset_count': 2,
            'analysis_type': 'asset_comparison',
            'describe_table': '📊 **Статистика активов:**\n\n| Метрика | SPY.US | QQQ.US |\n|---------|--------|--------|\n| CAGR | 0.14 | 0.18 |',
            'performance': {
                'SPY.US': {
                    'total_return': 0.15,
                    'volatility': 0.12,
                    'sharpe_ratio': 1.2
                },
                'QQQ.US': {
                    'total_return': 0.18,
                    'volatility': 0.15,
                    'sharpe_ratio': 1.1
                }
            },
            'correlations': [[1.0, 0.8], [0.8, 1.0]],
            'analysis_metadata': {
                'data_source': 'okama.AssetList.describe()',
                'analysis_depth': 'comprehensive',
                'includes_correlations': True,
                'includes_describe_table': True
            }
        }
        
        # Test the prepare_data_description function
        result = self.gemini_service._prepare_data_description(data_info)
        
        # Check that result contains expected elements
        self.assertIsInstance(result, str)
        self.assertIn("📊 ДЕТАЛЬНАЯ СТАТИСТИКА АКТИВОВ", result)
        self.assertIn("okama.AssetList.describe", result)
        self.assertIn("SPY.US", result)
        self.assertIn("QQQ.US", result)
        self.assertIn("ИНСТРУКЦИИ ДЛЯ АНАЛИЗА", result)
        self.assertIn("Сравни активы по всем метрикам", result)
        
        print(f"Enhanced data description result:\n{result}")
    
    def test_prepare_data_description_without_describe_table(self):
        """Test prepare_data_description when describe table is missing"""
        data_info = {
            'symbols': ['SPY.US'],
            'currency': 'USD',
            'period': 'полный доступный период данных',
            'describe_table': '',  # Empty describe table
            'performance': {
                'SPY.US': {
                    'total_return': 0.15,
                    'volatility': 0.12
                }
            },
            'analysis_metadata': {
                'data_source': 'basic',
                'analysis_depth': 'basic',
                'includes_correlations': False,
                'includes_describe_table': False
            }
        }
        
        result = self.gemini_service._prepare_data_description(data_info)
        
        # Should still work but without describe table
        self.assertIsInstance(result, str)
        self.assertIn("SPY.US", result)
        self.assertIn("USD", result)
        self.assertNotIn("📊 ДЕТАЛЬНАЯ СТАТИСТИКА АКТИВОВ", result)
        
        print(f"Data description without describe table:\n{result}")
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_prepare_data_for_analysis_enhanced(self):
        """Test enhanced prepare_data_for_analysis function"""
        try:
            # Create a simple asset list for testing
            symbols = ['SPY.US', 'QQQ.US']
            asset_list = ok.AssetList(symbols)
            
            # Mock user context with describe table
            user_id = 12345
            describe_table = self.bot._format_describe_table(asset_list)
            
            # Mock user context
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
            
            # Check that result contains enhanced fields
            self.assertIn('describe_table', result)
            self.assertIn('asset_count', result)
            self.assertIn('analysis_type', result)
            self.assertIn('analysis_metadata', result)
            
            # Check analysis metadata
            metadata = result['analysis_metadata']
            self.assertIn('timestamp', metadata)
            self.assertIn('data_source', metadata)
            self.assertIn('analysis_depth', metadata)
            self.assertIn('includes_correlations', metadata)
            self.assertIn('includes_describe_table', metadata)
            
            # Check that describe table is included
            self.assertTrue(result['analysis_metadata']['includes_describe_table'])
            self.assertIn('📊', result['describe_table'])
            
            print(f"Enhanced data info keys: {list(result.keys())}")
            print(f"Analysis metadata: {result['analysis_metadata']}")
            
        except Exception as e:
            self.fail(f"Error testing enhanced prepare_data_for_analysis: {e}")
    
    def test_gemini_prompt_enhancement(self):
        """Test that Gemini prompt includes detailed instructions"""
        # Mock data info
        data_info = {
            'symbols': ['SPY.US', 'QQQ.US'],
            'describe_table': '📊 **Статистика активов:**\n\n| Метрика | SPY.US | QQQ.US |',
            'analysis_metadata': {
                'data_source': 'okama.AssetList.describe()',
                'analysis_depth': 'comprehensive'
            }
        }
        
        # Test the prompt generation
        data_description = self.gemini_service._prepare_data_description(data_info)
        
        # Check that prompt includes detailed instructions
        self.assertIn("ИНСТРУКЦИИ ДЛЯ АНАЛИЗА", data_description)
        self.assertIn("Сравни активы по всем метрикам", data_description)
        self.assertIn("Проанализируй соотношение риск-доходность", data_description)
        self.assertIn("Оцени корреляции между активами", data_description)
        self.assertIn("Дай рекомендации по инвестированию", data_description)
        self.assertIn("Выдели сильные и слабые стороны", data_description)
        
        print(f"Enhanced prompt includes detailed instructions: {len(data_description)} characters")
    
    def test_error_handling_in_prepare_data_description(self):
        """Test error handling in prepare_data_description"""
        # Test with empty data_info
        result = self.gemini_service._prepare_data_description({})
        self.assertIsInstance(result, str)
        self.assertIn("ИНСТРУКЦИИ ДЛЯ АНАЛИЗА", result)
        
        # Test with None data_info
        result = self.gemini_service._prepare_data_description(None)
        self.assertIsInstance(result, str)


if __name__ == '__main__':
    print("Testing enhanced AI data analysis functionality...")
    print(f"OKAMA_AVAILABLE: {OKAMA_AVAILABLE}")
    
    unittest.main(verbosity=2)
