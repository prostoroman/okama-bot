#!/usr/bin/env python3
"""
Test for AI data validation - check what data is actually being sent to AI services
"""

import unittest
import asyncio
import sys
import os

# Add the parent directory to the path to import bot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
import okama as ok

class TestAIDataValidation(unittest.TestCase):
    """Test cases for AI data validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.bot = ShansAi()
        
    def test_data_preparation_validation(self):
        """Test that data preparation creates correct structure for AI"""
        print(f"\n=== Testing Data Preparation Validation ===")
        
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
            
            print(f"\n📊 Data Structure Validation:")
            
            # Check required fields
            required_fields = ['symbols', 'currency', 'performance', 'asset_names']
            for field in required_fields:
                if field in data_info:
                    print(f"  ✅ {field}: Present")
                    if field == 'performance':
                        print(f"    - Keys: {list(data_info[field].keys())}")
                    elif field == 'asset_names':
                        print(f"    - Values: {data_info[field]}")
                else:
                    print(f"  ❌ {field}: Missing")
            
            # Validate performance data structure
            print(f"\n📈 Performance Data Validation:")
            for symbol in symbols:
                if symbol in data_info.get('performance', {}):
                    metrics = data_info['performance'][symbol]
                    required_metrics = ['total_return', 'annual_return', 'volatility', 'sharpe_ratio', 'sortino_ratio', 'max_drawdown']
                    
                    print(f"  {symbol}:")
                    for metric in required_metrics:
                        if metric in metrics:
                            value = metrics[metric]
                            if value is not None and value != 0:
                                print(f"    ✅ {metric}: {value}")
                            else:
                                print(f"    ❌ {metric}: {value} (empty/zero)")
                        else:
                            print(f"    ❌ {metric}: Missing")
                else:
                    print(f"  ❌ {symbol}: No performance data")
            
            # Test data description preparation
            print(f"\n🤖 Data Description Validation:")
            
            # Test Gemini data description
            if hasattr(self.bot, 'gemini_service') and self.bot.gemini_service:
                try:
                    data_description = self.bot.gemini_service._prepare_data_description(data_info)
                    print(f"  Gemini description length: {len(data_description)}")
                    
                    # Check for key data in description
                    key_checks = [
                        ('Apple Inc', 'Apple name'),
                        ('SPDR S&P 500 ETF Trust', 'SPY name'),
                        ('Коэффициент Шарпа: 0.05', 'AAPL Sharpe'),
                        ('Коэффициент Шарпа: 0.44', 'SPY Sharpe'),
                        ('Коэффициент Сортино: 0.07', 'AAPL Sortino'),
                        ('Коэффициент Сортино: 0.61', 'SPY Sortino'),
                        ('Годовая доходность: 4.44%', 'AAPL annual return'),
                        ('Годовая доходность: 8.56%', 'SPY annual return')
                    ]
                    
                    for check_text, check_name in key_checks:
                        if check_text in data_description:
                            print(f"    ✅ {check_name}: Found")
                        else:
                            print(f"    ❌ {check_name}: Missing")
                            
                except Exception as e:
                    print(f"    ❌ Gemini description error: {e}")
            
            # Test YandexGPT data description
            if hasattr(self.bot, 'yandexgpt_service') and self.bot.yandexgpt_service:
                try:
                    data_description = self.bot.yandexgpt_service._prepare_data_description(data_info)
                    print(f"  YandexGPT description length: {len(data_description)}")
                    
                    # Check for key data in description
                    key_checks = [
                        ('Apple Inc', 'Apple name'),
                        ('SPDR S&P 500 ETF Trust', 'SPY name'),
                        ('Коэффициент Шарпа: 0.05', 'AAPL Sharpe'),
                        ('Коэффициент Шарпа: 0.44', 'SPY Sharpe'),
                        ('Коэффициент Сортино: 0.07', 'AAPL Sortino'),
                        ('Коэффициент Сортино: 0.61', 'SPY Sortino'),
                        ('Годовая доходность: 4.44%', 'AAPL annual return'),
                        ('Годовая доходность: 8.56%', 'SPY annual return')
                    ]
                    
                    for check_text, check_name in key_checks:
                        if check_text in data_description:
                            print(f"    ✅ {check_name}: Found")
                        else:
                            print(f"    ❌ {check_name}: Missing")
                            
                except Exception as e:
                    print(f"    ❌ YandexGPT description error: {e}")
            
            print(f"\n✅ Data Preparation Validation Completed")
            
        except Exception as e:
            print(f"❌ Error in test: {e}")
            import traceback
            traceback.print_exc()

    def test_api_configuration(self):
        """Test API configuration for AI services"""
        print(f"\n=== Testing API Configuration ===")
        
        # Check Gemini service
        if hasattr(self.bot, 'gemini_service') and self.bot.gemini_service:
            print(f"🤖 Gemini Service:")
            print(f"  - Available: {self.bot.gemini_service.is_available()}")
            status = self.bot.gemini_service.get_service_status()
            print(f"  - Status: {status}")
        else:
            print(f"❌ Gemini service not initialized")
        
        # Check YandexGPT service
        if hasattr(self.bot, 'yandexgpt_service') and self.bot.yandexgpt_service:
            print(f"🤖 YandexGPT Service:")
            print(f"  - API Key: {'Yes' if self.bot.yandexgpt_service.api_key else 'No'}")
            print(f"  - Folder ID: {'Yes' if self.bot.yandexgpt_service.folder_id else 'No'}")
        else:
            print(f"❌ YandexGPT service not initialized")

if __name__ == '__main__':
    print("Testing AI Data Validation...")
    unittest.main()
