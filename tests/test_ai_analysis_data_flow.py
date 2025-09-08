#!/usr/bin/env python3
"""
Test for AI analysis data flow - checking if data reaches AI services correctly
"""

import unittest
import asyncio
import sys
import os

# Add the parent directory to the path to import bot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
import okama as ok

class TestAIAnalysisDataFlow(unittest.TestCase):
    """Test cases for AI analysis data flow"""
    
    def setUp(self):
        """Set up test environment"""
        self.bot = ShansAi()
        
    def test_gemini_data_description_content(self):
        """Test that Gemini receives correct data with Sharpe and Sortino ratios"""
        print(f"\n=== Testing Gemini Data Description Content ===")
        
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
        
        # Prepare data
        try:
            data_info = asyncio.run(self.bot._prepare_data_for_analysis(
                symbols=symbols,
                currency=currency,
                expanded_symbols=expanded_symbols,
                portfolio_contexts=[],
                user_id=12345
            ))
            
            # Test Gemini service data description
            if hasattr(self.bot, 'gemini_service') and self.bot.gemini_service:
                print(f"\n🤖 Testing Gemini Data Description:")
                try:
                    data_description = self.bot.gemini_service._prepare_data_description(data_info)
                    print(f"  - Description length: {len(data_description)}")
                    
                    # Print the actual description to see what's being sent
                    print(f"\n📄 Gemini Data Description:")
                    print("=" * 80)
                    print(data_description)
                    print("=" * 80)
                    
                    # Check specific content
                    checks = [
                        ('Анализируемые активы', 'Asset names'),
                        ('Apple Inc', 'Apple name'),
                        ('SPDR S&P 500 ETF Trust', 'SPY name'),
                        ('Коэффициент Шарпа', 'Sharpe ratio'),
                        ('Коэффициент Сортино', 'Sortino ratio'),
                        ('0.05', 'Sharpe value'),
                        ('0.44', 'Sharpe value'),
                        ('0.07', 'Sortino value'),
                        ('0.61', 'Sortino value')
                    ]
                    
                    for check_text, check_name in checks:
                        if check_text in data_description:
                            print(f"  ✅ {check_name}: Found '{check_text}'")
                        else:
                            print(f"  ❌ {check_name}: Missing '{check_text}'")
                    
                except Exception as e:
                    print(f"  ❌ Error preparing Gemini description: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"❌ Gemini service not available")
            
        except Exception as e:
            print(f"❌ Error in test: {e}")
            import traceback
            traceback.print_exc()

    def test_yandexgpt_data_description_content(self):
        """Test that YandexGPT receives correct data with Sharpe and Sortino ratios"""
        print(f"\n=== Testing YandexGPT Data Description Content ===")
        
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
        
        # Prepare data
        try:
            data_info = asyncio.run(self.bot._prepare_data_for_analysis(
                symbols=symbols,
                currency=currency,
                expanded_symbols=expanded_symbols,
                portfolio_contexts=[],
                user_id=12345
            ))
            
            # Test YandexGPT service data description
            if hasattr(self.bot, 'yandexgpt_service') and self.bot.yandexgpt_service:
                print(f"\n🤖 Testing YandexGPT Data Description:")
                try:
                    data_description = self.bot.yandexgpt_service._prepare_data_description(data_info)
                    print(f"  - Description length: {len(data_description)}")
                    
                    # Print the actual description to see what's being sent
                    print(f"\n📄 YandexGPT Data Description:")
                    print("=" * 80)
                    print(data_description)
                    print("=" * 80)
                    
                    # Check specific content
                    checks = [
                        ('Анализируемые активы', 'Asset names'),
                        ('Apple Inc', 'Apple name'),
                        ('SPDR S&P 500 ETF Trust', 'SPY name'),
                        ('Коэффициент Шарпа', 'Sharpe ratio'),
                        ('Коэффициент Сортино', 'Sortino ratio'),
                        ('0.05', 'Sharpe value'),
                        ('0.44', 'Sharpe value'),
                        ('0.07', 'Sortino value'),
                        ('0.61', 'Sortino value')
                    ]
                    
                    for check_text, check_name in checks:
                        if check_text in data_description:
                            print(f"  ✅ {check_name}: Found '{check_text}'")
                        else:
                            print(f"  ❌ {check_name}: Missing '{check_text}'")
                    
                except Exception as e:
                    print(f"  ❌ Error preparing YandexGPT description: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"❌ YandexGPT service not available")
            
        except Exception as e:
            print(f"❌ Error in test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("Testing AI Analysis Data Flow...")
    unittest.main()
