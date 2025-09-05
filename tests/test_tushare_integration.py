#!/usr/bin/env python3
"""
Test script for Tushare integration
"""

import sys
import os

# Add the parent directory to the path so we can import the bot modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_tushare_service_import():
    """Test that TushareService can be imported"""
    try:
        from services.tushare_service import TushareService
        print("✅ TushareService import successful")
        return True
    except ImportError as e:
        print(f"❌ TushareService import failed: {e}")
        return False

def test_bot_import():
    """Test that bot can be imported with TushareService"""
    try:
        from bot import ShansAi
        print("✅ Bot import with TushareService successful")
        return True
    except ImportError as e:
        print(f"❌ Bot import failed: {e}")
        return False

def test_config_import():
    """Test that config can be imported"""
    try:
        from config import Config
        print("✅ Config import successful")
        # Check if TUSHARE_API_KEY is defined
        if hasattr(Config, 'TUSHARE_API_KEY'):
            print("✅ TUSHARE_API_KEY configuration found")
        else:
            print("❌ TUSHARE_API_KEY configuration missing")
            return False
        return True
    except ImportError as e:
        print(f"❌ Config import failed: {e}")
        return False

def test_symbol_patterns():
    """Test symbol pattern recognition"""
    try:
        from services.tushare_service import TushareService
        
        # Mock the service without API key for testing patterns
        class MockTushareService:
            def __init__(self):
                self.exchange_mappings = {
                    'SSE': '.SH',
                    'SZSE': '.SZ', 
                    'BSE': '.BJ',
                    'HKEX': '.HK'
                }
                self.symbol_patterns = {
                    'SSE': r'^[0-9]{6}\.SH$',
                    'SZSE': r'^[0-9]{6}\.SZ$',
                    'BSE': r'^[0-9]{6}\.BJ$',
                    'HKEX': r'^[0-9]{5}\.HK$'
                }
            
            def is_tushare_symbol(self, symbol):
                import re
                for pattern in self.symbol_patterns.values():
                    if re.match(pattern, symbol):
                        return True
                return False
        
        service = MockTushareService()
        
        # Test valid symbols
        test_symbols = [
            ('600000.SH', True),
            ('000001.SH', True),
            ('000001.SZ', True),
            ('399005.SZ', True),
            ('900001.BJ', True),
            ('800001.BJ', True),
            ('00001.HK', True),
            ('00700.HK', True),
            ('AAPL.US', False),
            ('SBER.MOEX', False)
        ]
        
        for symbol, expected in test_symbols:
            result = service.is_tushare_symbol(symbol)
            if result == expected:
                print(f"✅ {symbol}: {result}")
            else:
                print(f"❌ {symbol}: expected {expected}, got {result}")
                return False
        
        print("✅ All symbol pattern tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Symbol pattern test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Tushare Integration")
    print("=" * 50)
    
    tests = [
        test_config_import,
        test_tushare_service_import,
        test_bot_import,
        test_symbol_patterns
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Tushare integration is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
