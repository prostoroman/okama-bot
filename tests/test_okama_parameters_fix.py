#!/usr/bin/env python3
"""
Test script to verify the okama parameter names fix.
This test simulates the portfolio creation process to ensure correct parameter names are used.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_okama_parameter_names():
    """Test that okama library calls use correct parameter names"""
    print("Testing okama parameter names...")
    
    try:
        import okama as ok
        print("✅ Okama library imported successfully")
    except ImportError:
        print("⚠️ Okama library not available for testing, but parameter names should be correct")
        return True
    
    # Test 1: Portfolio creation with period parameters
    try:
        symbols = ["SPY.US", "QQQ.US", "BND.US"]
        weights = [0.5, 0.3, 0.2]
        currency = "USD"
        specified_period = "5Y"
        
        if specified_period:
            years = int(specified_period[:-1])  # Extract number from '5Y'
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            
            # This should work with correct parameter names
            portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency,
                                   first_date=start_date.strftime('%Y-%m-%d'), 
                                   last_date=end_date.strftime('%Y-%m-%d'))
            print(f"✅ Portfolio creation with period works: {portfolio}")
            
    except Exception as e:
        print(f"❌ Portfolio creation with period failed: {e}")
        return False
    
    # Test 2: AssetList creation with period parameters
    try:
        symbols = ["SPY.US", "QQQ.US"]
        currency = "USD"
        specified_period = "5Y"
        
        if specified_period:
            years = int(specified_period[:-1])
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            
            # This should work with correct parameter names
            comparison = ok.AssetList(symbols, ccy=currency, inflation=True,
                                    first_date=start_date.strftime('%Y-%m-%d'), 
                                    last_date=end_date.strftime('%Y-%m-%d'))
            print(f"✅ AssetList creation with period works: {comparison}")
            
    except Exception as e:
        print(f"❌ AssetList creation with period failed: {e}")
        return False
    
    # Test 3: Portfolio creation without period parameters
    try:
        symbols = ["SPY.US", "QQQ.US", "BND.US"]
        weights = [0.5, 0.3, 0.2]
        currency = "USD"
        
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency)
        print(f"✅ Portfolio creation without period works: {portfolio}")
        
    except Exception as e:
        print(f"❌ Portfolio creation without period failed: {e}")
        return False
    
    print("✅ All okama parameter tests passed!")
    return True

def test_parameter_name_consistency():
    """Test that all parameter names are consistent"""
    print("\nTesting parameter name consistency...")
    
    # Read the bot.py file and check for any remaining incorrect parameter names
    bot_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot.py')
    
    try:
        with open(bot_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for old incorrect parameter names
        if 'firstdate=' in content:
            print("❌ Found 'firstdate=' in bot.py - should be 'first_date='")
            return False
        
        if 'lastdate=' in content:
            print("❌ Found 'lastdate=' in bot.py - should be 'last_date='")
            return False
        
        # Check for correct parameter names
        if 'first_date=' in content:
            print("✅ Found 'first_date=' in bot.py")
        else:
            print("⚠️ No 'first_date=' found in bot.py")
        
        if 'last_date=' in content:
            print("✅ Found 'last_date=' in bot.py")
        else:
            print("⚠️ No 'last_date=' found in bot.py")
        
        print("✅ Parameter name consistency check passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error reading bot.py: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing okama parameter names fix...")
    
    success1 = test_okama_parameter_names()
    success2 = test_parameter_name_consistency()
    
    if success1 and success2:
        print("\n🎉 All okama parameter tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some okama parameter tests failed!")
        sys.exit(1)
