#!/usr/bin/env python3
"""
Test script for Chinese symbols fix
Tests that Hong Kong symbols (00001.HK, 00005.HK) can now be compared successfully
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tushare_service import TushareService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_hong_kong_monthly_data():
    """Test that Hong Kong symbols can retrieve monthly data"""
    
    print("🔍 Testing Hong Kong Monthly Data Fix")
    print("=" * 50)
    
    # Test symbols that were failing
    test_symbols = ['00001.HK', '00005.HK']
    
    try:
        # Initialize Tushare service
        tushare_service = TushareService()
        
        for symbol in test_symbols:
            print(f"\n🔍 Testing symbol: {symbol}")
            print("-" * 30)
            
            # Test monthly data retrieval with a reasonable date range
            monthly_data = tushare_service.get_monthly_data(symbol, start_date='20200101', end_date='20241231')
            
            if not monthly_data.empty:
                print(f"✅ Monthly data retrieved: {len(monthly_data)} records")
                print(f"   Date range: {monthly_data['trade_date'].min()} to {monthly_data['trade_date'].max()}")
                
                # Verify data structure
                required_columns = ['trade_date', 'ts_code', 'close']
                missing_columns = [col for col in required_columns if col not in monthly_data.columns]
                
                if not missing_columns:
                    print("✅ Required columns present")
                else:
                    print(f"❌ Missing columns: {missing_columns}")
                    
            else:
                print("❌ No monthly data retrieved")
                return False
        
        print("\n✅ All Hong Kong symbols can retrieve monthly data successfully")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_symbol_recognition():
    """Test that Hong Kong symbols are properly recognized"""
    
    print("\n🔍 Testing Symbol Recognition")
    print("=" * 50)
    
    test_symbols = ['00001.HK', '00005.HK']
    
    try:
        tushare_service = TushareService()
        
        for symbol in test_symbols:
            print(f"\n🔍 Testing symbol: {symbol}")
            print("-" * 30)
            
            # Test symbol recognition
            is_chinese = tushare_service.is_tushare_symbol(symbol)
            exchange = tushare_service.get_exchange_from_symbol(symbol)
            
            print(f"✅ Is Chinese symbol: {is_chinese}")
            print(f"✅ Exchange: {exchange}")
            
            if not is_chinese or exchange != 'HKEX':
                print(f"❌ Symbol recognition failed for {symbol}")
                return False
        
        print("\n✅ All Hong Kong symbols are properly recognized")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Chinese Symbols Fix Test")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_symbol_recognition()
    test2_passed = test_hong_kong_monthly_data()
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Chinese symbols fix is working correctly.")
        exit(0)
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        exit(1)
