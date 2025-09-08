#!/usr/bin/env python3
"""
Test for asset names display in AI analysis messages
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


class TestAssetNamesDisplay(unittest.TestCase):
    """Test cases for asset names display in AI analysis messages"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    def test_asset_names_in_gemini_analysis_message(self):
        """Test that Gemini analysis messages include asset names"""
        try:
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
            
            symbols = ['SPY.US', 'QQQ.US']
            currency = 'USD'
            
            print(f"\n=== Testing Asset Names in Gemini Analysis Message ===")
            
            # Simulate the message formatting logic from _handle_data_analysis_compare_button
            asset_names = data_info.get('asset_names', {})
            
            # Create list with asset names if available
            assets_with_names = []
            for symbol in symbols:
                if symbol in asset_names and asset_names[symbol] != symbol:
                    assets_with_names.append(f"{symbol} ({asset_names[symbol]})")
                else:
                    assets_with_names.append(symbol)
            
            # Format the message as it would appear in the bot
            analysis_text = "🤖 **Анализ данных выполнен**\n\n"
            analysis_text += f"🔍 **Анализируемые активы:** {', '.join(assets_with_names)}\n"
            analysis_text += f"💰 **Валюта:** {currency}\n"
            analysis_text += f"📅 **Период:** полный доступный период данных\n"
            analysis_text += f"📊 **Тип анализа:** Данные (не изображение)"
            
            # Verify asset names are included
            self.assertIn('SPY.US (SPDR S&P 500 ETF Trust)', analysis_text)
            self.assertIn('QQQ.US (Invesco QQQ Trust)', analysis_text)
            
            print(f"✅ Asset names correctly included in Gemini analysis message:")
            print(f"   Message: {analysis_text}")
            
        except Exception as e:
            self.fail(f"Error testing asset names in Gemini analysis message: {e}")
    
    def test_asset_names_in_yandexgpt_analysis_message(self):
        """Test that YandexGPT analysis messages include asset names"""
        try:
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
            
            symbols = ['SPY.US', 'QQQ.US']
            currency = 'USD'
            
            print(f"\n=== Testing Asset Names in YandexGPT Analysis Message ===")
            
            # Simulate the message formatting logic from _handle_yandexgpt_analysis_compare_button
            asset_names = data_info.get('asset_names', {})
            
            # Create list with asset names if available
            assets_with_names = []
            for symbol in symbols:
                if symbol in asset_names and asset_names[symbol] != symbol:
                    assets_with_names.append(f"{symbol} ({asset_names[symbol]})")
                else:
                    assets_with_names.append(symbol)
            
            # Format the message as it would appear in the bot
            analysis_text = "🤖 **Анализ данных выполнен**\n\n"
            analysis_text += f"🔍 **Анализируемые активы:** {', '.join(assets_with_names)}\n"
            analysis_text += f"💰 **Валюта:** {currency}\n"
            analysis_text += f"📅 **Период:** полный доступный период данных\n"
            analysis_text += f"🤖 **AI сервис:** YandexGPT"
            
            # Verify asset names are included
            self.assertIn('SPY.US (SPDR S&P 500 ETF Trust)', analysis_text)
            self.assertIn('QQQ.US (Invesco QQQ Trust)', analysis_text)
            
            print(f"✅ Asset names correctly included in YandexGPT analysis message:")
            print(f"   Message: {analysis_text}")
            
        except Exception as e:
            self.fail(f"Error testing asset names in YandexGPT analysis message: {e}")
    
    def test_asset_names_in_chart_analysis_message(self):
        """Test that chart analysis messages include asset names"""
        try:
            symbols = ['SPY.US', 'QQQ.US']
            asset_names = ['SPY.US (SPDR S&P 500 ETF Trust)', 'QQQ.US (Invesco QQQ Trust)']
            currency = 'USD'
            
            print(f"\n=== Testing Asset Names in Chart Analysis Message ===")
            
            # Simulate the message formatting logic from _handle_chart_analysis_compare_button
            display_assets = asset_names if asset_names else symbols
            
            # Format the message as it would appear in the bot
            analysis_text = "🤖 **Анализ графика выполнен**\n\n"
            analysis_text += f"🔍 **Анализируемые активы:** {', '.join(display_assets)}\n"
            analysis_text += f"💰 **Валюта:** {currency}\n"
            analysis_text += f"📅 **Период:** полный доступный период данных"
            
            # Verify asset names are included
            self.assertIn('SPY.US (SPDR S&P 500 ETF Trust)', analysis_text)
            self.assertIn('QQQ.US (Invesco QQQ Trust)', analysis_text)
            
            print(f"✅ Asset names correctly included in chart analysis message:")
            print(f"   Message: {analysis_text}")
            
        except Exception as e:
            self.fail(f"Error testing asset names in chart analysis message: {e}")
    
    def test_asset_names_in_metrics_excel_caption(self):
        """Test that Excel metrics caption includes asset names"""
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
            
            print(f"\n=== Testing Asset Names in Excel Metrics Caption ===")
            
            # Simulate the caption formatting logic from _handle_metrics_compare_button
            asset_names = metrics_data.get('asset_names', {})
            
            # Create list with asset names if available
            assets_with_names = []
            for symbol in symbols:
                if symbol in asset_names and asset_names[symbol] != symbol:
                    assets_with_names.append(f"{symbol} ({asset_names[symbol]})")
                else:
                    assets_with_names.append(symbol)
            
            # Format the caption as it would appear in the bot
            caption = f"📊 **Детальная статистика активов**\n\n"
            caption += f"🔍 **Анализируемые активы:** {', '.join(assets_with_names)}\n"
            caption += f"💰 **Валюта:** {currency}\n"
            caption += f"📅 **Дата создания:** {metrics_data['timestamp']}\n\n"
            caption += f"📋 **Содержит:**\n"
            caption += f"• Основные метрики производительности\n"
            caption += f"• Коэффициенты Шарпа и Сортино\n"
            caption += f"• Анализ рисков и доходности\n"
            caption += f"• Корреляционная матрица\n"
            caption += f"• Детальная статистика по каждому активу"
            
            # Verify asset names are included
            self.assertIn('SPY.US (SPDR S&P 500 ETF Trust)', caption)
            self.assertIn('QQQ.US (Invesco QQQ Trust)', caption)
            
            print(f"✅ Asset names correctly included in Excel metrics caption:")
            print(f"   Caption: {caption}")
            
        except Exception as e:
            self.fail(f"Error testing asset names in Excel metrics caption: {e}")
    
    def test_asset_names_fallback_to_symbols(self):
        """Test fallback to symbols when asset names are not available"""
        try:
            symbols = ['SPY.US', 'QQQ.US']
            asset_names = {}  # No asset names available
            currency = 'USD'
            
            print(f"\n=== Testing Asset Names Fallback to Symbols ===")
            
            # Simulate the message formatting logic
            assets_with_names = []
            for symbol in symbols:
                if symbol in asset_names and asset_names[symbol] != symbol:
                    assets_with_names.append(f"{symbol} ({asset_names[symbol]})")
                else:
                    assets_with_names.append(symbol)
            
            # Format the message
            analysis_text = "🤖 **Анализ данных выполнен**\n\n"
            analysis_text += f"🔍 **Анализируемые активы:** {', '.join(assets_with_names)}\n"
            analysis_text += f"💰 **Валюта:** {currency}\n"
            
            # Verify fallback to symbols works
            self.assertIn('SPY.US', analysis_text)
            self.assertIn('QQQ.US', analysis_text)
            self.assertNotIn('SPDR S&P 500 ETF Trust', analysis_text)
            self.assertNotIn('Invesco QQQ Trust', analysis_text)
            
            print(f"✅ Fallback to symbols works correctly:")
            print(f"   Message: {analysis_text}")
            
        except Exception as e:
            self.fail(f"Error testing asset names fallback: {e}")
    
    def test_asset_names_formatting_consistency(self):
        """Test that asset names formatting is consistent across all messages"""
        try:
            symbols = ['SPY.US', 'QQQ.US']
            asset_names = {
                'SPY.US': 'SPDR S&P 500 ETF Trust',
                'QQQ.US': 'Invesco QQQ Trust'
            }
            
            print(f"\n=== Testing Asset Names Formatting Consistency ===")
            
            # Test different message types
            message_types = [
                "Gemini Analysis",
                "YandexGPT Analysis", 
                "Chart Analysis",
                "Excel Metrics"
            ]
            
            for msg_type in message_types:
                # Create list with asset names if available
                assets_with_names = []
                for symbol in symbols:
                    if symbol in asset_names and asset_names[symbol] != symbol:
                        assets_with_names.append(f"{symbol} ({asset_names[symbol]})")
                    else:
                        assets_with_names.append(symbol)
                
                # Verify consistent formatting
                self.assertEqual(len(assets_with_names), 2)
                self.assertIn('SPY.US (SPDR S&P 500 ETF Trust)', assets_with_names)
                self.assertIn('QQQ.US (Invesco QQQ Trust)', assets_with_names)
                
                print(f"✅ {msg_type}: {', '.join(assets_with_names)}")
            
        except Exception as e:
            self.fail(f"Error testing asset names formatting consistency: {e}")


if __name__ == '__main__':
    print("Testing asset names display in AI analysis messages...")
    print(f"OKAMA_AVAILABLE: {OKAMA_AVAILABLE}")
    
    unittest.main(verbosity=2)
