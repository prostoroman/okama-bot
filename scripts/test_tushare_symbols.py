#!/usr/bin/env python3
"""
Test script to debug Tushare symbol issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tushare_service import TushareService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_symbol_info():
    """Test symbol information retrieval"""
    print("=== Testing Symbol Information ===")
    
    try:
        tushare_service = TushareService()
        
        # Test different symbols
        test_symbols = [
            "000001.SH",  # Shanghai Composite Index
            "600000.SH",  # Pudong Development Bank
            "000001.SZ",  # Ping An Bank (Shenzhen)
            "000002.SZ",  # China Vanke
            "600036.SH",  # China Merchants Bank
        ]
        
        for symbol in test_symbols:
            print(f"\nTesting symbol: {symbol}")
            info = tushare_service.get_symbol_info(symbol)
            
            if "error" in info:
                print(f"  ❌ Error: {info['error']}")
            else:
                print(f"  ✅ Name: {info.get('name', 'N/A')}")
                print(f"  ✅ Exchange: {info.get('exchange', 'N/A')}")
                print(f"  ✅ Industry: {info.get('industry', 'N/A')}")
                print(f"  ✅ List Date: {info.get('list_date', 'N/A')}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_daily_data():
    """Test daily data retrieval"""
    print("\n=== Testing Daily Data Retrieval ===")
    
    try:
        tushare_service = TushareService()
        
        # Test different symbols
        test_symbols = [
            "000001.SH",  # Shanghai Composite Index
            "600000.SH",  # Pudong Development Bank
            "000001.SZ",  # Ping An Bank (Shenzhen)
        ]
        
        for symbol in test_symbols:
            print(f"\nTesting daily data for: {symbol}")
            
            daily_data = tushare_service.get_daily_data(symbol)
            print(f"  Data shape: {daily_data.shape}")
            print(f"  Data empty: {daily_data.empty}")
            
            if not daily_data.empty:
                print(f"  Columns: {list(daily_data.columns)}")
                print(f"  Date range: {daily_data['trade_date'].min()} to {daily_data['trade_date'].max()}")
                print(f"  Sample data:")
                print(daily_data.head(3))
            else:
                print("  ❌ No data returned")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_symbol_mapping():
    """Test symbol mapping and validation"""
    print("\n=== Testing Symbol Mapping ===")
    
    try:
        tushare_service = TushareService()
        
        test_symbols = [
            "000001.SH",
            "600000.SH", 
            "000001.SZ",
            "000002.SZ",
            "600036.SH",
            "AAPL",  # Not a Tushare symbol
        ]
        
        for symbol in test_symbols:
            is_tushare = tushare_service.is_tushare_symbol(symbol)
            exchange = tushare_service.get_exchange_from_symbol(symbol)
            
            print(f"Symbol: {symbol}")
            print(f"  Is Tushare symbol: {is_tushare}")
            print(f"  Exchange: {exchange}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Tushare Symbol and Data Test")
    print("=" * 50)
    
    test_symbol_mapping()
    test_symbol_info()
    test_daily_data()
    
    print("\nTest completed!")
