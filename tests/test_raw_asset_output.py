#!/usr/bin/env python3
"""
Test raw asset output functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok

def test_raw_asset_output():
    """Test raw asset output without emojis and formatting"""
    print("Testing raw asset output...")
    
    symbols = ['VOO.US', 'AAPL.US', 'SBER.MOEX']
    
    for symbol in symbols:
        print(f"\n{'='*50}")
        print(f"Testing symbol: {symbol}")
        print(f"{'='*50}")
        
        try:
            # Test raw asset output
            asset = ok.Asset(symbol)
            raw_output = f"{asset}"
            
            print("Raw asset output:")
            print(raw_output)
            
            # Check that output doesn't contain emojis
            emojis = ['📊', '🏛️', '🌍', '💰', '📈', '🔹', '💵', '📉']
            has_emojis = any(emoji in raw_output for emoji in emojis)
            
            if has_emojis:
                print("❌ Output contains emojis!")
            else:
                print("✅ Output is clean (no emojis)")
            
            # Check that output contains expected fields
            expected_fields = ['symbol', 'name', 'country', 'exchange', 'currency', 'type']
            has_fields = all(field in raw_output.lower() for field in expected_fields)
            
            if has_fields:
                print("✅ Output contains expected fields")
            else:
                print("❌ Missing expected fields")
                
        except Exception as e:
            print(f"❌ Error testing {symbol}: {e}")
            continue

if __name__ == "__main__":
    test_raw_asset_output()
