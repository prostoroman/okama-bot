#!/usr/bin/env python3
"""
Test for actual AI response to understand what data is being passed incorrectly
"""

import unittest
import asyncio
import sys
import os

# Add the parent directory to the path to import bot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
import okama as ok

class TestAIActualResponse(unittest.TestCase):
    """Test cases for actual AI response analysis"""
    
    def setUp(self):
        """Set up test environment"""
        self.bot = ShansAi()
        
    def test_gemini_actual_analysis(self):
        """Test actual Gemini analysis response"""
        print(f"\n=== Testing Actual Gemini Analysis Response ===")
        
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
            
            print(f"\n📊 Prepared Data Info:")
            print(f"  - Symbols: {data_info.get('symbols', [])}")
            print(f"  - Currency: {data_info.get('currency', 'N/A')}")
            print(f"  - Asset names: {data_info.get('asset_names', {})}")
            print(f"  - Performance keys: {list(data_info.get('performance', {}).keys())}")
            
            # Check performance metrics for each symbol
            for symbol in symbols:
                if symbol in data_info.get('performance', {}):
                    metrics = data_info['performance'][symbol]
                    print(f"\n📈 {symbol} Performance Metrics:")
                    for key, value in metrics.items():
                        if key != '_returns':  # Skip internal returns data
                            print(f"  - {key}: {value}")
            
            # Test actual Gemini analysis
            if hasattr(self.bot, 'gemini_service') and self.bot.gemini_service:
                print(f"\n🤖 Testing Actual Gemini Analysis:")
                try:
                    # Call the actual analyze_data method
                    analysis_result = self.bot.gemini_service.analyze_data(data_info)
                    
                    if analysis_result:
                        print(f"  - Success: {analysis_result.get('success', False)}")
                        print(f"  - Analysis length: {len(analysis_result.get('analysis', ''))}")
                        
                        if analysis_result.get('success') and analysis_result.get('analysis'):
                            analysis_text = analysis_result['analysis']
                            print(f"\n📄 Actual Gemini Analysis Response:")
                            print("=" * 80)
                            print(analysis_text)
                            print("=" * 80)
                            
                            # Check if the analysis mentions the correct data
                            checks = [
                                ('Apple', 'Apple mention'),
                                ('AAPL', 'AAPL symbol'),
                                ('SPY', 'SPY symbol'),
                                ('SPDR', 'SPDR mention'),
                                ('0.05', 'Sharpe ratio AAPL'),
                                ('0.44', 'Sharpe ratio SPY'),
                                ('0.07', 'Sortino ratio AAPL'),
                                ('0.61', 'Sortino ratio SPY'),
                                ('4.44%', 'Annual return AAPL'),
                                ('8.56%', 'Annual return SPY')
                            ]
                            
                            print(f"\n🔍 Analysis Content Check:")
                            for check_text, check_name in checks:
                                if check_text in analysis_text:
                                    print(f"  ✅ {check_name}: Found '{check_text}'")
                                else:
                                    print(f"  ❌ {check_name}: Missing '{check_text}'")
                        else:
                            print(f"  ❌ Analysis failed or empty")
                            if 'error' in analysis_result:
                                print(f"  - Error: {analysis_result['error']}")
                    else:
                        print(f"  ❌ No analysis result")
                        
                except Exception as e:
                    print(f"  ❌ Error in Gemini analysis: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"❌ Gemini service not available")
            
        except Exception as e:
            print(f"❌ Error in test: {e}")
            import traceback
            traceback.print_exc()

    def test_yandexgpt_actual_analysis(self):
        """Test actual YandexGPT analysis response"""
        print(f"\n=== Testing Actual YandexGPT Analysis Response ===")
        
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
            
            # Test actual YandexGPT analysis
            if hasattr(self.bot, 'yandexgpt_service') and self.bot.yandexgpt_service:
                print(f"\n🤖 Testing Actual YandexGPT Analysis:")
                try:
                    # Call the actual analyze_data method
                    analysis_result = self.bot.yandexgpt_service.analyze_data(data_info)
                    
                    if analysis_result:
                        print(f"  - Success: {analysis_result.get('success', False)}")
                        print(f"  - Analysis length: {len(analysis_result.get('analysis', ''))}")
                        
                        if analysis_result.get('success') and analysis_result.get('analysis'):
                            analysis_text = analysis_result['analysis']
                            print(f"\n📄 Actual YandexGPT Analysis Response:")
                            print("=" * 80)
                            print(analysis_text)
                            print("=" * 80)
                            
                            # Check if the analysis mentions the correct data
                            checks = [
                                ('Apple', 'Apple mention'),
                                ('AAPL', 'AAPL symbol'),
                                ('SPY', 'SPY symbol'),
                                ('SPDR', 'SPDR mention'),
                                ('0.05', 'Sharpe ratio AAPL'),
                                ('0.44', 'Sharpe ratio SPY'),
                                ('0.07', 'Sortino ratio AAPL'),
                                ('0.61', 'Sortino ratio SPY'),
                                ('4.44%', 'Annual return AAPL'),
                                ('8.56%', 'Annual return SPY')
                            ]
                            
                            print(f"\n🔍 Analysis Content Check:")
                            for check_text, check_name in checks:
                                if check_text in analysis_text:
                                    print(f"  ✅ {check_name}: Found '{check_text}'")
                                else:
                                    print(f"  ❌ {check_name}: Missing '{check_text}'")
                        else:
                            print(f"  ❌ Analysis failed or empty")
                            if 'error' in analysis_result:
                                print(f"  - Error: {analysis_result['error']}")
                    else:
                        print(f"  ❌ No analysis result")
                        
                except Exception as e:
                    print(f"  ❌ Error in YandexGPT analysis: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"❌ YandexGPT service not available")
            
        except Exception as e:
            print(f"❌ Error in test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("Testing Actual AI Response...")
    unittest.main()
