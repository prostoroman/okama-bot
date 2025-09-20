#!/usr/bin/env python3
"""
Test script to verify Chinese symbol support fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tushare_service import TushareService
from bot import ShansAi

def test_tushare_symbol_recognition():
    """Test that TushareService correctly recognizes Chinese symbols"""
    print("Testing TushareService symbol recognition...")
    
    # Initialize TushareService
    tushare_service = TushareService()
    
    # Test cases for different symbol formats
    test_cases = [
        # Original format (should still work)
        ('600000.SH', True, 'SSE'),
        ('000001.SZ', True, 'SZSE'),
        ('900001.BJ', True, 'BSE'),
        ('00001.HK', True, 'HKEX'),
        
        # New format (should now work)
        ('600000.SSE', True, 'SSE'),
        ('002594.SZSE', True, 'SZSE'),
        ('900001.BSE', True, 'BSE'),
        ('00001.HKEX', True, 'HKEX'),
        
        # Invalid formats (should not work)
        ('600000.US', False, None),
        ('AAPL.US', False, None),
        ('SBER.MOEX', False, None),
    ]
    
    print("\nTesting symbol recognition:")
    for symbol, expected_result, expected_exchange in test_cases:
        is_tushare = tushare_service.is_tushare_symbol(symbol)
        exchange = tushare_service.get_exchange_from_symbol(symbol)
        
        status = "✅ PASS" if is_tushare == expected_result else "❌ FAIL"
        print(f"{status} {symbol}: is_tushare={is_tushare} (expected {expected_result}), exchange={exchange} (expected {expected_exchange})")
        
        if is_tushare != expected_result:
            print(f"   ERROR: Expected {expected_result}, got {is_tushare}")
        if expected_exchange and exchange != expected_exchange:
            print(f"   ERROR: Expected exchange {expected_exchange}, got {exchange}")

def test_bot_data_source_determination():
    """Test that bot correctly determines data source for Chinese symbols"""
    print("\nTesting bot data source determination...")
    
    # Initialize bot
    bot = ShansAi()
    
    # Test cases
    test_cases = [
        # Chinese symbols (should use tushare)
        ('600000.SH', 'tushare'),
        ('000001.SZ', 'tushare'),
        ('002594.SZSE', 'tushare'),
        ('600000.SSE', 'tushare'),
        ('00001.HK', 'tushare'),
        ('00001.HKEX', 'tushare'),
        
        # Non-Chinese symbols (should use okama)
        ('AAPL.US', 'okama'),
        ('SBER.MOEX', 'okama'),
        ('VOD.LSE', 'okama'),
    ]
    
    print("\nTesting data source determination:")
    for symbol, expected_source in test_cases:
        try:
            source = bot.determine_data_source(symbol)
            status = "✅ PASS" if source == expected_source else "❌ FAIL"
            print(f"{status} {symbol}: {source} (expected {expected_source})")
        except Exception as e:
            print(f"❌ ERROR {symbol}: {e}")

def test_allowed_exchanges():
    """Test that Chinese exchanges are in allowed exchanges list"""
    print("\nTesting allowed exchanges...")
    
    # Initialize bot
    bot = ShansAi()
    
    # Get the allowed exchanges from the bot
    # We need to access the private method, so we'll test it indirectly
    test_symbol = "002594.SZSE"
    
    try:
        # This should not raise an exception about SZSE not being in allowed exchanges
        source = bot.determine_data_source(test_symbol)
        print(f"✅ PASS: {test_symbol} correctly determined as {source}")
    except Exception as e:
        if "not in allowed assets namespaces" in str(e):
            print(f"❌ FAIL: {test_symbol} still not recognized: {e}")
        else:
            print(f"❌ ERROR: Unexpected error for {test_symbol}: {e}")

if __name__ == "__main__":
    print("🧪 Testing Chinese Symbol Support Fixes")
    print("=" * 50)
    
    try:
        test_tushare_symbol_recognition()
        test_bot_data_source_determination()
        test_allowed_exchanges()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
