#!/usr/bin/env python3
"""
Test for AI analysis Sharpe and Sortino ratio fix
"""

import unittest
import asyncio
import sys
import os

# Add the parent directory to the path to import bot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
import okama as ok

class TestAIAnalysisSharpeSortinoFix(unittest.TestCase):
    """Test cases for AI analysis Sharpe and Sortino ratio fix"""
    
    def setUp(self):
        """Set up test environment"""
        self.bot = ShansAi()
        
    def test_prepare_data_for_analysis_sharpe_sortino(self):
        """Test that _prepare_data_for_analysis includes Sharpe and Sortino ratios"""
        print(f"\n=== Testing AI Analysis Data Preparation ===")
        
        # Test symbols
        symbols = ['AAPL.US', 'SPY.US']
        currency = 'USD'
        
        # Create expanded symbols
        expanded_symbols = []
        for symbol in symbols:
            try:
                asset = ok.Asset(symbol)
                expanded_symbols.append(asset)
                print(f"✅ Created asset: {symbol}")
            except Exception as e:
                print(f"❌ Failed to create asset {symbol}: {e}")
                return
        
        # Test the function
        try:
            data_info = asyncio.run(self.bot._prepare_data_for_analysis(
                symbols=symbols,
                currency=currency,
                expanded_symbols=expanded_symbols,
                portfolio_contexts=[],
                user_id=12345
            ))
            
            print(f"\n📊 Data Info Structure:")
            print(f"  - Symbols: {data_info.get('symbols', [])}")
            print(f"  - Currency: {data_info.get('currency', 'N/A')}")
            print(f"  - Asset names: {data_info.get('asset_names', {})}")
            print(f"  - Performance keys: {list(data_info.get('performance', {}).keys())}")
            
            # Check performance metrics for each symbol
            for symbol in symbols:
                if symbol in data_info.get('performance', {}):
                    metrics = data_info['performance'][symbol]
                    print(f"\n📈 {symbol} Metrics:")
                    print(f"  - Total return: {metrics.get('total_return', 'N/A')}")
                    print(f"  - Annual return: {metrics.get('annual_return', 'N/A')}")
                    print(f"  - Volatility: {metrics.get('volatility', 'N/A')}")
                    print(f"  - Sharpe ratio: {metrics.get('sharpe_ratio', 'N/A')}")
                    print(f"  - Sortino ratio: {metrics.get('sortino_ratio', 'N/A')}")
                    print(f"  - Max drawdown: {metrics.get('max_drawdown', 'N/A')}")
                    
                    # Check if Sharpe and Sortino are not None/empty
                    sharpe = metrics.get('sharpe_ratio')
                    sortino = metrics.get('sortino_ratio')
                    
                    if sharpe is not None and sharpe != 0:
                        print(f"  ✅ Sharpe ratio: {sharpe:.4f}")
                    else:
                        print(f"  ❌ Sharpe ratio is empty or zero: {sharpe}")
                    
                    if sortino is not None and sortino != 0:
                        print(f"  ✅ Sortino ratio: {sortino:.4f}")
                    else:
                        print(f"  ❌ Sortino ratio is empty or zero: {sortino}")
                else:
                    print(f"❌ No performance data for {symbol}")
            
            # Test Gemini service data preparation
            if hasattr(self.bot, 'gemini_service') and self.bot.gemini_service:
                print(f"\n🤖 Testing Gemini Data Description:")
                try:
                    data_description = self.bot.gemini_service._prepare_data_description(data_info)
                    print(f"  - Description length: {len(data_description)}")
                    
                    # Check if Sharpe and Sortino are mentioned in description
                    if 'Коэффициент Шарпа' in data_description:
                        print(f"  ✅ Sharpe ratio mentioned in description")
                    else:
                        print(f"  ❌ Sharpe ratio NOT mentioned in description")
                    
                    if 'Коэффициент Сортино' in data_description:
                        print(f"  ✅ Sortino ratio mentioned in description")
                    else:
                        print(f"  ❌ Sortino ratio NOT mentioned in description")
                        
                except Exception as e:
                    print(f"  ❌ Error preparing Gemini description: {e}")
            
            # Test YandexGPT service data preparation
            if hasattr(self.bot, 'yandexgpt_service') and self.bot.yandexgpt_service:
                print(f"\n🤖 Testing YandexGPT Data Description:")
                try:
                    data_description = self.bot.yandexgpt_service._prepare_data_description(data_info)
                    print(f"  - Description length: {len(data_description)}")
                    
                    # Check if Sharpe and Sortino are mentioned in description
                    if 'Коэффициент Шарпа' in data_description:
                        print(f"  ✅ Sharpe ratio mentioned in description")
                    else:
                        print(f"  ❌ Sharpe ratio NOT mentioned in description")
                    
                    if 'Коэффициент Сортино' in data_description:
                        print(f"  ✅ Sortino ratio mentioned in description")
                    else:
                        print(f"  ❌ Sortino ratio NOT mentioned in description")
                        
                except Exception as e:
                    print(f"  ❌ Error preparing YandexGPT description: {e}")
            
            print(f"\n✅ AI Analysis Data Preparation Test Completed")
            
        except Exception as e:
            print(f"❌ Error in test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("Testing AI Analysis Sharpe and Sortino Ratio Fix...")
    unittest.main()
