#!/usr/bin/env python3
"""
Test for asset names integration in data preparation and Excel export
"""

import unittest
import sys
import os
from unittest.mock import Mock, AsyncMock, patch
import pandas as pd
import numpy as np
import asyncio

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import okama as ok
    OKAMA_AVAILABLE = True
except ImportError:
    OKAMA_AVAILABLE = False
    print("Warning: okama library not available for testing")

from bot import ShansAi


class TestAssetNamesIntegration(unittest.TestCase):
    """Test cases for asset names integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    @unittest.skipUnless(OKAMA_AVAILABLE, "okama library not available")
    def test_prepare_data_for_analysis_with_asset_names(self):
        """Test _prepare_data_for_analysis includes asset names"""
        try:
            # Use real assets for testing
            symbols = ['SPY.US']
            expanded_symbols = [ok.Asset('SPY.US')]
            
            print(f"\n=== Testing Asset Names in Data Preparation ===")
            
            # Test the enhanced prepare_data_for_analysis function
            import asyncio
            
            async def test_prepare_data():
                result = await self.bot._prepare_data_for_analysis(
                    symbols=symbols,
                    currency='USD',
                    expanded_symbols=expanded_symbols,
                    portfolio_contexts=[],
                    user_id=12345
                )
                return result
            
            result = asyncio.run(test_prepare_data())
            
            # Verify asset names are included
            self.assertIn('asset_names', result)
            self.assertIsInstance(result['asset_names'], dict)
            
            # Check specific asset name
            self.assertEqual(result['asset_names']['SPY.US'], "SPDR S&P 500 ETF Trust")
            
            print(f"✅ Asset names correctly included:")
            for symbol, name in result['asset_names'].items():
                print(f"   {symbol}: {name}")
            
            # Verify other data is still present
            self.assertIn('symbols', result)
            self.assertIn('performance', result)
            self.assertEqual(result['symbols'], symbols)
            
        except Exception as e:
            self.fail(f"Error testing asset names in data preparation: {e}")
    
    def test_prepare_comprehensive_metrics_with_asset_names(self):
        """Test _prepare_comprehensive_metrics includes asset names"""
        try:
            # Create mock assets with names
            mock_asset1 = Mock()
            mock_asset1.name = "SPDR S&P 500 ETF Trust"
            mock_asset1.symbol = "SPY.US"
            mock_asset1.close_monthly = pd.Series([100, 105, 110, 108, 115, 120], 
                                                 index=pd.date_range('2023-01-01', periods=6, freq='ME'))
            
            symbols = ['SPY.US']
            expanded_symbols = [mock_asset1]
            
            print(f"\n=== Testing Asset Names in Comprehensive Metrics ===")
            
            result = self.bot._prepare_comprehensive_metrics(
                symbols=symbols,
                currency='USD',
                expanded_symbols=expanded_symbols,
                portfolio_contexts=[],
                user_id=12345
            )
            
            # Verify asset names are included
            self.assertIn('asset_names', result)
            self.assertIsInstance(result['asset_names'], dict)
            
            # Check specific asset name
            self.assertEqual(result['asset_names']['SPY.US'], "SPDR S&P 500 ETF Trust")
            
            print(f"✅ Asset names correctly included in comprehensive metrics:")
            for symbol, name in result['asset_names'].items():
                print(f"   {symbol}: {name}")
            
            # Verify other data is still present
            self.assertIn('symbols', result)
            self.assertIn('detailed_metrics', result)
            self.assertEqual(result['symbols'], symbols)
            
        except Exception as e:
            self.fail(f"Error testing asset names in comprehensive metrics: {e}")
    
    def test_gemini_service_with_asset_names(self):
        """Test Gemini service uses asset names in data description"""
        try:
            from services.gemini_service import GeminiService
            
            gemini_service = GeminiService()
            
            # Create test data with asset names
            data_info = {
                'symbols': ['SPY.US', 'QQQ.US'],
                'asset_names': {
                    'SPY.US': 'SPDR S&P 500 ETF Trust',
                    'QQQ.US': 'Invesco QQQ Trust'
                },
                'currency': 'USD',
                'period': 'полный доступный период данных',
                'performance': {
                    'SPY.US': {'total_return': 0.12, 'annual_return': 0.08},
                    'QQQ.US': {'total_return': 0.15, 'annual_return': 0.10}
                },
                'correlations': [[1.0, 0.8], [0.8, 1.0]],
                'describe_table': 'Test describe table'
            }
            
            print(f"\n=== Testing Gemini Service with Asset Names ===")
            
            description = gemini_service._prepare_data_description(data_info)
            
            # Verify asset names are used in description
            self.assertIn('SPY.US (SPDR S&P 500 ETF Trust)', description)
            self.assertIn('QQQ.US (Invesco QQQ Trust)', description)
            
            # Verify performance metrics use asset names
            self.assertIn('**SPY.US (SPDR S&P 500 ETF Trust):**', description)
            self.assertIn('**QQQ.US (Invesco QQQ Trust):**', description)
            
            # Verify correlation matrix uses asset names
            self.assertIn('SPY.US (SPDR S&P 500 ETF Trust) ↔ QQQ.US (Invesco QQQ Trust)', description)
            
            print(f"✅ Gemini service correctly uses asset names in description")
            print(f"Description length: {len(description)} characters")
            
        except Exception as e:
            self.fail(f"Error testing Gemini service with asset names: {e}")
    
    def test_yandexgpt_service_with_asset_names(self):
        """Test YandexGPT service uses asset names in data description"""
        try:
            from services.yandexgpt_service import YandexGPTService
            
            yandexgpt_service = YandexGPTService()
            
            # Create test data with asset names
            data_info = {
                'symbols': ['SPY.US', 'QQQ.US'],
                'asset_names': {
                    'SPY.US': 'SPDR S&P 500 ETF Trust',
                    'QQQ.US': 'Invesco QQQ Trust'
                },
                'currency': 'USD',
                'period': 'полный доступный период данных',
                'performance': {
                    'SPY.US': {'total_return': 0.12, 'annual_return': 0.08},
                    'QQQ.US': {'total_return': 0.15, 'annual_return': 0.10}
                },
                'correlations': [[1.0, 0.8], [0.8, 1.0]],
                'describe_table': 'Test describe table'
            }
            
            print(f"\n=== Testing YandexGPT Service with Asset Names ===")
            
            description = yandexgpt_service._prepare_data_description(data_info)
            
            # Verify asset names are used in description
            self.assertIn('SPY.US (SPDR S&P 500 ETF Trust)', description)
            self.assertIn('QQQ.US (Invesco QQQ Trust)', description)
            
            # Verify performance metrics use asset names
            self.assertIn('**SPY.US (SPDR S&P 500 ETF Trust):**', description)
            self.assertIn('**QQQ.US (Invesco QQQ Trust):**', description)
            
            # Verify correlation matrix uses asset names
            self.assertIn('SPY.US (SPDR S&P 500 ETF Trust) ↔ QQQ.US (Invesco QQQ Trust)', description)
            
            print(f"✅ YandexGPT service correctly uses asset names in description")
            print(f"Description length: {len(description)} characters")
            
        except Exception as e:
            self.fail(f"Error testing YandexGPT service with asset names: {e}")
    
    def test_excel_export_with_asset_names(self):
        """Test Excel export includes asset names"""
        try:
            # Create test metrics data with asset names
            metrics_data = {
                'symbols': ['SPY.US', 'QQQ.US'],
                'asset_names': {
                    'SPY.US': 'SPDR S&P 500 ETF Trust',
                    'QQQ.US': 'Invesco QQQ Trust'
                },
                'currency': 'USD',
                'period': 'полный доступный период данных',
                'timestamp': '2025-09-08 10:00:00',
                'detailed_metrics': {
                    'SPY.US': {
                        'total_return': 0.12,
                        'annual_return': 0.08,
                        'volatility': 0.15,
                        'sharpe_ratio': 0.4,
                        'sortino_ratio': 0.5,
                        'max_drawdown': -0.2,
                        'calmar_ratio': 0.4,
                        'var_95': -0.05,
                        'cvar_95': -0.07
                    },
                    'QQQ.US': {
                        'total_return': 0.15,
                        'annual_return': 0.10,
                        'volatility': 0.18,
                        'sharpe_ratio': 0.44,
                        'sortino_ratio': 0.55,
                        'max_drawdown': -0.25,
                        'calmar_ratio': 0.4,
                        'var_95': -0.06,
                        'cvar_95': -0.08
                    }
                },
                'correlations': [[1.0, 0.8], [0.8, 1.0]]
            }
            
            symbols = ['SPY.US', 'QQQ.US']
            currency = 'USD'
            
            print(f"\n=== Testing Excel Export with Asset Names ===")
            
            excel_buffer = self.bot._create_metrics_excel(metrics_data, symbols, currency)
            
            if excel_buffer:
                excel_bytes = excel_buffer.getvalue()
                print(f"✅ Excel file created successfully")
                print(f"   File size: {len(excel_bytes)} bytes")
                print(f"   File format: {'Excel (.xlsx)' if excel_bytes.startswith(b'PK') else 'CSV (.csv)'}")
                
                # Save to file for inspection
                filename = f"asset_names_test_{'_'.join(symbols)}_{currency}.xlsx"
                with open(filename, 'wb') as f:
                    f.write(excel_bytes)
                print(f"   Saved to: {filename}")
                
                # Verify file was created
                self.assertTrue(os.path.exists(filename))
                
                # Clean up
                os.remove(filename)
                
            else:
                print("❌ Failed to create Excel file")
                self.fail("Excel file creation failed")
            
        except Exception as e:
            self.fail(f"Error testing Excel export with asset names: {e}")
    
    def test_asset_names_fallback(self):
        """Test fallback when asset names are not available"""
        try:
            # Create mock asset without name
            mock_asset = Mock()
            mock_asset.symbol = "TEST.US"
            # No name attribute
            mock_asset.close_monthly = pd.Series([100, 105, 110], 
                                               index=pd.date_range('2023-01-01', periods=3, freq='ME'))
            
            symbols = ['TEST.US']
            expanded_symbols = [mock_asset]
            
            print(f"\n=== Testing Asset Names Fallback ===")
            
            result = self.bot._prepare_comprehensive_metrics(
                symbols=symbols,
                currency='USD',
                expanded_symbols=expanded_symbols,
                portfolio_contexts=[],
                user_id=12345
            )
            
            # Verify fallback to symbol
            self.assertIn('asset_names', result)
            self.assertEqual(result['asset_names']['TEST.US'], 'TEST.US')
            
            print(f"✅ Fallback to symbol works correctly:")
            print(f"   TEST.US: {result['asset_names']['TEST.US']}")
            
        except Exception as e:
            self.fail(f"Error testing asset names fallback: {e}")


if __name__ == '__main__':
    print("Testing asset names integration...")
    print(f"OKAMA_AVAILABLE: {OKAMA_AVAILABLE}")
    
    unittest.main(verbosity=2)
